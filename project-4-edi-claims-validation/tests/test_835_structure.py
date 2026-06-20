"""Structural tests for the X12 835 remittance advice file."""

from decimal import Decimal

import pytest


class TestRemittance835Structure:

    def test_isa_header_present(self, parsed_835):
        assert parsed_835['envelope']['isa'] is not None

    def test_payer_and_payee_present(self, parsed_835):
        assert parsed_835['payer'] is not None
        assert parsed_835['payee'] is not None

    def test_claim_payment_count_matches_837_claim_count(self, parsed_835, claims_by_id):
        assert len(parsed_835['claim_payments']) == len(claims_by_id)

    def test_total_payment_matches_claim_sum(self, parsed_835):
        claim_sum = sum(cp['paid_amount'] for cp in parsed_835['claim_payments'])
        assert abs(parsed_835['total_payment'] - claim_sum) <= Decimal('0.01')

    def test_paid_amount_non_negative(self, parsed_835):
        assert all(cp['paid_amount'] >= 0 for cp in parsed_835['claim_payments'])

    @pytest.mark.parametrize('status_code', ['1', '4'])
    def test_status_codes_are_valid(self, parsed_835, status_code):
        seen = {cp['status_code'] for cp in parsed_835['claim_payments']}
        assert seen <= {'1', '4'}

    def test_denied_claims_have_zero_payment(self, parsed_835):
        denied = [cp for cp in parsed_835['claim_payments'] if cp['status_code'] == '4']
        assert len(denied) >= 1
        assert all(cp['paid_amount'] == 0 for cp in denied)

    def test_service_line_paid_le_charge(self, parsed_835):
        for cp in parsed_835['claim_payments']:
            for sp in cp['service_payments']:
                assert sp['paid'] <= sp['charge']

    def test_adjustment_reason_codes_are_known(self, parsed_835):
        known = {('CO', '45'), ('CO', '50'), ('PR', '1')}
        for cp in parsed_835['claim_payments']:
            for sp in cp['service_payments']:
                for adj in sp['adjustments']:
                    assert (adj['group_code'], adj['reason_code']) in known

    def test_patient_responsibility_non_negative(self, parsed_835):
        assert all(cp['patient_responsibility'] >= 0 for cp in parsed_835['claim_payments'])
