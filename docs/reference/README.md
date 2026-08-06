# Reference

*Status: stub — not yet populated.*

This is where precise, lookup-oriented API documentation will live: one
page per `qrnetwork` module, listing every public class/function with its
parameters, return type, and exceptions raised — the kind of material a
reader consults while already writing code against the library.

Planned pages, mirroring the package layout described in
[`../explanation/architecture.md`](../explanation/architecture.md):

- `primaryfn.md` — `Q`, `Is`, `Qp`, `Ebit`
- `qteleportation.md` — `Teleport`, `teleport_ket_state`, `teleport_density_state`
- `qchannel.md` — `QChannel`
- `network.md` — `eswap`, `QRep`

This is intentionally deferred rather than drafted now: several of these
classes and functions do not yet have docstrings (noted in the
engineering review's documentation assessment), and writing reference
docs before the source has consistent docstrings would mean maintaining
the same information in two places. The recommended order is: add
docstrings to the source (P2), then generate/write this reference from
them.

Until this exists, the closest equivalent is the "Function reference"
table on the Documentation tab of the Streamlit app (`streamlit run
app.py`), and the function tables in [`../../readme.md`](../../readme.md).
