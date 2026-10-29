# PERF-01 site-build profiles (py-spy 0.4.0, 100 Hz, --threads --subprocesses)

- on-CPU run: `profile-20261029-100427-2933b0`; wall run (idle included): `profile-20261029-095448-856d4a`

## cold

Test thread wall (test phases only): 22.1 s. On-CPU seconds: test thread 2.6, in-process app 3.4, gateway child 1.7, other child 0.1, collection / start-up 7.3

Test thread wall by activity:

| activity | s | share |
| --- | ---: | ---: |
| gateway IPC (waiting on / talking to the gateway child) | 10.9 | 49.3% |
| YAML parsing | 3.2 | 14.4% |
| database driver (psycopg: round trip + Python) | 3.2 | 14.3% |
| AssetOps: gateway_process.py | 2.5 | 11.2% |
| imports | 1.1 | 5.2% |
| SQLAlchemy (Python) | 0.5 | 2.2% |
| migrations (alembic) | 0.3 | 1.4% |
| HTTP / ASGI / socket stack | 0.1 | 0.6% |
| JSON | 0.1 | 0.5% |
| AssetOps: assetops_backend/sites | 0.1 | 0.2% |
| AssetOps: assetops_backend/evidence | 0.1 | 0.2% |
| AssetOps: assetops_simulator/packs | 0.0 | 0.1% |
| AssetOps: assetops_backend/scenarios | 0.0 | 0.1% |
| AssetOps: assetops_contracts/ingestion_batch_v2.py | 0.0 | 0.0% |
| AssetOps: lab_execution.py | 0.0 | 0.0% |
| AssetOps: assetops_backend/runs | 0.0 | 0.0% |

On-CPU in test thread (2.6 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| YAML parsing | 1.2 | 47.1% |
| database driver (psycopg: round trip + Python) | 0.6 | 22.8% |
| imports | 0.3 | 10.8% |
| SQLAlchemy (Python) | 0.2 | 7.3% |
| AssetOps: assetops_backend/evidence | 0.1 | 3.9% |
| JSON | 0.0 | 1.5% |
| AssetOps: assetops_backend/scenarios | 0.0 | 1.5% |
| migrations (alembic) | 0.0 | 1.5% |
| gateway IPC (waiting on / talking to the gateway child) | 0.0 | 1.2% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.8% |
| HTTP / ASGI / socket stack | 0.0 | 0.4% |
| AssetOps: lab_execution.py | 0.0 | 0.4% |
| AssetOps: assetops_backend/analytics | 0.0 | 0.4% |
| AssetOps: assetops_simulator/packs | 0.0 | 0.4% |

Top AssetOps functions on-CPU in test thread (inclusive):

| s | function |
| ---: | --- |
| 1.3 | `start (lab_execution.py)` |
| 1.3 | `_start_cold (lab_execution.py)` |
| 1.2 | `get_scenario (assetops_backend/scenarios/service.py)` |
| 1.2 | `get_scenario (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 1.2 | `list_scenarios (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 1.2 | `list_scenarios (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 1.2 | `_read_shipped (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 0.6 | `read_scenario_record (assetops_backend/scenarios/adapters/yaml_scenario_documents.py)` |
| 0.4 | `release_registered (lab_execution.py)` |
| 0.4 | `publish (assetops_backend/runs/registered_release.py)` |
| 0.4 | `register_run (assetops_backend/evidence/publication.py)` |
| 0.3 | `<genexpr> (assetops_backend/evidence/publication.py)` |
| 0.3 | `register_publication (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.1 | `run_pending (assetops_backend/analytics/assessment_worker.py)` |
| 0.1 | `run_once (assetops_backend/analytics/assessment_worker.py)` |
| 0.1 | `_project (assetops_backend/analytics/assessment_worker.py)` |

On-CPU in in-process app (3.4 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| database driver (psycopg: round trip + Python) | 1.4 | 43.2% |
| imports | 0.7 | 20.2% |
| HTTP / ASGI / socket stack | 0.5 | 15.2% |
| SQLAlchemy (Python) | 0.4 | 11.0% |
| other | 0.1 | 3.6% |
| AssetOps: assetops_backend/evidence | 0.1 | 2.7% |
| HTTP / ASGI stack (TestClient) | 0.1 | 2.4% |
| JSON | 0.0 | 1.2% |
| AssetOps: assetops_backend/gateway_api.py | 0.0 | 0.3% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.3% |

Top AssetOps functions on-CPU in in-process app (inclusive):

| s | function |
| ---: | --- |
| 1.8 | `submit (assetops_backend/evidence/ledger_service.py)` |
| 1.7 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 1.4 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.8 | `_drive (assetops_backend/evidence/ledger_service.py)` |
| 0.8 | `decide_chunk (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `open_batch (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `post_batch (assetops_backend/evidence_api.py)` |
| 0.3 | `post_batch_v2 (assetops_backend/evidence_api.py)` |
| 0.2 | `_check_claims (assetops_backend/evidence/ledger_service.py)` |
| 0.2 | `registered_scope (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |
| 0.2 | `_persist (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `receipt (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `authenticate (assetops_backend/evidence_api.py)` |
| 0.2 | `resolve (assetops_backend/evidence/gateway_access.py)` |
| 0.2 | `credential (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.2 | `_run (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.2 | `_coalesce_job (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |

On-CPU in gateway child (1.7 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| imports | 0.8 | 46.2% |
| HTTP / ASGI / socket stack | 0.5 | 26.9% |
| AssetOps: assetops_gateway/service.py | 0.2 | 14.6% |
| AssetOps: assetops_contracts/ingestion_receipt_v2.py | 0.0 | 2.3% |
| AssetOps: assetops_gateway/snapshot.py | 0.0 | 1.8% |
| JSON | 0.0 | 1.2% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 0.0 | 1.2% |
| regex | 0.0 | 1.2% |
| gateway IPC (waiting on / talking to the gateway child) | 0.0 | 1.2% |
| AssetOps: assetops_contracts/observation.py | 0.0 | 0.6% |
| AssetOps: assetops_contracts/source_envelope.py | 0.0 | 0.6% |
| AssetOps: assetops_contracts/world_inputs.py | 0.0 | 0.6% |
| AssetOps: assetops_gateway/uploader.py | 0.0 | 0.6% |
| other | 0.0 | 0.6% |

Top AssetOps functions on-CPU in gateway child (inclusive):

| s | function |
| ---: | --- |
| 0.8 | `_serve (assetops_gateway/ipc.py)` |
| 0.8 | `handle (assetops_gateway/ipc.py)` |
| 0.7 | `deliver (assetops_gateway/uploader.py)` |
| 0.7 | `_deliver (assetops_gateway/ipc.py)` |
| 0.7 | `upload_pass (assetops_gateway/uploader.py)` |
| 0.7 | `_send_batch (assetops_gateway/uploader.py)` |
| 0.5 | `<module> (assetops_gateway/__main__.py)` |
| 0.5 | `_post (assetops_gateway/uploader.py)` |
| 0.3 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |
| 0.3 | `_call (assetops_gateway/uploader.py)` |
| 0.2 | `_tls_connection (assetops_gateway/uploader.py)` |
| 0.2 | `record_receipt (assetops_gateway/service.py)` |
| 0.2 | `__exit__ (assetops_gateway/service.py)` |
| 0.2 | `<module> (assetops_gateway/ipc.py)` |
| 0.1 | `<module> (assetops_gateway/uploader.py)` |
| 0.1 | `begin_attempt (assetops_gateway/service.py)` |
| 0.1 | `<module> (assetops_contracts/gateway_diagnostics.py)` |
| 0.1 | `_dispatch (assetops_gateway/ipc.py)` |

## ev

Test thread wall (test phases only): 21.3 s. On-CPU seconds: test thread 4.5, in-process app 3.4, gateway child 2.3, other child 0.1, collection / start-up 4.2

Test thread wall by activity:

| activity | s | share |
| --- | ---: | ---: |
| gateway IPC (waiting on / talking to the gateway child) | 12.3 | 57.8% |
| YAML parsing | 3.1 | 14.7% |
| database driver (psycopg: round trip + Python) | 2.4 | 11.1% |
| AssetOps: gateway_process.py | 1.6 | 7.4% |
| imports | 0.6 | 2.9% |
| SQLAlchemy (Python) | 0.4 | 1.9% |
| waiting on another thread (in-process app) | 0.3 | 1.5% |
| migrations (alembic) | 0.1 | 0.6% |
| AssetOps: assetops_backend/scenarios | 0.1 | 0.4% |
| HTTP / ASGI / socket stack | 0.1 | 0.3% |
| AssetOps: assetops_backend/evidence | 0.1 | 0.3% |
| AssetOps: assetops_backend/sites | 0.1 | 0.2% |
| AssetOps: assetops_simulator/packs | 0.0 | 0.1% |
| JSON | 0.0 | 0.1% |
| AssetOps: lab_execution.py | 0.0 | 0.1% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.1% |

On-CPU in test thread (4.5 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| YAML parsing | 2.5 | 55.4% |
| database driver (psycopg: round trip + Python) | 0.6 | 12.5% |
| SQLAlchemy (Python) | 0.3 | 7.7% |
| imports | 0.2 | 5.5% |
| gateway IPC (waiting on / talking to the gateway child) | 0.2 | 4.2% |
| JSON | 0.1 | 2.4% |
| migrations (alembic) | 0.1 | 2.0% |
| AssetOps: assetops_backend/scenarios | 0.1 | 2.0% |
| AssetOps: assetops_backend/evidence | 0.1 | 1.5% |
| AssetOps: lab_execution.py | 0.0 | 0.9% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.9% |
| HTTP / ASGI / socket stack | 0.0 | 0.7% |
| AssetOps: assetops_simulator/packs | 0.0 | 0.7% |
| AssetOps: assetops_simulator/observation | 0.0 | 0.4% |

Top AssetOps functions on-CPU in test thread (inclusive):

| s | function |
| ---: | --- |
| 2.4 | `list_scenarios (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 2.4 | `_read_shipped (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 1.8 | `start (lab_execution.py)` |
| 1.8 | `_start_ev (lab_execution.py)` |
| 1.2 | `get_scenario (assetops_backend/scenarios/service.py)` |
| 1.2 | `get_scenario (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 1.2 | `list_scenarios (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 1.1 | `read_scenario_record (assetops_backend/scenarios/adapters/yaml_scenario_documents.py)` |
| 0.9 | `release_registered (lab_execution.py)` |
| 0.8 | `publish (assetops_backend/runs/registered_release.py)` |
| 0.8 | `register_run (assetops_backend/evidence/publication.py)` |
| 0.7 | `<genexpr> (assetops_backend/evidence/publication.py)` |
| 0.7 | `register_publication (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.7 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.6 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `_stage_registered_virtual_ev (lab_execution.py)` |
| 0.3 | `_stage_registered_v2_reports (lab_execution.py)` |
| 0.3 | `_release (lab_execution.py)` |

On-CPU in in-process app (3.4 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| database driver (psycopg: round trip + Python) | 1.7 | 49.9% |
| HTTP / ASGI / socket stack | 0.6 | 17.0% |
| imports | 0.6 | 16.7% |
| SQLAlchemy (Python) | 0.3 | 9.6% |
| HTTP / ASGI stack (TestClient) | 0.1 | 1.8% |
| other | 0.0 | 1.2% |
| waiting on another thread (in-process app) | 0.0 | 1.2% |
| JSON | 0.0 | 0.9% |
| AssetOps: assetops_backend/evidence | 0.0 | 0.9% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 0.0 | 0.3% |
| regex | 0.0 | 0.3% |
| AssetOps: assetops_backend/gateway_api.py | 0.0 | 0.3% |

Top AssetOps functions on-CPU in in-process app (inclusive):

| s | function |
| ---: | --- |
| 1.9 | `submit (assetops_backend/evidence/ledger_service.py)` |
| 1.8 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 1.5 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.5 | `_drive (assetops_backend/evidence/ledger_service.py)` |
| 0.5 | `decide_chunk (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.5 | `open_batch (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `_check_claims (assetops_backend/evidence/ledger_service.py)` |
| 0.3 | `registered_scope (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `binding_set (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `receipt (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `post_batch (assetops_backend/evidence_api.py)` |
| 0.2 | `post_batch_v2 (assetops_backend/evidence_api.py)` |
| 0.2 | `authenticate (assetops_backend/evidence_api.py)` |
| 0.2 | `resolve (assetops_backend/evidence/gateway_access.py)` |
| 0.2 | `credential (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.2 | `_run (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.2 | `_persist (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.2 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |

On-CPU in gateway child (2.3 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| HTTP / ASGI / socket stack | 0.7 | 30.7% |
| imports | 0.7 | 28.5% |
| AssetOps: assetops_gateway/service.py | 0.4 | 17.1% |
| gateway IPC (waiting on / talking to the gateway child) | 0.2 | 9.6% |
| JSON | 0.1 | 5.7% |
| datetime / decimal | 0.1 | 2.2% |
| AssetOps: assetops_contracts/ingestion_receipt_v2.py | 0.0 | 0.9% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 0.0 | 0.9% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.9% |
| other | 0.0 | 0.9% |
| AssetOps: assetops_contracts/source_envelope.py | 0.0 | 0.4% |
| AssetOps: assetops_gateway/snapshot.py | 0.0 | 0.4% |
| AssetOps: assetops_gateway/ledger.py | 0.0 | 0.4% |
| regex | 0.0 | 0.4% |

Top AssetOps functions on-CPU in gateway child (inclusive):

| s | function |
| ---: | --- |
| 1.5 | `_serve (assetops_gateway/ipc.py)` |
| 1.3 | `handle (assetops_gateway/ipc.py)` |
| 1.0 | `_deliver (assetops_gateway/ipc.py)` |
| 1.0 | `deliver (assetops_gateway/uploader.py)` |
| 0.9 | `upload_pass (assetops_gateway/uploader.py)` |
| 0.9 | `_send_batch (assetops_gateway/uploader.py)` |
| 0.7 | `_post (assetops_gateway/uploader.py)` |
| 0.6 | `<module> (assetops_gateway/__main__.py)` |
| 0.4 | `_tls_connection (assetops_gateway/uploader.py)` |
| 0.3 | `_dispatch (assetops_gateway/ipc.py)` |
| 0.3 | `__exit__ (assetops_gateway/service.py)` |
| 0.3 | `admit_texts (assetops_gateway/service.py)` |
| 0.3 | `_call (assetops_gateway/uploader.py)` |
| 0.2 | `<module> (assetops_gateway/ipc.py)` |
| 0.2 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |
| 0.1 | `_admit_in (assetops_gateway/service.py)` |
| 0.1 | `record_receipt (assetops_gateway/service.py)` |
| 0.1 | `begin_attempt (assetops_gateway/service.py)` |

## mini

Test thread wall (test phases only): 45.3 s. On-CPU seconds: test thread 16.8, in-process app 0.4, gateway child 0.0, other child 0.1, collection / start-up 6.9

Test thread wall by activity:

| activity | s | share |
| --- | ---: | ---: |
| database driver (psycopg: round trip + Python) | 27.9 | 61.4% |
| SQLAlchemy (Python) | 7.6 | 16.8% |
| imports | 2.6 | 5.6% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 1.6 | 3.6% |
| JSON | 1.5 | 3.3% |
| AssetOps: assetops_backend/evidence | 1.2 | 2.6% |
| datetime / decimal | 1.0 | 2.3% |
| migrations (alembic) | 0.9 | 1.9% |
| AssetOps: assetops_backend/mini_depth | 0.7 | 1.5% |
| AssetOps: assetops_backend/sites | 0.1 | 0.2% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.1 | 0.2% |
| YAML parsing | 0.1 | 0.2% |
| HTTP / ASGI / socket stack | 0.1 | 0.1% |
| AssetOps: assetops_contracts/source_envelope.py | 0.1 | 0.1% |
| AssetOps: assetops_contracts/ingestion_receipt_v2.py | 0.0 | 0.1% |
| AssetOps: assetops_contracts/ingestion_batch_v2.py | 0.0 | 0.0% |

On-CPU in test thread (16.8 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| database driver (psycopg: round trip + Python) | 6.9 | 41.2% |
| SQLAlchemy (Python) | 5.1 | 30.5% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 1.2 | 6.9% |
| JSON | 0.8 | 5.1% |
| AssetOps: assetops_backend/evidence | 0.7 | 4.3% |
| datetime / decimal | 0.6 | 3.3% |
| AssetOps: assetops_backend/mini_depth | 0.6 | 3.3% |
| imports | 0.5 | 3.2% |
| AssetOps: assetops_contracts/source_envelope.py | 0.1 | 0.8% |
| migrations (alembic) | 0.1 | 0.6% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.1 | 0.5% |
| YAML parsing | 0.1 | 0.3% |
| AssetOps: assetops_contracts/ingestion_receipt_v2.py | 0.0 | 0.1% |
| AssetOps: assetops_contracts/ingestion_batch_v2.py | 0.0 | 0.1% |

Top AssetOps functions on-CPU in test thread (inclusive):

| s | function |
| ---: | --- |
| 10.1 | `submit (assetops_backend/evidence/ledger_service.py)` |
| 9.6 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 9.4 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 9.2 | `_drive (assetops_backend/evidence/ledger_service.py)` |
| 9.2 | `decide_chunk (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 5.6 | `_persist (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 5.1 | `reconcile (assetops_backend/mini_depth/worker.py)` |
| 4.8 | `append_selection (assetops_backend/mini_depth/store.py)` |
| 4.7 | `_run (assetops_backend/mini_depth/store.py)` |
| 4.7 | `work (assetops_backend/mini_depth/store.py)` |
| 2.2 | `parse_canonical_envelope_v3_text (assetops_contracts/source_envelope_v3.py)` |
| 1.7 | `<lambda> (assetops_backend/evidence/ledger_service.py)` |
| 1.7 | `decide (assetops_backend/evidence/ledger.py)` |
| 1.6 | `parse_source_envelope_v3 (assetops_contracts/source_envelope_v3.py)` |
| 1.5 | `parse_canonical_source_envelope_text (assetops_contracts/source_envelope_v4.py)` |
| 1.2 | `__post_init__ (assetops_contracts/source_envelope_v3.py)` |
| 1.2 | `_validate (assetops_contracts/source_envelope_v3.py)` |
| 1.0 | `seal_batch_v2 (assetops_contracts/ingestion_batch_v2.py)` |

On-CPU in in-process app (0.4 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| imports | 0.4 | 97.5% |
| regex | 0.0 | 2.5% |

Top AssetOps functions on-CPU in in-process app (inclusive):

| s | function |
| ---: | --- |
| 0.1 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |

## portfolio

Test thread wall (test phases only): 9.9 s. On-CPU seconds: test thread 7.8, in-process app 8.6, gateway child 7.3, other child 0.1, collection / start-up 8.1

Test thread wall by activity:

| activity | s | share |
| --- | ---: | ---: |
| gateway IPC (waiting on / talking to the gateway child) | 2.5 | 25.3% |
| database driver (psycopg: round trip + Python) | 2.3 | 22.9% |
| YAML parsing | 1.8 | 18.2% |
| AssetOps: gateway_process.py | 1.5 | 15.3% |
| imports | 1.0 | 10.5% |
| SQLAlchemy (Python) | 0.3 | 3.1% |
| migrations (alembic) | 0.2 | 2.4% |
| JSON | 0.0 | 0.4% |
| AssetOps: assetops_backend/sites | 0.0 | 0.4% |
| AssetOps: assetops_simulator/packs | 0.0 | 0.3% |
| AssetOps: assetops_backend/scenarios | 0.0 | 0.2% |
| HTTP / ASGI / socket stack | 0.0 | 0.2% |
| AssetOps: assetops_backend/evidence | 0.0 | 0.1% |
| AssetOps: assetops_backend/document_bounds.py | 0.0 | 0.1% |
| hashing | 0.0 | 0.1% |
| AssetOps: lab_execution.py | 0.0 | 0.1% |

On-CPU in test thread (7.8 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| YAML parsing | 4.9 | 62.7% |
| database driver (psycopg: round trip + Python) | 1.0 | 12.9% |
| SQLAlchemy (Python) | 0.4 | 5.7% |
| imports | 0.3 | 4.5% |
| gateway IPC (waiting on / talking to the gateway child) | 0.3 | 4.2% |
| JSON | 0.2 | 2.4% |
| migrations (alembic) | 0.1 | 1.0% |
| AssetOps: lab_execution.py | 0.1 | 0.8% |
| AssetOps: assetops_backend/evidence | 0.1 | 0.8% |
| AssetOps: assetops_simulator/packs | 0.1 | 0.8% |
| AssetOps: assetops_backend/scenarios | 0.1 | 0.6% |
| AssetOps: assetops_backend/sites | 0.0 | 0.5% |
| AssetOps: assetops_backend/analytics | 0.0 | 0.4% |
| hashing | 0.0 | 0.4% |

Top AssetOps functions on-CPU in test thread (inclusive):

| s | function |
| ---: | --- |
| 4.5 | `list_scenarios (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 4.5 | `_read_shipped (assetops_backend/scenarios/adapters/yaml_shipped_scenario_store.py)` |
| 3.9 | `start (lab_execution.py)` |
| 3.2 | `get_scenario (assetops_backend/scenarios/service.py)` |
| 3.2 | `get_scenario (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 3.2 | `list_scenarios (assetops_backend/scenarios/adapters/composite_scenario_repository.py)` |
| 2.2 | `read_scenario_record (assetops_backend/scenarios/adapters/yaml_scenario_documents.py)` |
| 2.0 | `_start_ev (lab_execution.py)` |
| 1.8 | `_start_cold (lab_execution.py)` |
| 1.2 | `release_registered (lab_execution.py)` |
| 0.9 | `publish (assetops_backend/runs/registered_release.py)` |
| 0.9 | `register_run (assetops_backend/evidence/publication.py)` |
| 0.8 | `<genexpr> (assetops_backend/evidence/publication.py)` |
| 0.8 | `register_publication (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.8 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.6 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.5 | `call (assetops_gateway/ipc.py)` |
| 0.4 | `_stage_registered_v2_reports (lab_execution.py)` |

On-CPU in in-process app (8.6 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| database driver (psycopg: round trip + Python) | 4.5 | 52.1% |
| HTTP / ASGI / socket stack | 1.7 | 19.7% |
| SQLAlchemy (Python) | 1.2 | 13.8% |
| imports | 0.4 | 4.9% |
| AssetOps: assetops_backend/evidence | 0.3 | 3.1% |
| other | 0.2 | 1.9% |
| HTTP / ASGI stack (TestClient) | 0.1 | 1.5% |
| waiting on another thread (in-process app) | 0.1 | 0.8% |
| JSON | 0.0 | 0.5% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.0 | 0.5% |
| datetime / decimal | 0.0 | 0.2% |
| AssetOps: assetops_backend/evidence_api.py | 0.0 | 0.2% |
| regex | 0.0 | 0.2% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 0.0 | 0.2% |

Top AssetOps functions on-CPU in in-process app (inclusive):

| s | function |
| ---: | --- |
| 5.6 | `submit (assetops_backend/evidence/ledger_service.py)` |
| 5.5 | `_run (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 4.7 | `work (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 2.3 | `_drive (assetops_backend/evidence/ledger_service.py)` |
| 2.3 | `decide_chunk (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 1.2 | `open_batch (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.9 | `_persist (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.6 | `post_batch (assetops_backend/evidence_api.py)` |
| 0.6 | `post_batch_v2 (assetops_backend/evidence_api.py)` |
| 0.6 | `binding_set (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.6 | `receipt (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.5 | `authenticate (assetops_backend/evidence_api.py)` |
| 0.5 | `resolve (assetops_backend/evidence/gateway_access.py)` |
| 0.5 | `credential (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.5 | `_run (assetops_backend/evidence/adapters/postgres_gateway_access.py)` |
| 0.5 | `_check_claims (assetops_backend/evidence/ledger_service.py)` |
| 0.5 | `registered_scope (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |
| 0.3 | `find_batch (assetops_backend/evidence/adapters/postgres_evidence_ledger.py)` |

On-CPU in gateway child (7.3 s) by leaf:

| category | s | share |
| --- | ---: | ---: |
| imports | 2.4 | 32.9% |
| HTTP / ASGI / socket stack | 2.2 | 30.4% |
| AssetOps: assetops_gateway/service.py | 1.5 | 21.1% |
| JSON | 0.3 | 3.7% |
| gateway IPC (waiting on / talking to the gateway child) | 0.3 | 3.6% |
| AssetOps: assetops_contracts/source_envelope_v4.py | 0.1 | 1.4% |
| AssetOps: assetops_gateway/ledger.py | 0.1 | 1.0% |
| AssetOps: assetops_contracts/source_envelope_v3.py | 0.1 | 0.8% |
| AssetOps: assetops_contracts/gateway_report.py | 0.1 | 0.7% |
| AssetOps: assetops_contracts/ingestion_receipt_v2.py | 0.1 | 0.7% |
| AssetOps: assetops_gateway/uploader.py | 0.0 | 0.5% |
| AssetOps: assetops_gateway/snapshot.py | 0.0 | 0.5% |
| AssetOps: assetops_contracts/control.py | 0.0 | 0.5% |
| datetime / decimal | 0.0 | 0.5% |

Top AssetOps functions on-CPU in gateway child (inclusive):

| s | function |
| ---: | --- |
| 4.3 | `_serve (assetops_gateway/ipc.py)` |
| 4.1 | `handle (assetops_gateway/ipc.py)` |
| 3.2 | `deliver (assetops_gateway/uploader.py)` |
| 3.1 | `_deliver (assetops_gateway/ipc.py)` |
| 3.1 | `upload_pass (assetops_gateway/uploader.py)` |
| 3.1 | `_send_batch (assetops_gateway/uploader.py)` |
| 2.4 | `<module> (assetops_gateway/__main__.py)` |
| 2.1 | `_post (assetops_gateway/uploader.py)` |
| 1.1 | `_tls_connection (assetops_gateway/uploader.py)` |
| 1.1 | `_call (assetops_gateway/uploader.py)` |
| 1.0 | `__exit__ (assetops_gateway/service.py)` |
| 0.9 | `_dispatch (assetops_gateway/ipc.py)` |
| 0.7 | `<module> (assetops_gateway/ipc.py)` |
| 0.7 | `record_receipt (assetops_gateway/service.py)` |
| 0.6 | `admit_texts (assetops_gateway/service.py)` |
| 0.5 | `_admit_in (assetops_gateway/service.py)` |
| 0.4 | `<module> (__editable___assetops_backend_0_0_0_finder.py)` |
| 0.4 | `<module> (assetops_contracts/gateway_diagnostics.py)` |

