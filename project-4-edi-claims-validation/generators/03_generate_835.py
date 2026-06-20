"""
Generate a synthetic X12 835 (Health Care Claim Payment/Remittance Advice)
file that adjudicates every claim produced by 02_generate_837.py. Run
00_generate_members.py and 02_generate_837.py first.
"""

import json
import os
import random
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _x12_writer import seg, build_full_envelope  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBERS_SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_members_seed.json')
CLAIMS_SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_claims_seed.json')
OUT_FILE = os.path.join(ROOT, 'data', 'raw', '835_remittance.edi')

SENDER_ID = 'ACMEHEALTH'
RECEIVER_ID = 'COGNIZANT'
PAYER_NAME = 'ACME HEALTH PLAN'

ADJUSTMENT_RATE = Decimal('0.15')
FIXED_COPAY = Decimal('25.00')
SEED = 42
N_DENIED = 2


def round2(value) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def adjudicate_approved(claim: dict) -> dict:
    """Split an approved claim's charge into paid / contractual adjustment / patient responsibility."""
    lines = claim['service_lines']
    line_charges = [Decimal(line['charge']) for line in lines]
    charge_total = sum(line_charges)

    # Per-line contractual write-off (CO/45), last line absorbs rounding remainder.
    line_adjs = [round2(c * ADJUSTMENT_RATE) for c in line_charges[:-1]]
    contractual_total = round2(charge_total * ADJUSTMENT_RATE)
    line_adjs.append(contractual_total - sum(line_adjs))

    available = charge_total - contractual_total
    patient_resp = min(FIXED_COPAY, available) if available > 0 else Decimal('0.00')
    claim_paid = available - patient_resp

    line_paid = [c - a for c, a in zip(line_charges, line_adjs)]
    # Apply the patient-responsibility deduction to the highest-charge line so
    # sum(line_paid) reconciles exactly to claim_paid.
    largest_idx = max(range(len(lines)), key=lambda i: line_charges[i])
    line_paid[largest_idx] -= patient_resp

    service_payments = []
    for line, charge, paid, adj in zip(lines, line_charges, line_paid, line_adjs):
        adjustments = [{'group_code': 'CO', 'reason_code': '45', 'amount': str(adj)}]
        if largest_idx == lines.index(line) and patient_resp > 0:
            adjustments.append({'group_code': 'PR', 'reason_code': '1', 'amount': str(patient_resp)})
        service_payments.append({
            'procedure_code': line['procedure_code'],
            'charge': str(charge),
            'paid': str(paid),
            'adjustments': adjustments,
        })

    return {
        'claim_id': claim['claim_id'],
        'member_id': claim['member_id'],
        'status_code': '1',
        'charge_amount': str(charge_total),
        'paid_amount': str(claim_paid),
        'patient_responsibility': str(patient_resp),
        'service_payments': service_payments,
    }


def adjudicate_denied(claim: dict) -> dict:
    """Fully deny a claim: paid = 0, full charge written off (CO/50), patient owes nothing."""
    lines = claim['service_lines']
    charge_total = Decimal(claim['total_charge'])
    service_payments = []
    for line in lines:
        charge = Decimal(line['charge'])
        service_payments.append({
            'procedure_code': line['procedure_code'],
            'charge': str(charge),
            'paid': '0.00',
            'adjustments': [{'group_code': 'CO', 'reason_code': '50', 'amount': str(charge)}],
        })
    return {
        'claim_id': claim['claim_id'],
        'member_id': claim['member_id'],
        'status_code': '4',
        'charge_amount': str(charge_total),
        'paid_amount': '0.00',
        'patient_responsibility': '0.00',
        'service_payments': service_payments,
    }


def adjudicate_claims(claims: list, n_denied: int = N_DENIED, seed: int = SEED) -> list:
    rng = random.Random(seed + 1)  # different stream from the 837 generator
    denied_ids = set(rng.sample([c['claim_id'] for c in claims], n_denied))

    remittances = []
    for claim in claims:
        if claim['claim_id'] in denied_ids:
            remittances.append(adjudicate_denied(claim))
        else:
            remittances.append(adjudicate_approved(claim))
    return remittances


def build_remittance_body(members_by_id: dict, payee_name: str, payee_npi: str,
                           remittances: list, total_payment: Decimal) -> list:
    body = [
        seg('BPR', 'I', str(total_payment), 'C', 'CHK', '', '', '', '', '', '', '', '', '20240625'),
        seg('TRN', '1', 'RA0001', '1987654321'),
        seg('N1', 'PR', PAYER_NAME),
        seg('N1', 'PE', payee_name, 'XX', payee_npi),
    ]
    for idx, rem in enumerate(remittances, start=1):
        member = members_by_id[rem['member_id']]
        body.append(seg('LX', idx))
        body.append(seg('CLP', rem['claim_id'], rem['status_code'], rem['charge_amount'],
                         rem['paid_amount'], rem['patient_responsibility'], 'HM', f'RA0001-{idx}'))
        body.append(seg('NM1', 'QC', '1', member['last_name'], member['first_name'], '', '', '', 'MI', member['member_id']))
        for sp in rem['service_payments']:
            body.append(seg('SVC', f'HC:{sp["procedure_code"]}', sp['charge'], sp['paid'], '', '1'))
            for adj in sp['adjustments']:
                body.append(seg('CAS', adj['group_code'], adj['reason_code'], adj['amount']))
            body.append(seg('DTP', '472', 'D8', '20240610'))
    return body


def generate_835(members: list, claims: list, remittances: list, payee_name: str, payee_npi: str) -> str:
    members_by_id = {m['member_id']: m for m in members}
    total_payment = round2(sum(Decimal(r['paid_amount']) for r in remittances))
    body = build_remittance_body(members_by_id, payee_name, payee_npi, remittances, total_payment)

    transactions = [('835', '0001', body)]
    return build_full_envelope(
        functional_id_code='HP', version='005010X221A1',
        sender_id=SENDER_ID, receiver_id=RECEIVER_ID,
        transactions=transactions,
        interchange_control_number='000000003',
        group_control_number='1',
        date_str='240625', time_str='1000',
    )


def main():
    if not os.path.exists(CLAIMS_SEED_JSON):
        raise SystemExit(f'{CLAIMS_SEED_JSON} not found. Run 02_generate_837.py first.')
    with open(MEMBERS_SEED_JSON) as f:
        seed_data = json.load(f)
    with open(CLAIMS_SEED_JSON) as f:
        claims = json.load(f)

    remittances = adjudicate_claims(claims)
    # Single payee for this synthetic batch (all claims share one billing provider context).
    payee_name = claims[0]['provider_name']
    payee_npi = claims[0]['provider_npi']

    edi_text = generate_835(seed_data['members'], claims, remittances, payee_name, payee_npi)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        f.write(edi_text)

    n_denied = sum(1 for r in remittances if r['status_code'] == '4')
    print(f'Wrote remittance for {len(remittances)} claims ({n_denied} denied) to {OUT_FILE}')


if __name__ == '__main__':
    main()
