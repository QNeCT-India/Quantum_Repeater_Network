# Contributing to QNeCT

Thanks for your interest in QNeCT (Quantum Network and Communication
Toolbox). This document is meant to be self-contained: if you're a new
contributor (including a new student in the group), you should be able
to go from "cloned the repo" to "opened a PR" using only this file and
the links inside it.

## Project status

This repository is a research-software codebase currently undergoing a
structured engineering review (see the `review/*` branches and
[`docs/README.md`](docs/README.md)). That review is behavior-preserving
by design: algorithms are not being rewritten, only structure, naming,
duplication, and documentation. If you're contributing during this
period, please follow the same principle unless you're explicitly
proposing an algorithmic or architectural change (see "Proposing larger
changes" below).

## Getting set up

1. Clone the repo and install dependencies — see the
   ["Installation" section of `readme.md`](readme.md#installation) for
   the exact commands (`pip install -r requirements.txt`).
2. Confirm your setup works:
   ```sh
   python mainQRN.py
   ```
   This should print a list of measurement-outcome dictionaries with no
   errors. If it doesn't, your environment isn't set up correctly yet —
   fix that before writing any code.
3. Optionally, run the GUI to explore the project interactively:
   ```sh
   streamlit run app.py
   ```
4. Read [`docs/explanation/architecture.md`](docs/explanation/architecture.md)
   before touching `qrnetwork/` — it explains how the four modules
   depend on each other, which isn't obvious from file names alone.

## Finding something to work on

- Browse [open issues](https://github.com/QNeCT-India/Quantum_Repeater_Network/issues).
  Issues labeled `good first issue` are scoped to be tractable
  without deep context on the rest of the project — start there if
  you're new. See [`.github/labels.yml`](.github/labels.yml) for the
  full label taxonomy and what each label means.
- If nothing open matches what you want to work on, open an issue first
  using the appropriate template (see "How to propose a change," below)
  before writing code — this avoids duplicated or wasted effort, and
  gives a maintainer a chance to flag a concern (e.g. "we tried that,
  here's why it didn't work") before you invest time.
- [`.github/MILESTONES.md`](.github/MILESTONES.md) describes the
  project's longer-term structure (engineering-hardening phases vs.
  open-ended research/feature work), if you want to see how a given
  issue fits into the bigger picture.

## How to propose a change

1. **Open an issue first**, using whichever
   [issue template](.github/ISSUE_TEMPLATE/) fits: bug report, feature
   request, or research discussion (for open-ended scientific/design
   questions that don't yet have a clear answer). Explain **why** the
   change is needed, not just what it does.
2. **Fork the repository and branch from `main`.** Most contributors
   (including students) have read-only access to this repo directly, so
   you'll push to your own fork and open a pull request from there —
   GitHub's ["fork and pull request" workflow](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)
   covers the mechanics if you haven't done this before. (If you've been
   given push access directly, use a branch instead of a fork, but still
   open a PR rather than pushing to `main`.)
3. **Keep changes small and scoped to one concern.** Prefer several
   small, reviewable PRs over one large one.
4. **Keep commits small and logically grouped** — each commit should
   represent one coherent change (e.g. "remove dead code in
   qteleportation.py" separate from "add docstrings to Q class") so the
   history stays bisectable and reviewable.
5. **Open the PR against `main`** and fill in the
   [PR template](.github/PULL_REQUEST_TEMPLATE.md) completely — the
   "Scientific Impact" section is not optional even for small changes,
   since it's how a reviewer knows whether to check numerical output.
6. **Expect review from a maintainer.** [`.github/CODEOWNERS`](.github/CODEOWNERS)
   currently routes all review requests to the project maintainers
   (`@ToxicLabs-iiser`, `@SatishS11`); this will expand as the group
   grows (see that file for how).

If your change alters simulator output for any input (not just
formatting/refactoring), say so explicitly in the PR description — this
project treats "identical results" as the default expectation for
anything not an intentional physics/algorithm change.

## Proposing larger changes

Structural or architectural changes (e.g. merging modules, changing
public APIs, consolidating the duplicated measurement/correction logic
noted in [`docs/explanation/architecture.md`](docs/explanation/architecture.md))
should be proposed and discussed — open a **Research Discussion** issue
if it's a scientific/design question, or a **Feature Request** if the
desired outcome is already clear — before being implemented. This
project currently has no automated regression test suite (see
"Testing," below), so changes that affect computation are especially
risky to land without prior discussion; the plan is to build that test
suite before undertaking any such change.

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

Governance/process documentation (this file, issue and PR templates,
CODEOWNERS, labels, milestones) lives in the repository root and
`.github/` rather than under `docs/` — that's a GitHub convention
(GitHub only recognizes `CODEOWNERS`, issue/PR templates, etc. in
specific locations), not an exception to the `docs/` taxonomy.
`docs/README.md` links out to this file so the two stay connected.

## Testing

There is currently no automated test suite for this project — this is a
known gap being tracked as a priority follow-up (see
[`.github/MILESTONES.md`](.github/MILESTONES.md), Phase 1), not an
oversight to work around. Until it exists:
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
