# Physics background

QNeCT simulates **quantum repeater networks**: chains of intermediate
nodes that distribute entanglement between two distant parties by
generating entangled pairs over each short link and then performing
**entanglement swapping** at each intermediate node, extending
entanglement end-to-end without physically transmitting a qubit the full
distance.

The detailed protocol description, including the swapping procedure and
the noise model implemented in `qrnetwork.network` (fiber loss as
amplitude damping, memory dephasing, and detector dark counts), is
written up in [`QR_Protocol.pdf`](../QR_Protocol.pdf) at the repository
root. That document is the authoritative reference for *why* the
`noise()` methods in [`network.py`](../qrnetwork/network.py) compute what
they compute; this page exists mainly to make the PDF discoverable from
the documentation tree, since previously nothing linked to it.

See also [`architecture.md`](architecture.md) for how the physical model
maps onto the package's module layout.
