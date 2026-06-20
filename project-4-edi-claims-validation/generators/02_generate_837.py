"""
Generate a synthetic X12 837P (Professional Healthcare Claim) file from
the shared member roster + CPT reference table. Run 00_generate_members.py
first. Also writes data/raw/_claims_seed.json so 03_generate_835.py can
adjudicate the exact same claims.
"""

import json
import os
import random
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _x12_writer import seg, build_transaction, build_isa, build_gs, build_ge, build_iea  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_members_seed.json')
CLAIMS_SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_claims_seed.json')
OUT_FILE = os.path.join(ROOT, 'data', 'raw', '837_claims.edi')

SENDER_ID = 'COGNIZANT'
RECEIVER_ID = 'ACMEHEALTH'
CLEARINGHOUSE_NAME = 'COGNIZANT CLEARINGHOUSE'
PAYER_NAME = 'ACME HEALTH PLAN'

N_CLAIMS = 18
SEED = 42


def round2(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def build_claims(members: list, providers: list, cpt_codes: list, icd10_codes: list,
                  n_claims: int = N_CLAIMS, seed: int = SEED) -> list:
    """
    Build n_claims claim dicts referencing the given members/providers.
    Every claim references a real enrolled member (eligibility stays clean
    on the golden file; negative cases live in a separate test fixture).
    """
    rng = random.Random(seed)
    claims = []
    for i in range(n_claims):
        member = rng.choice(members)
        provider = rng.choice(providers)
        n_lines = rng.randint(1, 3)
        lines = []
        for line_no in range(1, n_lines + 1):
            cpt = rng.choice(cpt_codes)
            charge = round2(rng.uniform(cpt['charge_min'], cpt['charge_max']))
            lines.append({
                'line_number': line_no,
                'procedure_code': cpt['code'],
                'charge': str(charge),
                'units': 1,
                'service_date': '20240610',
                'diagnosis_pointer': '1',
            })
        total_charge = sum(Decimal(line['charge']) for line in lines)
        claims.append({
            'claim_id': f'CLAIM{i + 1:05d}',
            'member_id': member['member_id'],
            'provider_npi': provider['npi'],
            'provider_name': provider['name'],
            'total_charge': str(total_charge),
            'diagnosis_code': rng.choice(icd10_codes),
            'place_of_service': '11',
            'service_lines': lines,
        })
    return claims


def build_claim_body(member: dict, provider: dict, claim: dict) -> list:
    """Body segments for a single ST...SE claim transaction (Loop 2000A/2300/2400, simplified)."""
    body = [
        seg('BHT', '0019', '00', f'BATCH{claim["claim_id"][-5:]}', '20240615', '0900', 'CH'),
        seg('NM1', '41', '2', CLEARINGHOUSE_NAME, '', '', '', '', '46', 'SUBMITTER01'),
        seg('NM1', '40', '2', PAYER_NAME, '', '', '', '', '46', 'RECEIVER01'),
        seg('HL', '1', '', '20', '1'),
        seg('NM1', '85', '2', provider['name'], '', '', '', '', 'XX', provider['npi']),
        seg('N3', provider['address']),
        seg('N4', provider['city'], provider['state'], provider['zip']),
        seg('HL', '2', '1', '22', '0'),
        seg('SBR', 'P', '18', member['group_number'], '', '', '', '', '', 'CI'),
        seg('NM1', 'IL', '1', member['last_name'], member['first_name'], '', '', '', 'MI', member['member_id']),
        seg('N3', member['address']),
        seg('N4', member['city'], member['state'], member['zip']),
        seg('DMG', 'D8', member['dob'], member['gender']),
        seg('CLM', claim['claim_id'], claim['total_charge'], '', '', f'{claim["place_of_service"]}:B:1', 'Y', 'A', 'Y', 'Y'),
        seg('HI', f'ABK:{claim["diagnosis_code"]}'),
    ]
    for line in claim['service_lines']:
        body.append(seg('LX', line['line_number']))
        body.append(seg('SV1', f'HC:{line["procedure_code"]}', line['charge'], 'UN', line['units'], '', '', line['diagnosis_pointer']))
        body.append(seg('DTP', '472', 'D8', line['service_date']))
    return body


def generate_837(members: list, providers: list, claims: list) -> str:
    members_by_id = {m['member_id']: m for m in members}
    providers_by_npi = {p['npi']: p for p in providers}

    out = [build_isa(SENDER_ID, RECEIVER_ID, '000000002', '240615', '0900')]
    out.append(build_gs('HC', SENDER_ID, RECEIVER_ID, '1', '240615', '0900', '005010X222A1'))

    for idx, claim in enumerate(claims, start=1):
        member = members_by_id[claim['member_id']]
        provider = providers_by_npi[claim['provider_npi']]
        body = build_claim_body(member, provider, claim)
        st_control = f'{idx:04d}'
        out.extend(build_transaction('837', st_control, body))

    out.append(build_ge(len(claims), '1'))
    out.append(build_iea(1, '000000002'))
    return ''.join(out)


def main():
    if not os.path.exists(SEED_JSON):
        raise SystemExit(f'{SEED_JSON} not found. Run 00_generate_members.py first.')
    with open(SEED_JSON) as f:
        seed_data = json.load(f)

    claims = build_claims(seed_data['members'], seed_data['providers'],
                           seed_data['cpt_codes'], seed_data['icd10_codes'])

    edi_text = generate_837(seed_data['members'], seed_data['providers'], claims)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        f.write(edi_text)

    with open(CLAIMS_SEED_JSON, 'w') as f:
        json.dump(claims, f, indent=2)

    print(f'Wrote {len(claims)} claims to {OUT_FILE} (seed data: {CLAIMS_SEED_JSON})')


if __name__ == '__main__':
    main()
