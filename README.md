# Śrī workbench

Local runnable vertical slice: two solved geometry profiles, a complete 69-vertex/142-edge/74-bounded-region planar cell complex, the traditional 43-triangle subset, selectable SVG, and independently stored SQLite overlays and n-ary events. Designed so AYLI can consume compiled geometry and overlay exports later without changing the geometry source.

## Windows 11: double-click start

Download the repository ZIP, extract it, and double-click **`START-SRI-WORKBENCH.cmd`**. The launcher selects an official CPython 3.13 or 3.11 installation, creates `.venv`, installs `requirements.txt`, removes inherited Python/Conda/NVIDIA/CUDA variables from the launcher process, verifies the geometry seal, starts the local server, and opens the browser. It does not modify or uninstall any global Python, NVIDIA, CUDA, or Conda setup. Keep the launcher window open while using the workbench; close it or press Ctrl+C to stop.

GitHub and Windows intentionally do not permit a web link to download and execute arbitrary code silently. The safe minimum is therefore one double-click **after** downloading and extracting the repository. Windows SmartScreen may ask you to confirm a newly downloaded script.

Every push is also exercised by the `Windows launcher verification` workflow, which repeats virtual-environment creation, requirements installation, geometry compilation, and seal verification on a clean Windows runner.

## Verification

The double-click launcher runs these checks automatically. Manual equivalents are:

```powershell
py -3.13 -I audit_workbench.py --rebuild
py -3.13 -I -m unittest discover -s tests -v
```

`audit_workbench.py --rebuild` requires byte-identical regeneration of both `geometry/compiled.json` and the native seal. It checks source hashes, stable-ID uniqueness, incidence reciprocity, connectedness, Euler consistency, canonical enclosure counts, edge provenance, both arithmetic residual passes, research-contract consistency, namespace firewalls, and every sealed file hash. CI runs the same contract under Python 3.11 and 3.13.

The research contract now ships with a SUN-free native ledger, noncollapsed provenance layers, a preregistered negative-control suite, an explicit exposure ledger, a frozen research-role map, and a content-addressed seal. The coordinate-derived topology is complete for the two pinned profiles. `P_topology`—the map from a numbered printed-SYG feature to an actual coordinate/geometric entity—remains unresolved and quarantined. `P_construction` independently maps a geometric entity to a derivational dependency and is currently partial. Every admitted claim has two orthogonal coordinates: relation class (`GEOMETRIC`, `CONSTRUCTION`, `SOLVER`, `RITUAL`, `SYMBOLIC`) and modal status (`NECESSARY`, `OPTIONAL`, `REALIZATION_SPECIFIC`, `UNKNOWN`). Read the complete contract at `/api/native`; regenerate the seal with the selected virtual-environment Python after an intentional native-data revision.

Manual alternative: use either `py -3.13` or `py -3.11` in place of `python3`. Run `py -3.13 compile_geometry.py`, then `py -3.13 server.py --port 8765`; open `http://127.0.0.1:8765`. No npm installation is required. `workbench.sqlite3` is created at startup. Data edits stay there. Export creates a JSON snapshot of research state.

Mathematical authority: [Chiodo 2021](https://comptes-rendus.academie-sciences.fr/mathematique/articles/10.5802/crmath.163/), whose minimal conditions parameterize a four-parameter concurrent family up to the paper's stated equivalences. Checked implementation: `geometry/source.json` copied from [TheHardikDewra/sri-yantra](https://github.com/TheHardikDewra/sri-yantra), `public/data/sri-yantra.json`, MIT license, commit `1da047f4641a9ea95457080801f2438e634d668a`. The compiler stamps the implementation commit and byte SHA-256 separately from Chiodo's authority metadata. It locally recomputes the 21 Chiodo-condition residuals in float64 and from the upstream approximately 40-digit decimal strings using an 80-digit Decimal context; it also checks the bilateral symmetry needed to infer the left-side concurrence conditions. Huet's parameter values select one realization; the second rational profile is experimental and inherits only the upstream label “traditional.”

The compiler orders canonical triangular-region IDs clockwise from north within each enclosure, separately per profile. It reconstructs atomic edges by splitting every exported polygon side at collinear arrangement vertices, then derives edge adjacency, shared-corner contact, and generating-parent provenance. See `AUDIT.md` for the Chiodo/code/SYG-SYD cross-check. Outer petals, gates, circles, 3D surfaces, a complete construction DAG, and individual source-backed deity positions remain later slices. Imported traditional deity identities should be overlay records with lineage and passage, never fields in `geometry/compiled.json`.

Current database tables: overlays, entities, placements, relation_events, event_participants. Relation events retain both geometry profile and feature address. The three-role event represents an overlay-specific proposed `A + B → C` relation. Its feature link is a binding and carries no claim that Śrī Vidyā assigns this meaning to three corners. Direct HTTP access to the SQLite file is denied.

Scientific limit: Śrī is a `PARTIALLY_EXPOSED_TYPE_II_CALIBRATION_DOMAIN`. SUN, its ratios, the printed route motif, and the exceptional-boundary comparison were already known when the observable families were selected. The sealed record can support prospective calibration, robustness and discrimination tests, but it cannot honestly be reported as an untouched blind discovery. A later untouched domain is required for external blind validation. Kulaichev and Mahesh remain explicit placeholders until their primary texts and tables are ingested.

Namespace rule: historical SUN snapshots remain unchanged, including their old `\mathcal{R}` notation. The current research architecture has no ROSETTA component. The lawful adapter/model-construction function remains real but unnamed until the repository/application/snapshot namespace collision is deliberately resolved.
