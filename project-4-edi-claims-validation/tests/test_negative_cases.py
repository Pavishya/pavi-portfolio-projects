"""
Negative-path tests: prove the parsers/validators correctly DETECT bad
data, rather than only passing quietly on good data. The golden generated
files (834/837/835) are kept internally consistent on purpose -- all
defect scenarios here are deliberately malformed fixtures defined inline,
never injected into the golden data.
"""

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from parsers_837 import parse_837  # noqa: E402
from validators import (  # noqa: E402
    check_claim_total_matches_line_sum,
    find_claims_without_eligible_member,
    check_service_line_paid_le_charge,
    check_paid_plus_adjustment_equals_charge,
    check_no_duplicate_claim_ids,
)

# Deliberately malformed 837: CLM02 ($500.00) does not equal the SV1 line
# sum ($150.00), and the member (MBR9999) does not exist in any enrollment.
MALFORMED_837 = """\
ISA*00*          *00*          *ZZ*TESTSENDER     *ZZ*TESTRECEIVER   *240701*1200*^*00501*000000099*0*T*:~
GS*HC*TESTSENDER*TESTRECEIVER*240701*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*BATCHBAD*20240701*1200*CH~
NM1*41*2*TEST CLEARINGHOUSE*****46*SUBMITTER01~
NM1*40*2*TEST PAYER*****46*RECEIVER01~
HL*1**20*1~
NM1*85*2*TEST PROVIDER*****XX*1999999999~
N3*1 TEST ST~
N4*TESTCITY*TX*75001~
HL*2*1*22*0~
SBR*P*18*GRP999******CI~
NM1*IL*1*GHOST*PATIENT****MI*MBR9999~
N3*2 TEST ST~
N4*TESTCITY*TX*75001~
DMG*D8*19900101*M~
CLM*BADCLAIM001*500.00***11:B:1*Y*A*Y*Y~
HI*ABK:E119~
LX*1~
SV1*HC:99213*150.00*UN*1***1~
DTP*472*D8*20240630~
SE*20*0001~
GE*1*1~
IEA*1*000000099~
"""


class TestNegativeCases:

    def test_malformed_claim_total_mismatch_is_detected(self):
        parsed = parse_837(MALFORMED_837)
        claim = parsed['claims'][0]
        assert not check_claim_total_matches_line_sum(claim)

    def test_orphaned_member_claim_is_detected(self, enrolled_member_ids):
        parsed = parse_837(MALFORMED_837)
        claim = parsed['claims'][0]
        orphans = find_claims_without_eligible_member([claim], enrolled_member_ids)
        assert orphans == ['BADCLAIM001']

    def test_overpayment_above_charge_is_detected(self):
        bad_service_payment = {
            'procedure_code': '99213',
            'charge': Decimal('150.00'),
            'paid': Decimal('600.00'),  # paid more than charged -- invalid
            'adjustments': [],
        }
        assert not check_service_line_paid_le_charge(bad_service_payment)

    def test_unbalanced_adjudication_arithmetic_is_detected(self):
        bad_remittance_claim = {
            'claim_id': 'BADCLAIM001',
            'charge_amount': Decimal('500.00'),
            'paid_amount': Decimal('600.00'),
            'service_payments': [
                {'procedure_code': '99213', 'charge': Decimal('150.00'),
                 'paid': Decimal('600.00'), 'adjustments': []},
            ],
        }
        assert not check_paid_plus_adjustment_equals_charge(bad_remittance_claim)

    def test_duplicate_claim_ids_are_detected(self):
        duplicated_claims = [{'claim_id': 'CLAIM00001'}, {'claim_id': 'CLAIM00001'}, {'claim_id': 'CLAIM00002'}]
        assert check_no_duplicate_claim_ids(duplicated_claims) == ['CLAIM00001']
