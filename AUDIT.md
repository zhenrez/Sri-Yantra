# Geometry and topology audit

Audit date: 2026-09-17. Governing mathematical source: Alessandro Chiodo, *On the construction of the Śrī Yantra* (2021), user-supplied published PDF, DOI `10.5802/crmath.163`. Checked implementation: pinned `TheHardikDewra/sri-yantra` export and solver code at commit `1da047f4641a9ea95457080801f2438e634d668a`. Comparison artifact: user-supplied *Sri Yantra Graph / Dual* PDF.

## Confirmed

- Chiodo numbers nine generating triangles by descending base height: `t1..t5` downward and `t6..t9` upward. The pinned solver uses that convention.
- The solver's seven apex/base pairs exactly match Chiodo condition (ii), including the easily omitted `(t1,t6)` pair.
- The solver's twelve concurrency triples exactly match Chiodo condition (iii).
- Huet's four base-point parameters in Chiodo note 20 are `0.332, 0.537, 0.602, 0.835`; those are the upstream `huet` profile values.
- Chiodo presents the minimally concurrent family with four real parameters up to the paper's stated rescaling/congruence equivalences. The UI must therefore treat a geometry as a profile, not as the unique Śrī Yantra.
- The pinned export contains 74 bounded planar regions. Exactly 43 are marked as traditional triangular regions in the required `14/10/10/8/1` enclosure counts.
- Reconstructing atomic edges from exported polygon sides gives `V=69`, `E=142`, `F_bounded=74`. Euler's connected planar identity holds: `E - V + 1 = 74`.
- The compiler locally recomputes 21 float64 checks directly from exported coordinates: two common-circumcircle residuals for condition (i), seven apex/base residuals for (ii), and twelve right-side concurrence residuals for (iii). It separately checks bilateral symmetry before inferring the left-side conditions. Maximum float64 residuals are `5.55e-17` for Huet and `1.11e-16` for the rational realization, below the frozen `1e-12` gate.
- A second arithmetic pass uses the upstream approximately 40-digit decimal strings in an 80-digit Decimal context. Maximum residuals are approximately `6.45e-41` for Huet and `7.49e-41` for the rational realization, below the declared `1e-35` gate. This checks arithmetic stability against float64 rounding; it is not an independent source of coordinates or a proof of uniqueness.

## Corrections made

- Compiler schema upgraded from a 43-face selection to the complete 74-region cell complex.
- Added 69 stable vertex addresses, 142 stable atomic-edge addresses, 31 auxiliary-region addresses, cell-to-edge incidence, edge adjacency, and shared-corner contact.
- Retained the 43 traditional triangles as an explicit subset rather than equating them with the entire planar arrangement.
- Renamed the second UI profile to “Rational parameters (upstream label: traditional).” Its label is an upstream convention, not evidence that it is the uniquely traditional construction.
- Reuse entities by `(name, tradition)` in SQLite instead of creating a duplicate entity for every placement/event.
- UI can toggle between the 43 traditional triangles and all 74 bounded regions.
- Added Chiodo's conditions (i), seven pairs in (ii), and twelve triples in (iii) as machine-readable authority metadata.
- Added generating-triangle, orientation, and base/leg provenance to atomic edges; vertices now record apex, base-point, intersection, and triple-concurrency roles without SUN labels.
- Split coordinate-derived topology, graph-to-geometry provenance (`P_topology`), and geometry-to-construction provenance (`P_construction`). The coordinate topology is complete for the pinned profiles; `P_topology` is not. None may substitute for another.
- Added a native three-layer ledger: `G_INTRINSIC`, `G_CONSTRUCTION`, and `G_INTERPRETATION`.
- Added orthogonal relation-class and modal-status fields. For example, a relation may be geometrically stated yet realization-specific, or constructional yet unnecessary.
- Sealed the native ledger, provenance map, compiled geometry, native protocol, exposure ledger, and research-role map by byte-level SHA-256 manifest.

## Research-program boundary

The surviving object is a candidate target, not an established novelty claim: preserved observation under hidden change; typed nontrivial traversal; local relational closure with global nonclosure; inequivalent internal routes with convergent realization; and lawful transport of the conjunction across domains. THREAD remains the historical recurrence of explicit musical/harmonic objects used to organize nonmusical systems, not generic process language. Śrī is an independent pressure-test and sophisticated negative control; isolated concurrence, recursion, route convergence, return symbolism, or a `2/3` value must fail to establish the full conjunction.

The preregistration classifies Śrī as a `PARTIALLY_EXPOSED_TYPE_II_CALIBRATION_DOMAIN`: SUN, its ratios, the printed route motif and the exceptional-boundary analogy were known before observable selection. The exposure ledger distinguishes prior knowledge from still-unresolved substructure. Future KEYSTONE-on-anonymized-Śrī and frozen-SUN-on-sealed-Śrī runs are separate calibration experiments and must retain separate provenance. A later untouched domain is required for genuine blind validation.

The current research architecture deliberately contains no ROSETTA role. Historical snapshots preserve their original notation, while the cross-domain adapter/model-construction function remains unnamed pending deliberate namespace resolution.

## SYG/SYD document finding

The graph PDF is useful as a comparison artifact but is not safe as the canonical topology source without a numbering key and correction. Its primal adjacency table has 69 vertices and degree sum 280, hence 140 edges. A connected arrangement with 69 vertices and 74 bounded faces requires 142 edges. Its later face-boundary table contains 142 distinct edge pairs but does not correspond directly to the first table's edge labels. Therefore this workbench derives topology from the pinned coordinates and tests Euler's identity instead of importing the PDF numbering.

## Still not independently proved

- The upstream 60-digit solver's 49-check report was inspected but has not been vendored and rerun here. This workbench recomputes the 21 residuals representing Chiodo's three condition classes at float64 and Decimal80 precision as described above, using the pinned exported coordinates rather than rerunning the upstream solver.
- The outer lotus, circle, and bhūpura dimensions in the upstream renderer are conventions beyond Chiodo's minimal triangle concurrency conditions. They are not yet part of the addressable geometry kernel.
- Individual traditional deity/mantra placements have not been authenticated by lineage and passage, and none are embedded in geometry.
- Stable IDs are deterministic within this compiler version. Cross-profile identity is not asserted merely because two features share the same ordinal address.
