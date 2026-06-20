"""Structural tests for the X12 834 enrollment file."""

import pytest


class TestEnrollment834Structure:

    def test_isa_header_present(self, parsed_834):
        assert parsed_834['envelope']['isa'] is not None
        assert parsed_834['envelope']['isa'][0] == 'ISA'

    def test_sponsor_present(self, parsed_834):
        assert parsed_834['sponsor'] is not None
        assert parsed_834['sponsor']['name']

    def test_member_count_matches_expected(self, parsed_834):
        assert len(parsed_834['members']) == 8

    def test_all_members_have_member_id(self, parsed_834):
        assert all(m['member_id'] for m in parsed_834['members'])

    def test_all_members_have_dob_parseable(self, parsed_834):
        assert all(m['dob'] is not None for m in parsed_834['members'])

    def test_no_duplicate_member_ids(self, parsed_834):
        ids = [m['member_id'] for m in parsed_834['members']]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize('valid_gender', ['M', 'F'])
    def test_gender_is_in_allowed_set(self, parsed_834, valid_gender):
        genders = {m['gender'] for m in parsed_834['members']}
        assert genders <= {'M', 'F'}

    @pytest.mark.parametrize('maint_type', ['030', '024', '001'])
    def test_maintenance_type_values_are_known(self, parsed_834, maint_type):
        seen_types = {m['maintenance_type'] for m in parsed_834['members']}
        assert maint_type in seen_types

    def test_coverage_effective_date_not_null(self, parsed_834):
        assert all(m['coverage_effective_date'] is not None for m in parsed_834['members'])

    @pytest.mark.parametrize('group', ['GRP100', 'GRP200'])
    def test_group_number_is_known_value(self, parsed_834, group):
        groups = {m['group_number'] for m in parsed_834['members']}
        assert group in groups
