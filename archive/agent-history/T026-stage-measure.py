"""T026 phase 1: stage size and per-step stage write cost at the 8 h window."""
import sys, tempfile, time, statistics
from pathlib import Path
sys.path[:0] = ['C:/Users/assef/Bineyame/AssetOpsv1/host', 'C:/Users/assef/Bineyame/AssetOpsv1/host/tests']
from kobo import kobo_draft
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages


def measure(model_version, profile_version, name='kobo-mini-grid-prolonged'):
    run = kobo_draft(name, model_profile='mini-grid', model_profile_version=model_version,
                     timestep_minutes=5, start_time='2026-09-22T03:00:00Z',
                     end_time='2026-09-22T11:00:00Z',
                     publication_profile_version=profile_version)
    tmp = Path(tempfile.mkdtemp())
    stages = JsonSourceStages(tmp / 'stages')
    lab = HostLabExecution(artifacts=YamlExecutionArtifacts(tmp), stages=stages)
    stage_ms, step_ms, written = [], [], []
    original = lab._stage

    def timed(session):
        t = time.process_time()
        original(session)
        stage_ms.append(1000 * (time.process_time() - t))
        path = stages.path(session.run_id)
        written.append(path.stat().st_size if path.exists() else 0)
    lab._stage = timed
    lab.start(run)
    while True:
        at = lab._sessions[run.run_id].execution.boundaries_completed
        t = time.process_time()
        proj = lab.step(run, boundaries=1, from_boundary=at)
        step_ms.append(1000 * (time.process_time() - t))
        if proj.is_terminal:
            break
    last = stage_ms[-10:]
    st = lab.staged_envelopes(run).stage
    print(f"mini-grid v{model_version} / profile {profile_version}: steps={len(step_ms)} "
          f"envelopes={len(st.envelopes)} final_stage_bytes={written[-1]} "
          f"total_bytes_written={sum(written)} "
          f"stage_ms last10 mean={statistics.mean(last):.1f} max={max(last):.1f} "
          f"stage_ms p95(all)={sorted(stage_ms)[int(0.95*len(stage_ms))-1]:.1f} "
          f"step_ms last10 mean={statistics.mean(step_ms[-10:]):.1f} "
          f"step_ms p95={sorted(step_ms)[int(0.95*len(step_ms))-1]:.1f}")


for model_version, profile_version in [(2, 4), (3, 5)]:
    measure(model_version, profile_version)
