"""
Structured parser for the X12 835 (Health Care Claim Payment/Remittance
Advice) transaction set, matching the segment layout produced by
generators/03_generate_835.py (Loop 1000A/1000B/2000/2100/2110, simplified).
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


def extract_claim_payments(body_segments: List[List[str]]) -> List[Dict]:
    """Walk segments; each CLP starts a new claim payment block."""
    claim_payments: List[Dict] = []
    current_claim = None
    current_service = None

    for elements in body_segments:
        seg_id = elements[0]

        if seg_id == 'CLP':
            current_claim = {
                'claim_id': elements[1] if len(elements) > 1 else None,
                'status_code': elements[2] if len(elements) > 2 else None,
                'charge_amount': _parse_decimal(elements[3]) if len(elements) > 3 else None,
                'paid_amount': _parse_decimal(elements[4]) if len(elements) > 4 else None,
                'patient_responsibility': _parse_decimal(elements[5]) if len(elements) > 5 else None,
                'member_id': None,
                'service_payments': [],
            }
            claim_payments.append(current_claim)
            current_service = None
        elif seg_id == 'NM1' and current_claim is not None and len(elements) > 1 and elements[1] == 'QC':
            current_claim['member_id'] = elements[-1]
        elif seg_id == 'SVC' and current_claim is not None:
            procedure_raw = elements[1] if len(elements) > 1 else ''
            current_service = {
                'procedure_code': procedure_raw.split(':')[-1] if procedure_raw else None,
                'charge': _parse_decimal(elements[2]) if len(elements) > 2 else None,
                'paid': _parse_decimal(elements[3]) if len(elements) > 3 else None,
                'adjustments': [],
            }
            current_claim['service_payments'].append(current_service)
        elif seg_id == 'CAS' and current_service is not None:
            current_service['adjustments'].append({
                'group_code': elements[1] if len(elements) > 1 else None,
                'reason_code': elements[2] if len(elements) > 2 else None,
                'amount': _parse_decimal(elements[3]) if len(elements) > 3 else None,
            })
        elif seg_id == 'DTP' and current_service is not None and len(elements) > 1 and elements[1] == '472':
            current_service['service_date'] = _parse_date(elements[3]) if len(elements) > 3 else None

    return claim_payments


def parse_835(raw_text: str) -> Dict:
    """
    Returns:
    {
        'envelope': {...},
        'payer': {...}, 'payee': {...},
        'total_payment': Decimal,           # BPR02
        'claim_payments': [
            {
                'claim_id': str, 'status_code': str, 'charge_amount': Decimal,
                'paid_amount': Decimal, 'patient_responsibility': Decimal,
                'member_id': str,
                'service_payments': [{'procedure_code','charge','paid','adjustments':[...]}],
            }, ...
        ],
    }
    """
    segments = split_segments(raw_text)
    envelope = parse_envelope(segments)
    transaction = envelope['st_transactions'][0]
    body = transaction['body_segments']

    payer = None
    payee = None
    total_payment = None

    for elements in body:
        seg_id = elements[0]
        if seg_id == 'BPR':
            total_payment = _parse_decimal(elements[2]) if len(elements) > 2 else None
        elif seg_id == 'N1' and len(elements) > 1 and elements[1] == 'PR':
            payer = {'name': elements[2] if len(elements) > 2 else None}
        elif seg_id == 'N1' and len(elements) > 1 and elements[1] == 'PE':
            payee = {'name': elements[2] if len(elements) > 2 else None,
                     'npi': elements[-1] if len(elements) > 1 else None}

    return {
        'envelope': envelope,
        'payer': payer,
        'payee': payee,
        'total_payment': total_payment,
        'claim_payments': extract_claim_payments(body),
    }


def parse_835_file(path: str) -> Dict:
    return parse_835(read_edi_file(path))
