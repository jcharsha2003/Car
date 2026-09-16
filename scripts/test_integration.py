import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
from app.integration.mediator import Mediator

m = Mediator()

tests = [
    ('UP32AB1234', 'CASE 1 INSURED'),
    ('UP32CD5678', 'CASE 2 EXPIRED'),
    ('MH02EF9012', 'CASE 3 UNINSURED'),
    ('DL01GH3456', 'CASE 4 STOLEN'),
    ('KA03IJ7890', 'CASE 5 SCRAPPED'),
    ('TN05KL1122', 'CASE 6 CONFLICT'),
    ('GJ06MN3344', 'CASE 7 PARTIAL'),
    ('HR26PQ7788', 'CASE 9 SUSPICIOUS'),
]

for plate, label in tests:
    r = m.integrate(plate)
    status = r['overall_status']
    conflicts = r['conflicts']['conflict_count']
    data_avail = sum(1 for v in r['integration_metadata']['data_availability'].values() if v)
    print(f"{plate} ({label}): status={status}, conflicts={conflicts}, sources_with_data={data_avail}/5")

print()
print("Sub-query decomposition for UP32AB1234:")
r = m.integrate('UP32AB1234')
for src, q in r['integration_metadata']['sub_queries'].items():
    print(f"  {src}: local_key={q['local_key']} -> {q['query_template']}")

print()
print("Schema mapping (GAV):")
for src, local_key in r['integration_metadata']['schema_mapping_used'].items():
    print(f"  registration_number (global) -> {src}.{local_key} (local)")
