"""
Generate the shared member/provider/reference roster used by all three
EDI generators (834 enrollment, 837 claims, 835 remittance), so the
generated files are internally consistent and reconciliation tests have
something real to check.

Run standalone to write data/raw/_members_seed.json, or import
generate_members()/generate_providers()/REFERENCE_DATA directly.
"""

import json
import os
import random
from datetime import date, timedelta

from faker import Faker

SEED = 42
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_JSON = os.path.join(ROOT, 'data', 'raw', '_members_seed.json')

GROUP_NUMBERS = ['GRP100', 'GRP200']
PLAN_CODES = ['PPO500', 'HMO250', 'EPO100']

# 8-10 CPT-style procedure codes with realistic charge ranges
CPT_CODES = [
    {'code': '99213', 'description': 'Office visit, established patient', 'charge_min': 125, 'charge_max': 175},
    {'code': '99214', 'description': 'Office visit, detailed', 'charge_min': 175, 'charge_max': 225},
    {'code': '80053', 'description': 'Comprehensive metabolic panel', 'charge_min': 180, 'charge_max': 220},
    {'code': '85025', 'description': 'Complete blood count', 'charge_min': 60, 'charge_max': 90},
    {'code': '71046', 'description': 'Chest X-ray, 2 views', 'charge_min': 90, 'charge_max': 140},
    {'code': '93000', 'description': 'Electrocardiogram', 'charge_min': 75, 'charge_max': 110},
    {'code': '90791', 'description': 'Psychiatric diagnostic evaluation', 'charge_min': 200, 'charge_max': 280},
    {'code': '36415', 'description': 'Routine venipuncture', 'charge_min': 15, 'charge_max': 30},
    {'code': '12001', 'description': 'Simple wound repair', 'charge_min': 150, 'charge_max': 220},
]

# 5-6 ICD-10 diagnosis codes
ICD10_CODES = ['E119', 'I10', 'J0190', 'M545', 'K219', 'F411']


def generate_providers(n=4, seed=SEED):
    """Return list of provider dicts: {npi, name, address, city, state, zip}."""
    fake = Faker()
    fake.seed_instance(seed)
    providers = []
    for i in range(n):
        providers.append({
            'npi': f'1{random.Random(seed + i).randint(100000000, 999999999) % 1000000000:09d}',
            'name': fake.company() + ' Medical Group',
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip': fake.zipcode()[:5],
        })
    return providers


def generate_members(n=8, seed=SEED):
    """
    Return list of member dicts:
    {member_id, subscriber_id, first_name, last_name, dob, gender,
     address, city, state, zip, group_number, plan_code,
     coverage_effective_date, maintenance_type, relationship_code}
    """
    fake = Faker()
    fake.seed_instance(seed)
    rng = random.Random(seed)

    members = []
    for i in range(n):
        gender = rng.choice(['M', 'F'])
        first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=75)

        # Most members are new enrollees (030); inject 1 termination (024) and 1 change (001)
        if i == n - 2:
            maintenance_type = '024'  # termination
        elif i == n - 1:
            maintenance_type = '001'  # change
        else:
            maintenance_type = '030'  # addition

        members.append({
            'member_id': f'MBR{1000 + i}',
            'subscriber_id': f'MBR{1000 + i}',
            'first_name': first_name.upper(),
            'last_name': fake.last_name().upper(),
            'dob': dob.strftime('%Y%m%d'),
            'gender': gender,
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip': fake.zipcode()[:5],
            'group_number': GROUP_NUMBERS[i % len(GROUP_NUMBERS)],
            'plan_code': PLAN_CODES[i % len(PLAN_CODES)],
            'coverage_effective_date': date(2024, 1, 1).strftime('%Y%m%d'),
            'maintenance_type': maintenance_type,
            'relationship_code': '18',  # self
        })
    return members


def build_seed_data(n_members=8, n_providers=4, seed=SEED):
    return {
        'members': generate_members(n_members, seed),
        'providers': generate_providers(n_providers, seed),
        'cpt_codes': CPT_CODES,
        'icd10_codes': ICD10_CODES,
    }


def main():
    data = build_seed_data()
    os.makedirs(os.path.dirname(SEED_JSON), exist_ok=True)
    with open(SEED_JSON, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Wrote {len(data["members"])} members, {len(data["providers"])} providers to {SEED_JSON}')


if __name__ == '__main__':
    main()
