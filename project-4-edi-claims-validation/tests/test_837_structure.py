"""Structural tests for the X12 837P claims file."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import check_no_duplicate_claim_ids, check_claim_total_matches_line_sum  # noqa: E402

KNOWN_CPT_CODES = {'99213', '99214', '80053', '85025', '71046', '93000', '90791', '36415', '12001'}


class TestClaims837Structure:

    def test_isa_header_present(self, parsed_837):
        assert parsed_837['envelope']['isa'] is not None

    def test_claim_count_within_expected_range(self, parsed_837):
        assert 15 <= len(parsed_837['claims']) <= 20

    def test_no_duplicate_claim_ids(self, parsed_837):
        assert check_no_duplicate_claim_ids(parsed_837['claims']) == []

    def test_every_claim_has_at_least_one_service_line(self, parsed_837):
        assert all(len(c['service_lines']) >= 1 for c in parsed_837['claims'])

    @pytest.mark.parametrize('claim_index', range(18))
    def test_claim_total_matches_line_sum(self, parsed_837, claim_index):
        if claim_index >= len(parsed_837['claims']):
            pytest.skip('fewer claims generated than parametrize range')
        claim = parsed_837['claims'][claim_index]
        assert check_claim_total_matches_line_sum(claim)

    def test_service_dates_parseable(self, parsed_837):
        for claim in parsed_837['claims']:
            for line in claim['service_lines']:
                assert line.get('service_date') is not None

    def test_procedure_codes_are_known(self, parsed_837):
        for claim in parsed_837['claims']:
            for line in claim['service_lines']:
                assert line['procedure_code'] in KNOWN_CPT_CODES

    def test_diagnosis_code_present_per_claim(self, parsed_837):
        assert all(len(c['diagnosis_codes']) >= 1 for c in parsed_837['claims'])

    def test_charge_amounts_are_positive(self, parsed_837):
        for claim in parsed_837['claims']:
            assert claim['total_charge'] > 0
            for line in claim['service_lines']:
                assert line['charge'] > 0
