"""Dependency-neutral contracts both sides of the truth barrier speak.

v4 section 3.2, rule 5: a schema used on both sides lives in an already-neutral
contract module, and the simulator does not import the backend merely to
construct one. This package is that module root.

It imports neither `assetops_backend` nor `assetops_simulator`, and
`tools/checks/dependency-direction.ps1` holds that structurally. Nothing here
reads a document, opens a file, or reaches a store: these are the versioned
rules and the record shapes, and resolving either against a Site or a scenario
belongs to the product domain on one side and to the host adapter on the other.

Seven modules:

- `execution_contract` - the versioned semantics: canonical units, half-open
  dispatch, the boundary cycle, what a timestamped reading describes, whether a
  reading exists at all, the bound policies, and the dispatch and cadence
  formulas as executable arithmetic;
- `world_inputs` - what one execution of one frozen Draft consumes, with no
  field an authored reading or a private expectation could arrive in;
- `trajectory` - the private trajectory a kernel produces, and what binds its
  identity;
- `observation` - what a device reports, in a record that carries no true value,
  and the BLAKE2b-256 draw contract the first stochastic mechanism uses;
- `lab_projection` - the one gated record where a true value and a reported value
  sit in one row, and the vocabulary a refused control request speaks;
- `failures` - why an execution stopped, as a vocabulary distinct from run
  setup's refusals, a Draft's blocking reasons and a refused control;
- `identity` - the BLAKE2b-256 identity domain and its canonical encoding.
"""

__all__: list[str] = []
