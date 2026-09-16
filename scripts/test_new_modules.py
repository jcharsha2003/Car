import sys
sys.path.insert(0, '.')

from app.integration.schema_matcher import compute_multisignal_similarity, compute_attribute_similarity, SchemaMatcher
from app.integration.source_registry import get_registry

print("=== Multi-signal matching test ===")
result = compute_multisignal_similarity(
    'plate_number', 'registration_id',
    instance_values1=['UP32AB1234', 'MH02EF9012', 'DL01GH3456'],
    instance_values2=['UP32AB1234', 'MH02EF9012', 'DL01GH3456']
)
print("plate_number vs registration_id:", result['score'], result['match_type'])
for sig, val in result['signals'].items():
    print(f"  {sig}: {val}")

result2 = compute_multisignal_similarity(
    'plate_number', 'vehicle_ref',
    instance_values1=['UP32AB1234', 'MH02EF9012'],
    instance_values2=['UP32AB1234', 'MH02EF9012']
)
print("plate_number vs vehicle_ref (with instances):", result2['score'], result2['match_type'])

ling_only = compute_attribute_similarity('plate_number', 'vehicle_ref')
print("plate_number vs vehicle_ref (linguistic only):", ling_only)

print()
print("=== Source registry test ===")
reg = get_registry()
health = reg.get_health_summary()
print("Total sources:", health['total_sources'])
for src in health['sources']:
    print("  Source:", src['name'], "| org:", src['organization'][:30])

print()
print("=== Ping all sources ===")
pings = reg.ping_all_sources()
for p in pings:
    print("  ", p['source'], "->", p['status'], p.get('response_ms', ''), "ms")

print()
print("=== Optimal query order (fastest first) ===")
print(reg.get_optimal_query_order())
