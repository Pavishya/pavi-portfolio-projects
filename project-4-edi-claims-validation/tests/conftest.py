"""
Shared fixtures for all test modules.
Parses the three generated EDI files once per session and exposes both
the raw structured parses and convenience lookups (enrolled member ids,
claims-by-id, remittances-by-claim-id) built on top of them.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from edi_parser import read_edi_file  # noqa: E402
from parsers_834 import parse_834  # noqa: E402
from parsers_837 import parse_837  # noqa: E402
from parsers_835 import parse_835  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(__file__))
EDI_DIR = os.path.join(ROOT, 'data', 'raw')
PATH_834 = os.path.join(EDI_DIR, '834_enrollment.edi')
PATH_837 = os.path.join(EDI_DIR, '837_claims.edi')
PATH_835 = os.path.join(EDI_DIR, '835_remittance.edi')


@pytest.fixture(scope='session')
def raw_834_text() -> str:
    if not os.path.exists(PATH_834):
        pytest.skip(f'834 file not found at {PATH_834}. Run generators/01_generate_834.py first.')
    return read_edi_file(PATH_834)


@pytest.fixture(scope='session')
def raw_837_text() -> str:
    if not os.path.exists(PATH_837):
        pytest.skip(f'837 file not found at {PATH_837}. Run generators/02_generate_837.py first.')
    return read_edi_file(PATH_837)


@pytest.fixture(scope='session')
def raw_835_text() -> str:
    if not os.path.exists(PATH_835):
        pytest.skip(f'835 file not found at {PATH_835}. Run generators/03_generate_835.py first.')
    return read_edi_file(PATH_835)


@pytest.fixture(scope='session')
def parsed_834(raw_834_text) -> dict:
    return parse_834(raw_834_text)


@pytest.fixture(scope='session')
def parsed_837(raw_837_text) -> dict:
    return parse_837(raw_837_text)


@pytest.fixture(scope='session')
def parsed_835(raw_835_text) -> dict:
    return parse_835(raw_835_text)


@pytest.fixture(scope='session')
def enrolled_member_ids(parsed_834) -> set:
    return {m['member_id'] for m in parsed_834['members']}


@pytest.fixture(scope='session')
def claims_by_id(parsed_837) -> dict:
    return {c['claim_id']: c for c in parsed_837['claims']}


@pytest.fixture(scope='session')
def remittances_by_claim_id(parsed_835) -> dict:
    return {r['claim_id']: r for r in parsed_835['claim_payments']}
