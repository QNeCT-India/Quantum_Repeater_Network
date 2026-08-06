# Contributing to QNeCT

Thanks for your interest in QNeCT (Quantum Network and Communication
Toolbox). This document describes how to propose changes and the
conventions currently in effect on this project.

## Project status

This repository is a research-software codebase currently undergoing its
first structured engineering review (see the `review/*` branches). That
review is behavior-preserving by design: algorithms are not being
rewritten, only structure, naming, duplication, and documentation. If
you're contributing during this period, please follow the same
principle unless you're explicitly proposing an algorithmic or
architectural change (see "Proposing larger changes" below).

## How to propose a change

1. Open an issue (or start your PR description with one) describing
   **why** the change is needed, not just what it does. For bug fixes,
   include the failing scenario; for refactors, explain what's
   confusing or risky about the current code.
2. Keep changes small and scoped to one concern. Prefer several small,
   reviewable PRs over one large one.
3. Keep commits small and logically grouped — each commit should
   represent one coherent change (e.g. "remove dead code in
   qteleportation.py" separate from "add docstrings to Q class") so the
   history stays bisectable and reviewable.
4. If your change alters simulator output for any input (not just
   formatting/refactoring), say so explicitly in the PR description —
   this project treats "identical results" as the default expectation
   for anything not an intentional physics/algorithm change.

## Proposing larger changes

Structural or architectural changes (e.g. merging modules, changing
public APIs, consolidating the duplicated measurement/correction logic
noted in [`docs/explanation/architecture.md`](docs/explanation/architecture.md))
should be proposed and discussed before being implemented, ideally with
a short written rationale. This project currently has no automated
regression test suite (see "Testing," below), so changes that affect
computation are especially risky to land without prior discussion — the
plan is to build that test suite before undertaking any such change.

## Code style

- The core `qrnetwork` package uses a deliberately terse "fluent" method
  style (`Q(state).d().u()`, `Qp(a, b).fid()`, etc.) — see the note at
  the top of the `Q` class in
  [`qrnetwork/primaryfn.py`](qrnetwork/primaryfn.py) for the rationale.
  Match this style within `primaryfn.py`/`qteleportation.py`/
  `qchannel.py`/`network.py` rather than introducing a different
  convention; renaming existing public methods is a breaking API change
  and needs prior discussion.
- Follow standard PEP 8 naming for anything outside that established
  fluent API (module names, new functions/classes, variables).
- Prefer adding docstrings to new public classes/functions. See
  `qrnetwork/primaryfn.py`'s `Q` class methods for the current standard
  to match.
- Avoid adding commented-out code as a way of preserving history — that's
  what git history is for.

## Documentation

Longer-form documentation lives under [`docs/`](docs/README.md), organized
by reader intent (tutorial / how-to / reference / explanation — see that
file for the rationale). If you're adding a new capability:
- User-facing usage guidance → `docs/how-to/`
- New public API surface → update `docs/reference/` once that section is
  populated (currently a stub; until then, keep the function tables in
  `readme.md`/`index.md` and the Streamlit "Documentation" tab in sync)
- Design rationale / physics background → `docs/explanation/`

## Testing

There is currently no automated test suite for this project — this is a
known gap being tracked as a priority follow-up to the engineering
review, not an oversight to work around. Until it exists:
- Manually verify your change doesn't alter existing outputs for
  representative inputs (Bell states, Werner states, both noiseless and
  noisy `QRep` chains) before submitting.
- If you're adding new functionality, consider including a small,
  self-contained script demonstrating expected input/output as part of
  your PR description — this makes manual review meaningful and will
  make it easy to convert into an automated test once the suite exists.

## Licensing

This project does not yet have a formal license file (tracked as an open
item). By submitting a contribution, you agree it may be included in the
project under whatever license is ultimately adopted.
