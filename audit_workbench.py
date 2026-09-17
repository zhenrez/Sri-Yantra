"""Reproducible, standard-library audit of the checked-in workbench artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit(rebuild: bool = False) -> dict:
    compiled_path = ROOT / "geometry/compiled.json"
    seal_path = ROOT / "preregistration/sri-native-seal-v1.json"
    before = {p: digest(ROOT / p) for p in ("geometry/compiled.json", "preregistration/sri-native-seal-v1.json")}
    if rebuild:
        subprocess.run([sys.executable, "-I", str(ROOT / "compile_geometry.py")], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "-I", str(ROOT / "seal_native.py")], cwd=ROOT, check=True)
        after = {p: digest(ROOT / p) for p in before}
        require(after == before, f"rebuild changed sealed artifacts: before={before}, after={after}")

    geometry = json.loads(compiled_path.read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "native/ledger.json").read_text(encoding="utf-8"))
    provenance = json.loads((ROOT / "native/provenance-map.json").read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "preregistration/sri-native-protocol-v1.json").read_text(encoding="utf-8"))
    exposure = json.loads((ROOT / "preregistration/sri-exposure-ledger-v1.json").read_text(encoding="utf-8"))
    architecture = json.loads((ROOT / "preregistration/research-architecture-v1.json").read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))

    require(geometry["implementation"]["sha256"] == digest(ROOT / "geometry/source.json"), "source export hash mismatch")
    require(protocol["status"] == exposure["classification"], "protocol/exposure classification mismatch")
    require(provenance["coordinate_topology"]["status"] == "COMPLETE_FOR_PINNED_PROFILES", "coordinate topology is not complete")
    require(provenance["P_topology"]["status"] == "UNRESOLVED_QUARANTINED", "P_topology lost quarantine")
    require(all(role["id"] != "ROSETTA" for role in architecture["roles"]), "ROSETTA reintroduced as a research role")
    require(architecture["adapter_function"]["status"] == "REAL_BUT_UNNAMED", "adapter namespace freeze changed")
    require(set(protocol["dependency_classes"]) == {x["id"] for x in ledger["dependency_classes"]}, "dependency-class mismatch")
    require(set(protocol["modal_statuses"]) == {x["id"] for x in ledger["modal_statuses"]}, "modal-status mismatch")

    profile_results = {}
    for name, profile in geometry["profiles"].items():
        vertices, edges, cells = profile["vertices"], profile["edges"], profile["cells"]
        vertex_ids, edge_ids, cell_ids = ({x["id"] for x in group} for group in (vertices, edges, cells))
        require((len(vertices), len(edges), len(cells)) == (69, 142, 74), f"{name}: wrong V/E/F")
        require((len(vertex_ids), len(edge_ids), len(cell_ids)) == (69, 142, 74), f"{name}: duplicate stable ID")
        require(len(profile["canonical_face_ids"]) == 43, f"{name}: wrong canonical count")
        require(set(profile["canonical_face_ids"]) == {c["id"] for c in cells if c["canonical"]}, f"{name}: canonical ID mismatch")
        require(Counter(c["depth"] for c in cells if c["canonical"]) == Counter({1: 14, 3: 10, 5: 10, 7: 8, 9: 1}), f"{name}: enclosure count mismatch")

        edge_by_id = {e["id"]: e for e in edges}
        cell_by_id = {c["id"]: c for c in cells}
        require(all(set(e["vertices"]) <= vertex_ids and len(e["vertices"]) == 2 for e in edges), f"{name}: invalid edge endpoints")
        require(all(e["generated_by"] for e in edges), f"{name}: missing edge provenance")
        require(all(1 <= len(e["cells"]) <= 2 and set(e["cells"]) <= cell_ids for e in edges), f"{name}: invalid edge/cell incidence")
        for cell in cells:
            require(set(cell["vertices"]) <= vertex_ids and set(cell["edges"]) <= edge_ids, f"{name}: invalid cell incidence")
            require(all(cell["id"] in edge_by_id[e]["cells"] for e in cell["edges"]), f"{name}: nonreciprocal cell/edge incidence")
            expected_neighbors = {other for e in cell["edges"] for other in edge_by_id[e]["cells"] if other != cell["id"]}
            require(set(cell["edge_adjacent"]) == expected_neighbors, f"{name}: wrong edge adjacency for {cell['id']}")

        seen, queue = set(), deque([cells[0]["id"]])
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            queue.extend(cell_by_id[current]["edge_adjacent"])
        require(seen == cell_ids, f"{name}: bounded cell dual is disconnected")
        require(len(edges) - len(vertices) + 1 == len(cells), f"{name}: Euler identity failed")

        verification = profile["verification"]
        require(verification["chiodo_float64"]["checks"] == 21 and verification["chiodo_float64"]["pass"], f"{name}: float64 Chiodo gate failed")
        require(verification["chiodo_decimal80"]["checks"] == 21 and verification["chiodo_decimal80"]["pass"], f"{name}: Decimal80 Chiodo gate failed")
        require(verification["bilateral_symmetry"]["checks"] == 27 and verification["bilateral_symmetry"]["pass"], f"{name}: symmetry gate failed")
        profile_results[name] = {
            "vertices": len(vertices), "edges": len(edges), "bounded_cells": len(cells),
            "canonical_triangles": len(profile["canonical_face_ids"]),
            "float64_max": verification["chiodo_float64"]["maximum_residual"],
            "decimal80_max": verification["chiodo_decimal80"]["maximum_residual"],
        }

    entries = seal["entries"]
    for entry in entries:
        path = ROOT / entry["path"]
        require(path.is_file(), f"sealed file missing: {entry['path']}")
        require(entry["bytes"] == path.stat().st_size and entry["sha256"] == digest(path), f"sealed file changed: {entry['path']}")
    payload = {k: seal[k] for k in ("schema", "scope", "entries")}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    require(hashlib.sha256(canonical).hexdigest() == seal["manifest_sha256"], "manifest hash mismatch")

    return {"status": "PASS", "manifest_sha256": seal["manifest_sha256"], "profiles": profile_results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="rebuild geometry and seal and require byte-identical output")
    args = parser.parse_args()
    print(json.dumps(audit(rebuild=args.rebuild), indent=2))
