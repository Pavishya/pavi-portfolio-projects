"""837 (claim submission) <-> 835 (remittance) reconciliation tests."""

import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import (  # noqa: E402
    reconcile_claims_to_remittance,
    check_remittance_charge_matches_claim,
)


class TestClaimsToRemittanceReconciliation:

    def test_every_claim_has_matching_remittance(self, parsed_837, remittances_by_claim_id):
        for claim in parsed_837['claims']:
            assert claim['claim_id'] in remittances_by_claim_id

    def test_no_orphaned_remittance_lines(self, parsed_837, parsed_835):
        result = reconcile_claims_to_remittance(parsed_837['claims'], parsed_835['claim_payments'])
        assert result['unmatched_remittances'] == []

    def test_no_orphaned_claims_in_reconciliation(self, parsed_837, parsed_835):
        result = reconcile_claims_to_remittance(parsed_837['claims'], parsed_835['claim_payments'])
        assert result['unmatched_claims'] == []

    def test_matched_claim_count_equals_837_claim_count(self, parsed_837, parsed_835):
        result = reconcile_claims_to_remittance(parsed_837['claims'], parsed_835['claim_payments'])
        assert result['matched_count'] == len(parsed_837['claims'])

    @pytest.mark.parametrize('claim_index', range(18))
    def test_charge_amount_matches_between_837_and_835(self, parsed_837, remittances_by_claim_id, claim_index):
        if claim_index >= len(parsed_837['claims']):
            pytest.skip('fewer claims generated than parametrize range')
        claim = parsed_837['claims'][claim_index]
        remittance = remittances_by_claim_id[claim['claim_id']]
        assert check_remittance_charge_matches_claim(claim, remittance)

    def test_remittance_claim_ids_reference_real_claims(self, parsed_837, parsed_835):
        claim_ids = {c['claim_id'] for c in parsed_837['claims']}
        for remittance in parsed_835['claim_payments']:
            assert remittance['claim_id'] in claim_ids

    def test_reconciliation_summary_structure(self, parsed_837, parsed_835):
        result = reconcile_claims_to_remittance(parsed_837['claims'], parsed_835['claim_payments'])
        assert set(result.keys()) == {'unmatched_claims', 'unmatched_remittances', 'matched_count'}

    def test_total_charges_reconcile_across_files(self, parsed_837, parsed_835):
        total_837 = sum(c['total_charge'] for c in parsed_837['claims'])
        total_835 = sum(cp['charge_amount'] for cp in parsed_835['claim_payments'])
        assert abs(total_837 - total_835) <= Decimal('0.01')
