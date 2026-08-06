# QNeCT Documentation

This directory is the documentation home for QNeCT, separate from the
top-level `readme.md`/`index.md` (which remain short project overviews and
entry points). It exists so documentation can grow without turning the
README into an unmaintainable dumping ground, and so future contributors
have an obvious place to add material of a given kind.

## Why this structure

The layout follows [Diataxis](https://diataxis.fr/), a documentation
taxonomy used by long-running engineering projects (Django, Kubernetes,
the Python packaging guides, among others). Diataxis splits documentation
into four kinds, based on what the reader is trying to do, not what
component of the code it describes:

| Directory | Reader's need | Example for this project |
|---|---|---|
| [`tutorials/`](tutorials/) | *Learning* — a guided path for someone new | "Build your first repeater chain and read out its fidelity" |
| [`how-to/`](how-to/) | *Doing* — a specific task, assumes basic familiarity | "How to run the noise model with custom fiber loss" |
| [`reference/`](reference/) | *Looking up* — precise facts about the API | Per-module description of every public class/function, inputs, and outputs |
| [`explanation/`](explanation/) | *Understanding* — background and rationale | Why the package is layered the way it is; the physics behind the noise channels |

Rationale for a physics/research codebase specifically: a contributor
extending the noise model needs *explanation* (what physical process is
being modeled and why), a user of the Streamlit app needs *how-to* and
*tutorial* material, and anyone calling the library from a script needs
*reference*. Mixing all of that into one README is what produced the
current `readme.md`/`index.md` — both trying to be all four at once, and
drifting out of sync with each other in the process.

## Status

This skeleton was created as part of the repository hygiene pass on
`review/aug2026`. Only the sections below are populated with real content
today; the rest are stubs describing what belongs there so contributors
don't have to guess:

- [`explanation/architecture.md`](explanation/architecture.md) — populated (module layering and dependency direction)
- [`explanation/physics-background.md`](explanation/physics-background.md) — populated (pointer to `QR_Protocol.pdf` and the physical model)
- [`tutorials/`](tutorials/README.md) — stub
- [`how-to/`](how-to/README.md) — stub
- [`reference/`](reference/README.md) — stub

## Planned follow-up (not yet approved — listed here for visibility)

- Populate `reference/` with one page per `qrnetwork` module (`primaryfn`,
  `qteleportation`, `qchannel`, `network`), once docstring coverage is
  improved (tracked as a P2 item from the engineering review).
- Consolidate `readme.md`/`index.md` so one is the single source of truth
  and the other either mirrors or links to it, instead of the current
  hand-maintained duplication. This is a structural decision and is being
  deferred to a future approval step rather than done as part of this
  hygiene pass.
