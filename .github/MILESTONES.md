# Proposed milestone structure

STATUS: PROPOSAL ONLY — no milestones have been created on GitHub. This
document is the reference a maintainer can use to create them via the
repo's Issues → Milestones page.

## Why not sprints

GitHub Milestones are often used as calendar-boxed sprints (e.g. "Sprint
14, due in 2 weeks"). That model fits teams shipping continuously; it
fits poorly for a small research group where contributors are students
balancing coursework, and where "done" is often "the physics is right,"
not "the deadline arrived." The structure below uses milestones as
**scope containers with completion criteria**, not calendar deadlines.
Due dates are optional and, where used, should be treated as soft
planning targets, not commitments.

## Track A — Engineering infrastructure

One milestone per phase of the ongoing engineering review. Each is
closed when its stated scope is done, not on a schedule. This track is
finite — it ends at "v1.0."

| Milestone | Scope | Status |
|---|---|---|
| `Phase 0 — Repository Hygiene` | `.gitignore`, dead-file cleanup, README fixes, initial `docs/` skeleton | Complete (done on `review/aug2026`) |
| `Phase 0.5 — Governance & Collaboration` | PR/issue templates, CODEOWNERS, label taxonomy, CONTRIBUTING.md | In progress (this phase) |
| `Phase 1 — Regression Test Baseline` | Automated tests pinning current simulator output, so later changes can be verified as behavior-preserving | Not started |
| `Phase 2 — Packaging` | `pyproject.toml`, installable package, resolves the repo-root-relative-import issue | Not started |
| `Phase 3 — CI/CD` | Automated test/lint runs on PRs | Not started |
| `Phase 4 — Code Quality` | De-duplication (P2/P3 items from the engineering review), consistent docstrings | Not started |
| `v1.0 — Stable Release` | All of the above complete; first version considered stable for outside use/citation | Not started |

## Track B — Research / feature milestones

This track is open-ended by nature and its *content* is a scientific
decision for the project's researchers, not something this review sets.
What's being proposed here is only the **existence of the track and its
shape** — a place to group science-driven work distinctly from
engineering-hardening work, so a contributor looking at the milestone
list can tell "is this a plumbing task or a research question?" at a
glance.

Illustrative examples only (not a commitment to build these):
- `Noise Model Extensions` — e.g. memory-cutoff time, non-Markovian effects
- `Beyond Linear Topology` — star/mesh repeater networks
- `Multi-Party Entanglement` — GHZ states, W states, N > 2 protocols

A maintainer should create Track B milestones as actual research
direction is set, using whatever scope/title makes sense at the time —
this document is not meant to constrain that.

## Suggested labels-to-milestone convention

Track A milestones map naturally to `architecture` and `testing` issues
(see `labels.yml`). Track B milestones map naturally to `physics` and
`simulation` issues. This isn't a hard rule — it's a sanity check when
triaging: if a `Phase 1` issue is tagged `physics`, that's worth a
second look.
