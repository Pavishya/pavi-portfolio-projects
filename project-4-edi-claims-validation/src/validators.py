"""
Reusable structural and business-rule validation functions for the EDI
834/837/835 claims validation framework. Pure functions, no I/O -- used
by pytest fixtures and importable standalone for pipeline validation.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set

TOLERANCE = Decimal('0.01')


def _close(a: Optional[Decimal], b: Optional[Decimal], tolerance: Decimal = TOLERANCE) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tolerance


# ---------------------------------------------------------------------------
# Structural validators
# ---------------------------------------------------------------------------

def check_segment_count_matches(se_segment: List[str], actual_segment_count: int) -> bool:
    """SE01 declared count must equal the actual number of segments between ST and SE inclusive."""
    if not se_segment or len(se_segment) < 2:
        return False
    return int(se_segment[1]) == actual_segment_count


def check_control_number_consistency(isa: List[str], iea: List[str]) -> bool:
    """ISA13 (interchange control number) must equal IEA02."""
    if not isa or not iea or len(isa) < 14 or len(iea) < 3:
        return False
    return isa[13] == iea[2]


def check_group_control_consistency(gs: List[str], ge: List[str]) -> bool:
    """GS06 (group control number) must equal GE02."""
    if not gs or not ge or len(gs) < 7 or len(ge) < 3:
        return False
    return gs[6] == ge[2]


def check_st_se_control_match(st: List[str], se: List[str]) -> bool:
    """ST02 transaction control number must equal SE02."""
    if not st or not se or len(st) < 3 or len(se) < 3:
        return False
    return st[2] == se[2]


def check_required_segments_present(segments_by_id: Dict[str, list], required: List[str]) -> List[str]:
    """Return list of required segment IDs missing from a transaction set."""
    return [seg_id for seg_id in required if seg_id not in segments_by_id]


def check_no_duplicate_claim_ids(claims: List[Dict]) -> List[str]:
    """Return list of claim_id values that appear more than once in the 837 claims list."""
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for claim in claims:
        claim_id = claim.get('claim_id')
        if claim_id in seen:
            duplicates.add(claim_id)
        seen.add(claim_id)
    return sorted(duplicates)


def check_claim_total_matches_line_sum(claim: Dict) -> bool:
    """837 structural check: total_charge (CLM02) must equal sum of service_line charges (within $0.01)."""
    line_sum = sum((line.get('charge') or Decimal('0')) for line in claim.get('service_lines', []))
    return _close(claim.get('total_charge'), line_sum)


# ---------------------------------------------------------------------------
# Business / reconciliation validators
# ---------------------------------------------------------------------------

def check_member_exists_in_enrollment(claim_member_id: str, enrolled_member_ids: Set[str]) -> bool:
    """837 claim's member_id must be present in the 834 enrollment roster (eligibility check)."""
    return claim_member_id in enrolled_member_ids


def find_claims_without_eligible_member(claims: List[Dict], enrolled_member_ids: Set[str]) -> List[str]:
    """Return claim_ids referencing a member_id not found in 834 enrollment."""
    return [c['claim_id'] for c in claims if c.get('member_id') not in enrolled_member_ids]


def reconcile_claims_to_remittance(claims: List[Dict], remittances: List[Dict]) -> Dict:
    """
    Cross-reference 837 claim_ids against 835 claim_payment claim_ids.
    Returns {'unmatched_claims': [...], 'unmatched_remittances': [...], 'matched_count': int}.
    """
    claim_ids = {c['claim_id'] for c in claims}
    remittance_ids = {r['claim_id'] for r in remittances}
    return {
        'unmatched_claims': sorted(claim_ids - remittance_ids),
        'unmatched_remittances': sorted(remittance_ids - claim_ids),
        'matched_count': len(claim_ids & remittance_ids),
    }


def check_remittance_charge_matches_claim(claim: Dict, remittance: Dict) -> bool:
    """For a matched claim_id, 835 charge_amount (CLP03) must equal 837 total_charge (CLM02)."""
    return _close(claim.get('total_charge'), remittance.get('charge_amount'))


def check_paid_plus_adjustment_equals_charge(remittance_claim: Dict) -> bool:
    """
    835 adjudication arithmetic: paid_amount + sum(all CAS adjustments, every
    group code) == charge_amount. Patient responsibility (CLP05) is itself a
    summary of the PR-group CAS adjustments, not an additional amount on top
    of them -- see check_patient_responsibility_matches_pr_adjustments.
    """
    paid = remittance_claim.get('paid_amount') or Decimal('0')
    adjustment_total = sum(
        (adj.get('amount') or Decimal('0'))
        for sp in remittance_claim.get('service_payments', [])
        for adj in sp.get('adjustments', [])
    )
    return _close(paid + adjustment_total, remittance_claim.get('charge_amount'))


def check_patient_responsibility_matches_pr_adjustments(remittance_claim: Dict) -> bool:
    """CLP05 (patient_responsibility) must equal the sum of PR-group-code CAS adjustment amounts."""
    pr_total = sum(
        (adj.get('amount') or Decimal('0'))
        for sp in remittance_claim.get('service_payments', [])
        for adj in sp.get('adjustments', [])
        if adj.get('group_code') == 'PR'
    )
    return _close(remittance_claim.get('patient_responsibility') or Decimal('0'), pr_total)


def check_total_payment_matches_claim_sum(parsed_835: Dict) -> bool:
    """BPR02 (total_payment) must equal sum of CLP04 (paid_amount) across all claim_payments."""
    claim_sum = sum((cp.get('paid_amount') or Decimal('0')) for cp in parsed_835.get('claim_payments', []))
    return _close(parsed_835.get('total_payment'), claim_sum)


def check_denied_claims_have_zero_payment(remittances: List[Dict]) -> List[str]:
    """Return claim_ids with status_code == '4' (denied) but paid_amount != 0 -- should be empty."""
    return [
        r['claim_id'] for r in remittances
        if r.get('status_code') == '4' and (r.get('paid_amount') or Decimal('0')) != Decimal('0')
    ]


def check_service_line_paid_le_charge(service_payment: Dict) -> bool:
    """No service line should pay more than it charged (paid <= charge)."""
    paid = service_payment.get('paid')
    charge = service_payment.get('charge')
    if paid is None or charge is None:
        return False
    return paid <= charge + TOLERANCE
