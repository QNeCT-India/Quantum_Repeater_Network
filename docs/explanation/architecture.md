# Package architecture

This describes how `qrnetwork` is layered today and why, as a reference
for anyone extending it. It documents the existing design — it does not
propose changes.

## Layers

```
primaryfn.py         state representation & algebra: Q, Is, Qp, Ebit
      ^
      |
qteleportation.py     single-channel teleportation, built on primaryfn
      ^
      |
qchannel.py            Monte-Carlo channel-fidelity estimation, built on qteleportation
      ^
      |
network.py            entanglement swapping & multi-hop repeater chains (eswap, QRep), built on primaryfn
```

- **`primaryfn.py`** has no dependency on the rest of the package. It
  defines `Q` (a fluent wrapper around a complex NumPy array — states and
  operators), `Is` (structural checks: is this a ket, is it square, is it
  Hermitian, is it pure), `Qp` (binary operations on a pair of states:
  inner/outer/tensor product, fidelity), and `Ebit` (entanglement measure,
  concurrence by default).
- **`qteleportation.py`** implements the standard teleportation protocol
  (`teleport_ket_state`, `teleport_density_state`) and the `Teleport`
  class that dispatches between them based on whether the input state is
  a ket or a density matrix.
- **`qchannel.py`** wraps `qteleportation` in a Monte-Carlo loop
  (`QChannel.teleport()`) to estimate the average fidelity a given
  entangled channel achieves over many random input states.
- **`network.py`** is independent of `qteleportation.py` — it does not
  import or reuse it. It implements entanglement swapping directly
  (`eswap`, with `.ket()`, `.density()`, and `.noise()` variants) and
  chains swaps across a linear list of shared states (`QRep.linear()`).

`qrnetwork/__init__.py` re-exports the intended public surface:
`Q, Qp, Is, Ebit, Teleport, QChannel, eswap, QRep`.

## What consumes the package

- `mainQRN.py` (repo root) — a script that exercises the library directly
  via `from qrnetwork import *`.
- `app.py` (repo root) — a Streamlit GUI that imports the same public
  names and additionally implements its own simulation-orchestration
  helper (`run_repeater_simulation`) on top of `QRep`.

Both live outside the `qrnetwork` package and depend on being run from
the repository root, since the project is not currently pip-installable
(no `pyproject.toml`/`setup.py`).

## Known duplication (documented, not yet resolved)

`qteleportation.py` and `network.py` each independently define the Bell
basis list and a Pauli-correction lookup table, and `eswap.density()` /
`eswap.noise()` share a near-identical measurement-and-correction tail.
These are candidates for consolidation but touch the numerical control
flow directly, so they are deferred to a future, explicitly-approved
change backed by a regression test suite — see the engineering review
recommendations (P3).
