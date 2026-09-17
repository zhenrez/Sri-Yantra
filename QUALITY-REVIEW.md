# Accuracy and quality review

Review date: 2026-09-17.

## Primary verdict

The checked-in computation reproducibly verifies a finite assertion about two pinned coordinate exports: each compiles to a connected planar bounded-cell complex with `V=69`, `E=142`, `F_bounded=74`, and 43 canonical triangular regions in `14/10/10/8/1` enclosures; the exported triangle parameters satisfy the 21 encoded Chiodo residual checks under the declared float64 and Decimal80 gates.

This does **not** prove uniqueness, authenticate every upstream solver claim, establish traditional symbolic assignments, or resolve the printed SYG numbering. In particular:

```text
coordinate_topology = COMPLETE_FOR_PINNED_PROFILES
P_topology           = UNRESOLVED_QUARANTINED
P_construction       = PARTIAL_CHIODO_ONLY
```

## Corrections made

- Replaced the inaccurate “rescaling and translation” formulation with Chiodo's rescaling/congruence scope.
- Stopped treating an uninspected Huet citation as locally authenticated primary evidence.
- Separated complete coordinate topology from unresolved graph-to-geometry `P_topology`.
- Added an 80-digit Decimal residual pass and an explicit bilateral-symmetry gate.
- Added quantization-collision, edge-provenance, and edge/cell-incidence assertions to compilation.
- Made compiled geometry and seal writes atomic.
- Added a reproducible artifact auditor and API/database tests.
- Stored geometry profile on relation events and supplied an in-place SQLite migration.
- Denied direct HTTP access to the SQLite database and non-runtime repository files.
- Required a source/passage for records labelled `source-backed`.
- Removed an inert traversal-direction control and corrected misleading UI terminology.
- Added keyboard focus styling, control labels, keyboard selection, and research-contract metadata to exports.

## Evidence commands

```text
python -I audit_workbench.py --rebuild
python -I -m unittest discover -s tests -v
```

Both commands are standard-library-only. GitHub workflows exercise Python 3.11 and 3.13 on Linux and the isolated launcher path on Windows.

## Residual risks

- The coordinate and cell export is pinned upstream evidence; the upstream 60-digit solver and its 49-check report have not been vendored and independently rerun.
- Decimal80 uses the upstream approximately 40-digit decimal strings. It tests arithmetic stability, not coordinate independence.
- The fixed `1e-9` topology quantization is asserted safe for these two profiles, not proved safe over the full four-parameter realization family.
- The supplied printed SYG/SYD document remains internally inconsistent as used here: its adjacency table gives 140 edges, while its face table uses 142 distinct edge pairs.
- The local-only interface could not be reached by the cloud screenshot browser during this review. UI behavior is covered structurally and through API tests, but a final Windows visual/accessibility pass remains outstanding.
