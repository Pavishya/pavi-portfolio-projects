"""
Cross-file envelope integrity tests: ISA/IEA, GS/GE, and ST/SE control
number balancing, plus SE01 segment-count validation. Parametrized across
all three EDI files since the envelope rules are identical for each.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import (  # noqa: E402
    check_control_number_consistency,
    check_group_control_consistency,
    check_st_se_control_match,
    check_segment_count_matches,
)

FILE_LABELS = ['834', '837', '835']


class TestEnvelopeIntegrity:

    @pytest.mark.parametrize('file_label', FILE_LABELS)
    def test_isa_iea_control_number_matches(self, request, file_label):
        parsed = request.getfixturevalue(f'parsed_{file_label}')
        envelope = parsed['envelope']
        assert check_control_number_consistency(envelope['isa'], envelope['iea'])

    @pytest.mark.parametrize('file_label', FILE_LABELS)
    def test_gs_ge_control_number_matches(self, request, file_label):
        parsed = request.getfixturevalue(f'parsed_{file_label}')
        envelope = parsed['envelope']
        assert check_group_control_consistency(envelope['gs'], envelope['ge'])

    @pytest.mark.parametrize('file_label', FILE_LABELS)
    def test_st_se_control_number_matches_for_every_transaction(self, request, file_label):
        parsed = request.getfixturevalue(f'parsed_{file_label}')
        for transaction in parsed['envelope']['st_transactions']:
            assert check_st_se_control_match(transaction['st'], transaction['se'])

    @pytest.mark.parametrize('file_label', FILE_LABELS)
    def test_se01_segment_count_matches_actual_for_every_transaction(self, request, file_label):
        parsed = request.getfixturevalue(f'parsed_{file_label}')
        for transaction in parsed['envelope']['st_transactions']:
            # ST + body segments + SE itself
            actual_count = 1 + len(transaction['body_segments']) + 1
            assert check_segment_count_matches(transaction['se'], actual_count)

    @pytest.mark.parametrize('file_label', FILE_LABELS)
    def test_ge_transaction_count_matches_st_count(self, request, file_label):
        parsed = request.getfixturevalue(f'parsed_{file_label}')
        envelope = parsed['envelope']
        assert int(envelope['ge'][1]) == len(envelope['st_transactions'])
