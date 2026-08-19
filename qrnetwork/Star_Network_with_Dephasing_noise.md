# Entangled Star Network Protocol with Dephasing Noise & Entanglement Swapping

A Python framework modeling **asynchronous bipartite link generation**, **pure dephasing under quantum memory waiting times**, and **sequential multi-link entanglement swapping** on a centralized star architecture using Pauli and Bell operators.

---

## Theoretical Framework

### 1. Link Generation & Memory Waiting Times
In distributed quantum networks, elementary links are generated probabilistically at discrete time steps (rounds) $t_i \in \mathbb{N}$. If link $i$ is generated at round $t_i$, it must be stored in quantum memory until the slowest link $t_{\max} = \max_i \{t_i\}$ is established.

The memory storage duration for link $i$ is:

$$w_i = t_{\max} - t_i$$

### 2. Quantum Dephasing Channel
During memory storage, each link undergoes pure phase damping governed by the single-qubit Kraus decomposition:

$$\mathcal{E}(\rho) = \sum_{k=0}^1 (K_k \otimes I)\,\rho\,(K_k \otimes I)^\dagger$$

where the Kraus operators parameterize noise parameter $\lambda \in [0, 1]$:

$$K_0 = \sqrt{\frac{1+\lambda}{2}}\, I, \quad K_1 = \sqrt{\frac{1-\lambda}{2}}\, Z$$

Under $w_i$ storage rounds, the diagonal elements (populations) remain invariant, and only the off-diagonal coherence terms decay exponentially by $\lambda^{w_i}$:

$$\rho_{\text{link}}^{(i)}(w_i) = \begin{pmatrix} 0.5 & 0 & 0 & 0.5\lambda^{w_i} \\ 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 \\ 0.5\lambda^{w_i} & 0 & 0 & 0.5 \end{pmatrix}$$

---

## Circuit & Measurement Protocol

The central hub sequentially stitches together the generated bipartite links into a composite multi-node target state:
1. **SWAP & CNOT Gates:** Local hub qubits undergo dynamic permutation ($\text{SWAP}$) and controlled-NOT operations ($\text{CNOT}$) to entangle adjacent links.
2. **Sequential Spoke Measurement & Feedforward $X$:** Intermediate hub ancillae are projected into computational basis states $\{|0\rangle\langle 0|, |1\rangle\langle 1|\}$. Measurement outcome $b=1$ triggers a feedforward $X$-gate correction on the corresponding target spoke.
3. **Hub Hadamard & Feedforward $Z$:** A Hadamard gate $H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$ is applied to the remaining central hub qubit. Computational basis projection and classical feedforward condition an active $Z$-gate phase correction on qubit $0$.
4. **Subsystem Reduction:** Measured auxiliary qubits are projected and traced out to yield the final target state $\rho_{\text{final}}$.

---

## Dependencies & Setup

Ensure `primaryfn.py` (which provides `Q.Pauli` and `Q.Bell`) is located in the working directory.

```bash
pip install numpy scipy
---

## Execution Guide

Run the simulation script via standard Python CLI:

```bash
python rho_piece_with_dephasing.py
### Interactive Inputs Prompt:

```text
enter the no. of links : 3
enter the strength of dephasing parameter : 0.95
enter the round in which the link no. 1 is generated : 1
enter the round in which the link no. 2 is generated : 4
enter the round in which the link no. 3 is generated : 2
```

### Terminal Output:

```text
rounds in which links are generated : [1, 4, 2]
waiting time for each link : [3, 0, 2]

rho : 
[[0.5   +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.3869+0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j]
 [0.3869+0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.    +0.j 0.5   +0.j]]
```

*(Note: Populations remain $0.5$ on $|000\rangle\langle 000|$ and $|111\rangle\langle 111|$; only coherences scale by $\lambda^{\sum w_i} = 0.95^5 \approx 0.7738 \implies 0.5 \times 0.7738 \approx 0.3869$.)*

---
## Mathematical Operator Verification

| Operation | Matrix Representation / Formula | Protocol Target |
| :--- | :--- | :--- |
| **Initial Link** | $\vert\Phi^+\rangle = \frac{1}{\sqrt{2}}(\vert 00\rangle + \vert 11\rangle)$ | Maximally entangled Bell pair |
| **SWAP** | $\frac{1}{2}(I \otimes I + X \otimes X + Y \otimes Y + Z \otimes Z)$ | Hub subsystem spatial realignment |
| **CNOT** | $\vert 0\rangle\langle 0\vert \otimes I + \vert 1\rangle\langle 1\vert \otimes X$ | Entanglement routing |
| **Kraus Operators** | $K_0 = \sqrt{\frac{1+\lambda}{2}}I, \; K_1 = \sqrt{\frac{1-\lambda}{2}}Z$ | Pure single-axis dephasing in memory |
| **$X$-Correction** | $X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ | Bit-flip recovery from ancilla measurement |
| **$Z$-Correction** | $Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$ | Phase-flip recovery from central measurement |
 ---

## License

This project is licensed under the MIT License.