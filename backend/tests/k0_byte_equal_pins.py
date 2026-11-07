"""DIESEL-1 K0 (ruling DIESEL-1-R3f Q10): byte-equal pins for runs with no operational actions.

Taken on the unedited tree (main `1fc354bee` + the R3f ruling commit) and committed as the branch's first commit,
before any production edit, so git history shows they predate K0. `host/tests/test_k0_kisiwa_actions.py` rebuilds
every fixture and asserts all three digests (test 1, stop S1).

Recipe for each row, per §9f.1 Q10:
- the Draft is built by the existing no-DB fixture named in its setup tuple: the Kobo draft
  (`host/tests/kobo.py` `kobo_draft`), the Cold lab draft (`test_w202_cold_run_identity` `cold_service` +
  `cold_request`), the EV lab draft (`test_w205b_ev_scenarios` `ev_service` + `ev_request`), and one Draft per
  shipped timeline scenario (every `config/scenarios/*.yaml` that is not a cold or EV document) through
  `kobo_draft(name, model_profile=..., model_profile_version=..., start_time=..., end_time=...,
  timestep_minutes=...)`;
- `run_id` and `created_at` are random or clocked per process, so they are replaced by `FIXED_RUN_ID` and
  `FIXED_CREATED_AT` (`dataclasses.replace`) before hashing; nothing else is removed;
- the EV fixture's registered selection carries `uuid4` mapping ids from an in-memory install, which differ per
  process (DIESEL-1-R3i deviation 1: the seeding fixes only identifiers K0 does not produce, and has been here
  since the first commit, so the pin still covers every byte K0 could move). It is therefore built fresh (not from the module cache) under F0's `seeded_uuid4()`
  (`tools/probe_kisiwa_fuel.py`), which makes it reproducible across processes;
- digests: (a) `RENDER` = sha256 of `json.dumps(render_run_document(run), sort_keys=True, separators=(",", ":"),
  ensure_ascii=False, default=str)`; (b) `RUN_IDENTITY` = `run_identity_sha256(run)`; `CAUSES` = sha256 of the same
  dump of the rendered `deterministic_identity["causes"]`; (c) `TRAJECTORY` = `frozen_inputs_identity` over
  `frozen_world_inputs(run)` with the kernel's version and numeric policy, for a READY Draft; `None` for a BLOCKED
  Draft (the host refuses to build world inputs for it);
- `N_CAUSES` and `N_CONDITIONS` count the rendered causes and reporting-path conditions, so the set the pins cover
  is visibly non-empty.

Every value was reproduced identically in two fresh processes before it was written here.
"""

from __future__ import annotations

FIXED_RUN_ID = "run-00000000000000000000000000000000"
FIXED_CREATED_AT = "2026-01-01T00:00:00Z"

DAY = ("daytime-mini-grid", None, "2026-09-22T03:00:00Z", "2026-09-22T15:00:00Z", 15)

#: key -> (setup, (RENDER, RUN_IDENTITY, CAUSES, TRAJECTORY, N_CAUSES, N_CONDITIONS)).
#: setup is `(scenario, profile, version, start, end, timestep)` for a `kobo_draft`, or `(scenario,)` for the
#: Cold and EV lab fixtures, which fix their own request.
PINS: dict[str, tuple[tuple, tuple]] = {
    "kobo": (
        ("kobo-daytime", *DAY),
        ("2b0eb82c45af735f2c907f75e94a9494190564247f9e8060ea90cd376d6b6073",
         "bdb006830dfba539c4193fd6f6662db6583fe6d6612a15bc06f15b0dab563720",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "295bcb34edc52ad25721929f0a6be2b3eee0085e78e0f183f082158928a8551a", 0, 0)),
    "cold": (
        ("cold-normal",),
        ("90e0d12f9d365560bdfa984605261d4d64dab1493a23d7ad778c4ac490663ab4",
         "735645f093aae39026623d178590d8d2113b80b0b0d6d9619fd0b61e4d240687",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "8a408f60c45cf063e4a177d38f39b0a17a63c726321e98cd74c2cdccc82f3feb", 0, 0)),
    "ev": (
        ("ev-complete",),
        ("d09f2579481ce968156f27552bebaeea93a2effdbfb95f51078a87b596daded8",
         "4856c51988607d433a7e44653239ac6e2ef0bc8baf9630221cd3dcd61d24596b",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "80c76ea2eec464ac2149add1a3cc4e0b516f2b72063d2dc55889bc15081e8199", 0, 0)),
    "scenario:fuel-loss-event": (
        ("fuel-loss-event", "minimal-fuel-tank", None, "2026-09-22T00:00:00Z", "2026-09-24T00:00:00Z", 15),
        ("e628129ad283dedb398d380f94ebad323889dc2254c92510e8bf510acda8f735",
         "6aa149eadb8128ccf5133ebd3a4c7b2d62d716098fb44ee09f64699f977dcfe4",
         "4acf4cc582679bdd3706d3a2bd276e41423f9052b87a86814d1b8143a721588b",
         "8662f4a65d153eaf87853faad11c492067706a16e557d2eba6c61094e02d5b86", 2, 1)),
    "scenario:kobo-daytime-delayed-publication": (
        ("kobo-daytime-delayed-publication", *DAY),
        ("f313d208f78758fe52f86992c3d48c6a24314568b14de379333d0445f61b2aab",
         "342cd774bf22b84d84f84278f04648db9e74413e421164e203a8207683c5dd19",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 2)),
    "scenario:kobo-daytime-larger-mill": (
        ("kobo-daytime-larger-mill", *DAY),
        ("a946e4771e502a90b9274c20ceef021e4dfbea6b750b3863afc5f1ed86e99fbf",
         "b3243f47ef647346a6f25eab5e9169165a83f299e1722feedb5b63b230519c00",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "15f9d34a9256151eef1fe90375cbe3ad3e68f376bce5870cc5b8db354264c586", 0, 0)),
    "scenario:kobo-daytime-overcast": (
        ("kobo-daytime-overcast", *DAY),
        ("dc8c7adaf973191593305296e7bc86eaf6d80f63e5d861a8711fc892ab743a22",
         "90440f70a6bb5e8109d1be1ff2bbbe70e849fdc223fc3f75384de4724851a31a",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "167eebdb55f73c90c005cfe367a8c9fe867ace28d151971c83e9122c5b69bb42", 0, 0)),
    "scenario:kobo-daytime-post-run-publication": (
        ("kobo-daytime-post-run-publication", "daytime-mini-grid", None, "2026-09-22T03:00:00Z",
         "2026-09-23T03:00:00Z", 15),
        ("d0939ce3b7f4260e2963788f2beece955d78a2a97f6f6f33eeb45395589adce7",
         "e666c6a0ccb008d1a417e4cebc8ddefe4bc5af620d20e5d1514559834c581352",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 2)),
    "scenario:kobo-daytime": (
        ("kobo-daytime", *DAY),
        ("2b0eb82c45af735f2c907f75e94a9494190564247f9e8060ea90cd376d6b6073",
         "bdb006830dfba539c4193fd6f6662db6583fe6d6612a15bc06f15b0dab563720",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
         "295bcb34edc52ad25721929f0a6be2b3eee0085e78e0f183f082158928a8551a", 0, 0)),
    "scenario:kobo-mill-midday": (
        ("kobo-mill-midday", *DAY),
        ("04de27b0936439ec4c3879d7fd219f48a4172e500a4eceb4ec024f14329f8bf7",
         "f3a65845c9728e837868af7c3f4a39589516507ee6f62c1ad1dd77b296427ed1",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-mini-grid-degraded-evidence": (
        ("kobo-mini-grid-degraded-evidence", *DAY),
        ("02fce21a7ecf4ae37eac1c28f19f337bb13b3a9ec6592612ea7ab6fa31b40c3d",
         "b1558cab54b7060a14bb6e8740637e8a86856107d307ca469520e2d91a651c92",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 3)),
    "scenario:kobo-mini-grid-evening": (
        ("kobo-mini-grid-evening", *DAY),
        ("60607e42780fb10e66cdc6ca275e8753fecdadecaaa4a351cd191ad5cc866ae2",
         "c599c9b0f9bb3d662399cf07d0ed9e6bb5a233d1b8ce2e8b62f4e8dd322d938d",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-mini-grid-prolonged": (
        ("kobo-mini-grid-prolonged", *DAY),
        ("d28e88fdbea7aff3c784eaec14bf86a6f338b41629cfc0dad25f27e4a623e6f2",
         "5833348e4deeaeec306394bb98b6debda160f27a4bdc08d08070ca7d1bcc1237",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-mini-grid-reserve-matters": (
        ("kobo-mini-grid-reserve-matters", *DAY),
        ("595f4c2ab7b0d34ec025d06232afde53c36d032492e80c0065278034f4830539",
         "9621fd680616d9088b0c0473d1a2a34899547c7532d02d5d9362936e0573a683",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-mini-grid-reserve-trial": (
        ("kobo-mini-grid-reserve-trial", *DAY),
        ("0341060097bdbd4b490c3b07e201c61cd5ddfd35c4fbe39bec42a13165e5a0ae",
         "2440269ccc966d386e2eea55a28eb1b31ae119c48434427d726a5e829008fd7d",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-mini-grid-stop-60": (
        ("kobo-mini-grid-stop-60", *DAY),
        ("643b53f38d1abd7bd017884c5bb75aafaf7d21c9c4e9cfee3563b2fe73f56000",
         "758666248cfcc04c50f989ff8226fab6495206767ab8ca391cee2585c75e19ab",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-night-early-after-before-mill": (
        ("kobo-night-early-after-before-mill", *DAY),
        ("a0d88d08f51bdb86a3ba18f56b575ff810cd4893b74011eddc3b288bbbf56b23",
         "016a890a10a4f8f31ef991f58fac3bdd24327767cb24d6ba24f6efbf287fd334",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-night-early-from-0300": (
        ("kobo-night-early-from-0300", *DAY),
        ("afa72cc3cc0c968bb22e269ecf38511428e2804c677ec71185e3cac4e18d74a7",
         "642d3b493d311477aa6598589de82d4e6bee029c66b1c4ff20cedf899eb7554a",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-night-early-until-0255": (
        ("kobo-night-early-until-0255", *DAY),
        ("609f59c087c7e1f7f078967b926a04ae53d70465fb0cb82609ea1f62597c1b0d",
         "d9791d20246e2f58dd1505dc94b8655664258d86163f5cf5f14e88b0c4f3a9f2",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-night-early-until-0300": (
        ("kobo-night-early-until-0300", *DAY),
        ("270f90ad65c18eb2bee579d8421c8d9cd728bb95d43c78aacddfc261cdc56a1b",
         "bbfb4340dc68b9141543846074580dfe2cab78d90f99a56727fe681e3791de42",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-night-early": (
        ("kobo-night-early", *DAY),
        ("286891d14bb56dc27da09d3e603ca90527738282f4499249cd99de730178fa7c",
         "36b56b429dd7483c1e97f131e6114d94d6be6f57bbac35a27abba79f269861d3",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-rest-before-mill": (
        ("kobo-rest-before-mill", *DAY),
        ("29b93de8f3a53df9ef27ea0dfcaefb68d224ff6741a01d4da22545b33716c959",
         "2647d492fcbdd32628ee315699330ab65fcbb805ab22336fbcda30fa300e38e8",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-rest-mill": (
        ("kobo-rest-mill", *DAY),
        ("47e0788192727b15f923298a78f98a07ce5aca80158fc51878a177ab70c70c71",
         "015feff7de8fc5278a3daf8660eaf0b9ceda8b7e25ec181043da5f001b59bc10",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-s3-dispatch-degraded-reporting": (
        ("kobo-s3-dispatch-degraded-reporting", *DAY),
        ("e386223f7bf3fa02bca2fb1bb390cd010f80e57cd5915bb2534b6c50cb88b5ef",
         "04033b62f0cc9d8099d58474c57b893adc4d934382126fd67cf586fb65298d0f",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 2)),
    "scenario:kobo-s3-dispatch-necessary-run": (
        ("kobo-s3-dispatch-necessary-run", *DAY),
        ("66efe5a698b72a1ba91c8802c6029f4455a284ac6f76fee34c81ff619f045003",
         "bf9bf87e3fe9529aba28dc45f357b738aadcf2959a55a4398b496ef2bbfa7816",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-steady-before-mill": (
        ("kobo-steady-before-mill", *DAY),
        ("e3fe9a8475779e938d653c25e46d4e72b7003551c30ff404e48e32068f4c2ba9",
         "a50c6a646e1325de7db005cf2101366356fbc8b6261e03d68cc2a61d01c6d272",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
    "scenario:kobo-steady-day": (
        ("kobo-steady-day", *DAY),
        ("0ca16cbdf48b2a4afa673f1f4bf40b6bea53ea701b44f93629b9115b0c3b28a9",
         "ccf5bb345149017e7154f65a9fb42030bfaed8f254214827b1ab7515e8399363",
         "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", None, 0, 0)),
}
