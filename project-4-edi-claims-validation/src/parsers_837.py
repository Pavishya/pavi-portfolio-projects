"""
Structured parser for the X12 837P (Professional Healthcare Claim)
transaction set, matching the segment layout produced by
generators/02_generate_837.py (one ST...SE transaction per claim,
Loop 2000A/2300/2400, simplified).
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edi_parser import read_edi_file, split_segments, parse_envelope  # noqa: E402


def _parse_date(value: str):
    if not value:
        return None
    return datetime.strptime(value, '%Y%m%d').date()


def _parse_decimal(value: str):
    if value in (None, ''):
        return None
    return Decimal(value)


def _extract_one_claim(body_segments: List[List[str]]) -> Dict:
    """Each 837 transaction in this synthetic dataset contains exactly one claim."""
    billing_provider = None
    member_id = None
    claim = None
    service_lines: List[Dict] = []
    diagnosis_codes: List[str] = []
    current_line = None

    for elements in body_segments:
        seg_id = elements[0]

        if seg_id == 'NM1' and len(elements) > 1 and elements[1] == '85':
            billing_provider = {
                'name': elements[2] if len(elements) > 2 else None,
                'npi': elements[-1] if len(elements) > 1 else None,
            }
        elif seg_id == 'NM1' and len(elements) > 1 and elements[1] == 'IL':
            member_id = elements[-1]
        elif seg_id == 'CLM':
            claim = {
                'claim_id': elements[1] if len(elements) > 1 else None,
                'total_charge': _parse_decimal(elements[2]) if len(elements) > 2 else None,
                'place_of_service': elements[5].split(':')[0] if len(elements) > 5 and elements[5] else None,
            }
        elif seg_id == 'HI':
            for el in elements[1:]:
                if ':' in el:
                    diagnosis_codes.append(el.split(':')[1])
        elif seg_id == 'LX':
            current_line = {'line_number': int(elements[1]) if len(elements) > 1 else None}
            service_lines.append(current_line)
        elif seg_id == 'SV1' and current_line is not None:
            procedure_raw = elements[1] if len(elements) > 1 else ''
            current_line['procedure_code'] = procedure_raw.split(':')[-1] if procedure_raw else None
            current_line['charge'] = _parse_decimal(elements[2]) if len(elements) > 2 else None
            current_line['units'] = int(elements[4]) if len(elements) > 4 and elements[4] else None
            current_line['diagnosis_pointer'] = elements[7] if len(elements) > 7 else None
        elif seg_id == 'DTP' and current_line is not None and len(elements) > 1 and elements[1] == '472':
            current_line['service_date'] = _parse_date(elements[3]) if len(elements) > 3 else None

    claim = claim or {}
    claim['member_id'] = member_id
    claim['billing_provider'] = billing_provider
    claim['diagnosis_codes'] = diagnosis_codes
    claim['service_lines'] = service_lines
    return claim


def extract_claims(envelope: Dict) -> List[Dict]:
    """One claim per ST...SE transaction block."""
    return [_extract_one_claim(t['body_segments']) for t in envelope['st_transactions']]


def parse_837(raw_text: str) -> Dict:
    """
    Returns:
    {
        'envelope': {...},
        'claims': [
            {
                'claim_id': str, 'total_charge': Decimal, 'member_id': str,
                'place_of_service': str, 'billing_provider': {...},
                'diagnosis_codes': [str], 'service_lines': [{...}],
            }, ...
        ],
    }
    """
    segments = split_segments(raw_text)
    envelope = parse_envelope(segments)
    return {
        'envelope': envelope,
        'claims': extract_claims(envelope),
    }


def parse_837_file(path: str) -> Dict:
    return parse_837(read_edi_file(path))
