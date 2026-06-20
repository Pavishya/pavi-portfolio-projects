# Project 4 — EDI Claims Validation Framework

**Domain:** Healthcare Payer / EDI  
**Tools:** Python · pytest · pytest-html · X12 834/837/835  
**Tests cover:** Synthetic enrollment, claims, and remittance EDI files generated end-to-end by this project

---

## Narrative

> *"Before a claim ever reaches adjudication, it has to survive the EDI pipeline — enrollment has to be current, the claim has to total correctly, and the remittance has to reconcile to the penny. I test that pipeline the way I'd test any other system: with reproducible test data, explicit assertions, and automated reporting."*

This project simulates the EDI layer that surrounds a claims platform like Facets — the X12 834 (enrollment), 837 (professional claim), and 835 (remittance advice) transaction sets a healthcare payer test engineer validates daily. It generates internally consistent, seeded synthetic data for all three transaction types, parses them with a dependency-light custom parser, and runs a pytest suite that proves structural integrity, cross-file eligibility, claims-to-remittance reconciliation, and adjudication arithmetic — plus a negative-path suite proving the validators actually catch bad data.

---

## Why This Project (Role Alignment)

Built specifically against the **Test Engineer — Healthcare/Facets** JD at Cognizant. Facets itself is proprietary and unavailable outside an enterprise license, so this project targets the EDI artifacts a Facets test engineer validates around the platform — the strongest legitimate proxy achievable in a public portfolio.

| JD Requirement | Demonstrated In |
|---|---|
| EDI 834 (enrollment) testing | `generators/01_generate_834.py`, `src/parsers_834.py`, `tests/test_834_structure.py` |
| EDI 837 (claims) testing | `generators/02_generate_837.py`, `src/parsers_837.py`, `tests/test_837_structure.py` |
| EDI 835 (remittance) testing | `generators/03_generate_835.py`, `src/parsers_835.py`, `tests/test_835_structure.py` |
| End-to-end claims processing validation (pricing, adjudication) | `tests/test_adjudication_arithmetic.py` — paid + adjustments reconcile to charge; patient responsibility ties to PR-group CAS amounts |
| Cross-module reconciliation (Membership ↔ Claims ↔ Billing) | `tests/test_eligibility_validation.py`, `tests/test_claims_reconciliation.py` |
| Data migration / reconciliation testing | `tests/test_envelope_integrity.py` — control-number and segment-count balancing across all three files, the same class of check used to validate a file made it through a system migration intact |
| Test automation | Full pytest suite (143 tests), session-scoped fixtures, parametrization, `pytest-html` reporting |
| Test data management | Seeded, reproducible synthetic data generation (`Faker(seed=42)`) with a shared roster (`data/raw/_members_seed.json`) reused across all three transaction types |
| Defect detection / negative testing | `tests/test_negative_cases.py` — deliberately malformed 837 fixture proves validators flag mismatched totals, orphaned members, overpayments, and unbalanced adjudication |

---

## Project Structure

```
project-4-edi-claims-validation/
├── data/raw/
│   ├── 834_enrollment.edi     ← 8-member enrollment file
│   ├── 837_claims.edi         ← 18 professional claims
│   └── 835_remittance.edi     ← adjudicated remittance advice
├── generators/
│   ├── 00_generate_members.py ← shared roster + reference data (CPT/ICD codes, providers), seeded Faker(42)
│   ├── 01_generate_834.py     ← builds the 834 enrollment file
│   ├── 02_generate_837.py     ← builds the 837P claims file
│   ├── 03_generate_835.py     ← adjudicates claims and builds the 835 remittance file
│   └── _x12_writer.py         ← shared ISA/GS/ST...SE/GE/IEA envelope helpers
├── src/
│   ├── edi_parser.py          ← generic segment/element parser, envelope structuring
│   ├── parsers_834.py         ← parse_834() -> {'envelope','sponsor','members'}
│   ├── parsers_837.py         ← parse_837() -> {'envelope','claims'}
│   ├── parsers_835.py         ← parse_835() -> {'envelope','payer','payee','total_payment','claim_payments'}
│   └── validators.py          ← reusable structural + business-rule validation functions
├── tests/
│   ├── conftest.py            ← session-scoped fixtures, graceful skip when data isn't generated yet
│   ├── test_834_structure.py
│   ├── test_837_structure.py
│   ├── test_835_structure.py
│   ├── test_envelope_integrity.py
│   ├── test_eligibility_validation.py
│   ├── test_claims_reconciliation.py
│   ├── test_adjudication_arithmetic.py
│   └── test_negative_cases.py
├── reports/                   ← pytest-html output (generated on run)
└── requirements.txt
```

---

## Test Coverage

### `test_834_structure.py` — 14 tests

| Test Group | What's Validated |
|---|---|
| Envelope | ISA header present and well-formed |
| Roster | Sponsor present; exactly 8 members; no duplicate member IDs |
| Member data | Every member has a member_id and a parseable DOB; coverage effective date not null |
| Allowed values | Gender ∈ {`M`, `F`} (parameterized); maintenance type ∈ {`030` add, `024` termination, `001` change} (parameterized) |
| Group assignment | Group number ∈ {`GRP100`, `GRP200`} (parameterized) |

### `test_837_structure.py` — 26 tests

| Test Group | What's Validated |
|---|---|
| Envelope | ISA header present |
| Volume | Claim count within 15-20 |
| Integrity | No duplicate claim IDs; every claim has ≥1 service line and ≥1 diagnosis code |
| Arithmetic | `CLM02` (total_charge) equals the sum of `SV1` line charges — parameterized across all 18 claims |
| Data quality | Service dates parseable; procedure codes drawn from the known CPT set; all charges positive |

### `test_835_structure.py` — 11 tests

| Test Group | What's Validated |
|---|---|
| Envelope | ISA header, payer and payee both present |
| Reconciliation | Claim payment count matches 837 claim count; total_payment (BPR02) equals sum of CLP04 |
| Adjudication | Paid amounts non-negative; denied claims (status `4`) have zero payment; ≥1 denied claim present for edge-case coverage |
| Line-level | No service line pays more than it charged; adjustment reason codes are from the known set (`CO/45`, `CO/50`, `PR/1`) |
| Status codes | status_code ∈ {`1`, `4`} (parameterized) |

### `test_envelope_integrity.py` — 15 tests

Parametrized across all three files (`834`, `837`, `835`) via `request.getfixturevalue()`:

| Test | What's Validated |
|---|---|
| ISA/IEA balancing | ISA13 (interchange control number) equals IEA02 |
| GS/GE balancing | GS06 (group control number) equals GE02 |
| ST/SE balancing | ST02 matches SE02 for every transaction in the file |
| Segment counts | SE01 declared count equals actual segments between ST and SE, inclusive |
| Transaction counts | GE01 equals the number of ST...SE transactions in the group |

### `test_eligibility_validation.py` — 6 tests

| Test | What's Validated |
|---|---|
| Cross-file membership | Every 837 claim's member_id exists in the 834 enrollment roster |
| No orphans | `find_claims_without_eligible_member()` returns empty on golden data |
| Roster integrity | Enrolled member IDs are unique |
| Format | Claim member IDs match `^MBR\d+$` (parameterized) |
| Lifecycle | Exactly one member is flagged terminated (`024`) in the 834 |
| Date logic | Member's coverage effective date precedes every claimed service date |

### `test_claims_reconciliation.py` — 25 tests

| Test | What's Validated |
|---|---|
| Coverage | Every 837 claim has a matching 835 remittance line |
| No orphans either direction | `reconcile_claims_to_remittance()` returns empty unmatched sets on both sides |
| Match count | Matched count equals total 837 claim count |
| Amount parity | 835 charge_amount equals 837 total_charge, per claim — parameterized across all 18 claims |
| Referential integrity | Every remittance claim_id references a real 837 claim |
| Aggregate | Sum of 837 charges equals sum of 835 charges across the whole file |

### `test_adjudication_arithmetic.py` — 41 tests

| Test | What's Validated |
|---|---|
| Core reconciliation | `paid_amount + sum(all CAS adjustments)` equals `charge_amount` — parameterized across all 18 claims |
| Patient responsibility | CLP05 equals the sum of PR-group-code CAS amounts only — parameterized across all 18 claims |
| Line-level sum | Service line paid amounts sum to the claim-level paid amount |
| Sign rules | Contractual (CO) adjustments and all payments are non-negative |
| Adjustment rate | Contractual write-off rate falls within the expected 5-30% band for non-denied claims |
| File-level total | BPR02 equals the sum of CLP04 across the whole remittance file |

### `test_negative_cases.py` — 5 tests

Uses a deliberately malformed inline 837 fixture (mismatched claim total, an unenrolled member, an overpaid service line) to prove the validators **detect** bad data rather than only passing quietly on good data:

| Test | What's Validated |
|---|---|
| `test_malformed_claim_total_mismatch_is_detected` | CLM02 ≠ SV1 line sum is caught |
| `test_orphaned_member_claim_is_detected` | Claim referencing a non-enrolled member is caught |
| `test_overpayment_above_charge_is_detected` | Service line paid > charged is caught |
| `test_unbalanced_adjudication_arithmetic_is_detected` | Paid + adjustments ≠ charge is caught |
| `test_duplicate_claim_ids_are_detected` | Repeated claim_id is caught |

---

## Key pytest Features Demonstrated

```python
# Parameterized tests across every claim in the file
@pytest.mark.parametrize('claim_index', range(18))
def test_claim_total_matches_line_sum(self, parsed_837, claim_index):
    if claim_index >= len(parsed_837['claims']):
        pytest.skip('fewer claims generated than parametrize range')
    assert check_claim_total_matches_line_sum(parsed_837['claims'][claim_index])

# Indirect fixture access — one test body, three files
@pytest.mark.parametrize('file_label', ['834', '837', '835'])
def test_isa_iea_control_number_matches(self, request, file_label):
    parsed = request.getfixturevalue(f'parsed_{file_label}')
    assert check_control_number_consistency(parsed['envelope']['isa'], parsed['envelope']['iea'])

# Session-scoped fixtures — each EDI file parsed once, shared across all tests
@pytest.fixture(scope='session')
def parsed_837(raw_837_text) -> dict:
    return parse_837(raw_837_text)

# Graceful skip when generators haven't been run yet
if not os.path.exists(PATH_834):
    pytest.skip(f'834 file not found at {PATH_834}. Run generators/01_generate_834.py first.')
```

---

## How to Run

```bash
# 1. Navigate to this project
cd project-4-edi-claims-validation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate the synthetic EDI files (seeded, reproducible)
python generators/00_generate_members.py
python generators/01_generate_834.py
python generators/02_generate_837.py
python generators/03_generate_835.py

# 4. Run all tests with HTML report
pytest tests/ --html=reports/test_report.html --self-contained-html -v

# 5. Open report
open reports/test_report.html
```

---

## Sample Output

```
tests/test_834_structure.py::TestEnrollment834Structure::test_member_count_matches_expected PASSED
tests/test_837_structure.py::TestClaims837Structure::test_claim_total_matches_line_sum[5] PASSED
tests/test_835_structure.py::TestRemittance835Structure::test_denied_claims_have_zero_payment PASSED
tests/test_envelope_integrity.py::TestEnvelopeIntegrity::test_isa_iea_control_number_matches[837] PASSED
tests/test_adjudication_arithmetic.py::TestAdjudicationArithmetic::test_patient_responsibility_matches_pr_adjustments[12] PASSED
tests/test_negative_cases.py::TestNegativeCases::test_unbalanced_adjudication_arithmetic_is_detected PASSED

===== 143 passed in 0.07s =====
```

---

## Skills Demonstrated

`X12 EDI` `834 Enrollment` `837 Claims` `835 Remittance` `pytest` `conftest.py` `Session Fixtures` `Parameterized Tests` `Indirect Fixtures` `pytest-html` `Claims Adjudication` `Reconciliation Testing` `Test Data Management` `Negative Testing` `Healthcare Payer Domain` `QA Automation`
