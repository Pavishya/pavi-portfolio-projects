"""
Structured parser for the X12 834 (Benefit Enrollment and Maintenance)
transaction set, matching the segment layout produced by
generators/01_generate_834.py (Loop 2000/2100A/2300, simplified).
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edi_parser import read_edi_file, split_segments, parse_envelope  # noqa: E402


def _parse_date(value: str):
    if not value:
        return None
    return datetime.strptime(value, '%Y%m%d').date()


def extract_members(body_segments: List[List[str]]) -> List[Dict]:
    """Walk segments, starting a new member dict at each INS, until the next INS or end."""
    members: List[Dict] = []
    current = None

    for elements in body_segments:
        seg_id = elements[0]

        if seg_id == 'INS':
            current = {
                'relationship_code': elements[2] if len(elements) > 2 else None,
                'maintenance_type': elements[3] if len(elements) > 3 else None,
                'member_id': None,
                'subscriber_id': None,
                'group_number': None,
                'first_name': None,
                'last_name': None,
                'address': None,
                'city': None,
                'state': None,
                'zip': None,
                'dob': None,
                'gender': None,
                'plan_code': None,
                'coverage_effective_date': None,
                'benefit_begin_date': None,
            }
            members.append(current)
            continue

        if current is None:
            continue

        if seg_id == 'REF':
            qualifier = elements[1] if len(elements) > 1 else None
            value = elements[2] if len(elements) > 2 else None
            if qualifier == '0F':
                current['member_id'] = value
                current['subscriber_id'] = value
            elif qualifier == '1L':
                current['group_number'] = value
        elif seg_id == 'DTP':
            qualifier = elements[1] if len(elements) > 1 else None
            date_val = _parse_date(elements[3]) if len(elements) > 3 else None
            if qualifier == '356':
                current['coverage_effective_date'] = date_val
            elif qualifier == '348':
                current['benefit_begin_date'] = date_val
        elif seg_id == 'NM1' and elements[1] == 'IL':
            current['last_name'] = elements[3] if len(elements) > 3 else None
            current['first_name'] = elements[4] if len(elements) > 4 else None
        elif seg_id == 'N3':
            current['address'] = elements[1] if len(elements) > 1 else None
        elif seg_id == 'N4':
            current['city'] = elements[1] if len(elements) > 1 else None
            current['state'] = elements[2] if len(elements) > 2 else None
            current['zip'] = elements[3] if len(elements) > 3 else None
        elif seg_id == 'DMG':
            current['dob'] = _parse_date(elements[2]) if len(elements) > 2 else None
            current['gender'] = elements[3] if len(elements) > 3 else None
        elif seg_id == 'HD':
            current['plan_code'] = elements[4] if len(elements) > 4 else None

    return members


def parse_834(raw_text: str) -> Dict:
    """
    Returns:
    {
        'envelope': {...},   # ISA/GS/ST/SE/GE/IEA control fields
        'sponsor': {...},    # N1*P5 segment
        'members': [...],
    }
    """
    segments = split_segments(raw_text)
    envelope = parse_envelope(segments)
    transaction = envelope['st_transactions'][0]
    body = transaction['body_segments']

    sponsor = None
    for elements in body:
        if elements[0] == 'N1' and elements[1] == 'P5':
            sponsor = {'name': elements[2] if len(elements) > 2 else None}
            break

    return {
        'envelope': envelope,
        'sponsor': sponsor,
        'members': extract_members(body),
    }


def parse_834_file(path: str) -> Dict:
    return parse_834(read_edi_file(path))
