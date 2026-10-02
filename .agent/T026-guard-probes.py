"""Guard probes: each mutation must make its named test fail; files restored by git."""
import subprocess, sys
ROOT = 'C:/Users/assef/Bineyame/AssetOpsv1'
PY = ROOT + '/.venv/Scripts/python.exe'

PROBES = [
    ("R3 fullmatch", 'contracts/assetops_contracts/source_envelope.py',
     '_IDENTIFIER.fullmatch(', '_IDENTIFIER.match(',
     'simulator', 'tests/test_t026_schema2.py::TestParserCarries::test_a_trailing_newline_is_not_an_identifier_or_unit'),
    ("R3 unit fullmatch", 'contracts/assetops_contracts/source_envelope.py',
     '_UNIT.fullmatch(', '_UNIT.match(',
     'simulator', 'tests/test_t026_schema2.py::TestParserCarries::test_a_trailing_newline_is_not_an_identifier_or_unit'),
    ("R2 zero denominator", 'contracts/assetops_contracts/source_envelope.py',
     '    except ZeroDivisionError as error:\n        # Review R2', '    except KeyError as error:\n        # Review R2',
     'simulator', 'tests/test_t026_schema2.py::TestParserCarries::test_a_zero_denominator_is_a_refusal_not_an_exception'),
    ("R2 utf-8", 'host/source_stages.py',
     'except UnicodeDecodeError as error:', 'except KeyError as error:',
     'host', 'tests/test_t026_dispatch_evidence.py::test_a_corrupt_stage_reads_as_unreadable_not_an_error'),
    ("enum check before skip", 'simulator/assetops_simulator/gateway/publish.py',
     '        if entry is None:\n            continue\n        # T026 (backlog T025b C1)',
     '        if entry is None or item.outcome in NOT_PUBLISHED:\n            continue\n        # T026 (backlog T025b C1)',
     'simulator', 'tests/test_t026_schema2.py::TestTheEnumCheckPrecedesTheSkip'),
    ("member allowlist", 'contracts/assetops_contracts/source_envelope.py',
     '        and envelope.value not in entry.members', '        and envelope.value in ()',
     'simulator', 'tests/test_t026_schema2.py::TestSchemaTwoMeasurements::test_a_member_the_mapping_does_not_declare_is_refused'),
    ("delay applied", 'simulator/assetops_simulator/gateway/publish.py',
     'held = publication_delay_minutes(delays, device_id, signal_id, offset_minutes)',
     'held = 0',
     'simulator', 'tests/test_t026_schema2.py::TestDelay'),
    ("hold refusal", 'backend/assetops_backend/runs/service.py',
     '                if held > signal.cadence_minutes:', '                if held > 10_000:',
     'host', 'tests/test_t026_dispatch_evidence.py::test_a_hold_that_would_batch_publications_is_refused_at_setup'),
    ("record gap", 'simulator/assetops_simulator/observation/records.py',
     '            return "SUPPRESSED_BY_GAP", gap.event_id', '            return "REPORTED", None',
     'host', 'tests/test_t026_dispatch_evidence.py::test_a_missing_override_record_is_none_observed_not_no_override'),
    ("profile-by-mapping", 'simulator/assetops_simulator/gateway/mappings.py',
     '    ("simulator-lab-publication", 5): SIMULATOR_LAB_DISPATCH_MAPPINGS,', '',
     'host', 'tests/test_t026_dispatch_evidence.py::test_earlier_profiles_keep_the_fuel_only_schema_1_mapping'),
]

results = []
for name, path, old, new, suite, test in PROBES:
    full = f'{ROOT}/{path}'
    text = open(full, encoding='utf-8').read()
    assert old in text, name
    open(full, 'w', encoding='utf-8', newline='\n').write(text.replace(old, new) if old == '_UNIT.fullmatch(' else text.replace(old, new, 1))
    try:
        run = subprocess.run([PY, '-m', 'pytest', '-q', '-x', '-p', 'no:cacheprovider', test],
                             cwd=f'{ROOT}/{suite}', capture_output=True, text=True)
        caught = run.returncode != 0
    finally:
        subprocess.run(['git', 'checkout', '--', path], cwd=ROOT, check=True)
    results.append((name, 'CAUGHT' if caught else 'MISSED'))
for name, verdict in results:
    print(f'{verdict}: {name}')
print(subprocess.run(['git', 'status', '--short'], cwd=ROOT, capture_output=True, text=True).stdout)
