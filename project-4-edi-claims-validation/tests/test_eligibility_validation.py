"""Member eligibility cross-checks: 837 claims must reference valid 834 enrollees."""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import find_claims_without_eligible_member  # noqa: E402


class TestMemberEligibility:

    def test_all_claim_members_exist_in_enrollment(self, parsed_837, enrolled_member_ids):
        for claim in parsed_837['claims']:
            assert claim['member_id'] in enrolled_member_ids

    def test_no_orphaned_claims(self, parsed_837, enrolled_member_ids):
        assert find_claims_without_eligible_member(parsed_837['claims'], enrolled_member_ids) == []

    def test_enrolled_member_ids_are_unique(self, parsed_834):
        ids = [m['member_id'] for m in parsed_834['members']]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize('member_id_pattern', [r'^MBR\d+$'])
    def test_claim_member_ids_are_well_formed(self, parsed_837, member_id_pattern):
        for claim in parsed_837['claims']:
            assert re.match(member_id_pattern, claim['member_id'])

    def test_terminated_member_flagged_in_834(self, parsed_834):
        terminated = [m for m in parsed_834['members'] if m['maintenance_type'] == '024']
        assert len(terminated) == 1

    def test_member_coverage_effective_before_claim_service_date(self, parsed_834, parsed_837):
        members_by_id = {m['member_id']: m for m in parsed_834['members']}
        for claim in parsed_837['claims']:
            member = members_by_id.get(claim['member_id'])
            assert member is not None
            for line in claim['service_lines']:
                assert member['coverage_effective_date'] <= line['service_date']
