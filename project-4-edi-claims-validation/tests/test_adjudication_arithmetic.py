"""835 adjudication arithmetic: paid + adjustments must reconcile to charge."""

import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import (  # noqa: E402
    check_paid_plus_adjustment_equals_charge,
    check_patient_responsibility_matches_pr_adjustments,
    check_total_payment_matches_claim_sum,
)


class TestAdjudicationArithmetic:

    @pytest.mark.parametrize('claim_index', range(18))
    def test_paid_plus_adjustment_equals_charge(self, parsed_835, claim_index):
        claim_payments = parsed_835['claim_payments']
        if claim_index >= len(claim_payments):
            pytest.skip('fewer claim payments generated than parametrize range')
        assert check_paid_plus_adjustment_equals_charge(claim_payments[claim_index])

    @pytest.mark.parametrize('claim_index', range(18))
    def test_patient_responsibility_matches_pr_adjustments(self, parsed_835, claim_index):
        claim_payments = parsed_835['claim_payments']
        if claim_index >= len(claim_payments):
            pytest.skip('fewer claim payments generated than parametrize range')
        assert check_patient_responsibility_matches_pr_adjustments(claim_payments[claim_index])

    def test_service_line_paid_amounts_sum_to_claim_paid(self, parsed_835):
        for cp in parsed_835['claim_payments']:
            line_sum = sum(sp['paid'] for sp in cp['service_payments'])
            assert abs(line_sum - cp['paid_amount']) <= Decimal('0.01')

    def test_contractual_adjustment_non_negative(self, parsed_835):
        for cp in parsed_835['claim_payments']:
            for sp in cp['service_payments']:
                for adj in sp['adjustments']:
                    if adj['group_code'] == 'CO':
                        assert adj['amount'] >= 0

    def test_adjustment_rate_within_expected_band(self, parsed_835):
        for cp in parsed_835['claim_payments']:
            if cp['status_code'] == '4':
                continue  # denied claims are 100% written off, not a contractual rate
            co_total = sum(
                adj['amount']
                for sp in cp['service_payments']
                for adj in sp['adjustments']
                if adj['group_code'] == 'CO'
            )
            rate = co_total / cp['charge_amount']
            assert Decimal('0.05') <= rate <= Decimal('0.30')

    def test_no_negative_payments(self, parsed_835):
        for cp in parsed_835['claim_payments']:
            assert cp['paid_amount'] >= 0
            for sp in cp['service_payments']:
                assert sp['paid'] >= 0

    def test_total_payment_arithmetic_consistent(self, parsed_835):
        assert check_total_payment_matches_claim_sum(parsed_835)
