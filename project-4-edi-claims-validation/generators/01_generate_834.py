"""
Generate a synthetic X12 834 (Benefit Enrollment and Maintenance) file
from the shared member roster. Run 00_generate_members.py first.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _x12_writer import seg, build_full_envelope  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_members_seed.json')
OUT_FILE = os.path.join(ROOT, 'data', 'raw', '834_enrollment.edi')

SENDER_ID = 'ACMEHEALTH'
RECEIVER_ID = 'COGNIZANT'
SPONSOR_NAME = 'ACME HEALTH PLAN'
PAYER_NAME = 'COGNIZANT HEALTH PAYER'


def build_member_loop(member: dict) -> list:
    """INS-anchored loop (Loop 2000/2100A/2300 simplified) for one member."""
    return [
        seg('INS', 'Y', member['relationship_code'], member['maintenance_type'], 'XN', 'A', '', '', 'FT'),
        seg('REF', '0F', member['member_id']),
        seg('REF', '1L', member['group_number']),
        seg('DTP', '356', 'D8', member['coverage_effective_date']),
        seg('NM1', 'IL', '1', member['last_name'], member['first_name'], '', '', '', '34', member['member_id']),
        seg('N3', member['address']),
        seg('N4', member['city'], member['state'], member['zip']),
        seg('DMG', 'D8', member['dob'], member['gender']),
        seg('HD', '030', '', 'HLT', member['plan_code']),
        seg('DTP', '348', 'D8', member['coverage_effective_date']),
    ]


def generate_834(members: list) -> str:
    body_segments = [
        seg('BGN', '00', 'REF12345', '20240601', '1200', '', '', '', '4'),
        seg('N1', 'P5', SPONSOR_NAME, 'FI', '123456789'),
        seg('N1', 'IN', PAYER_NAME, 'FI', '987654321'),
    ]
    for member in members:
        body_segments.extend(build_member_loop(member))

    transactions = [('834', '0001', body_segments)]
    return build_full_envelope(
        functional_id_code='BE', version='005010X220A1',
        sender_id=SENDER_ID, receiver_id=RECEIVER_ID,
        transactions=transactions,
        interchange_control_number='000000001',
        group_control_number='1',
        date_str='240601', time_str='1200',
    )


def main():
    if not os.path.exists(SEED_JSON):
        raise SystemExit(f'{SEED_JSON} not found. Run 00_generate_members.py first.')
    with open(SEED_JSON) as f:
        seed_data = json.load(f)

    edi_text = generate_834(seed_data['members'])
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        f.write(edi_text)
    print(f'Wrote 834 enrollment file for {len(seed_data["members"])} members to {OUT_FILE}')


if __name__ == '__main__':
    main()
