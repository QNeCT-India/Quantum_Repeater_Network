import numpy as np
from .primaryfn import Q, Qp, fold

# ============================================================
# Predefined Common States and Operators
# ============================================================
zero = Q.basis(2, 0)
one = Q.basis(2, 1)
base = [zero, one]

II, XX, YY, ZZ = Q.Pauli.I, Q.Pauli.X, Q.Pauli.Y, Q.Pauli.Z

P_00 = Qp(zero, zero).op()
P_11 = Qp(one, one).op()

CNOT = Q.Gate.CNOT
eta = Q.Bell.phi_plus
rho_0 = eta.dm()


def ghz_fidelity(rho):
    """Calculate fidelity with the standard N-qubit GHZ state."""

    rho = rho.state if isinstance(rho, Q) else np.asarray(rho, dtype=complex)

    dim = rho.shape[0]
    n_qubits = int(np.log2(dim))

    if rho.shape != (dim, dim) or 2**n_qubits != dim:
        raise ValueError("rho must be a square density matrix of dimension 2**N.")

    ghz = np.zeros((dim, 1), dtype=complex)
    ghz[0, 0] = 1 / np.sqrt(2)
    ghz[-1, 0] = 1 / np.sqrt(2)

    return float(np.real((ghz.conj().T @ rho @ ghz).item()))


# ============================================================
# Helper Noise Channels
# ============================================================
def dephase_state_2qubit(rho_2qubit, Lambda, steps):
    """
    Apply pure dephasing to the first (hub) qubit of a Bell link.

    Lambda is the single-round coherence factor:
        Lambda = exp(-t / T_dp)

    After 'steps' rounds, coherence is reduced by Lambda**steps.
    """
    if not -1 <= Lambda <= 1:
        raise ValueError("Lambda must lie between -1 and 1.")

    if steps <= 0:
        return rho_2qubit

    K_0 = np.sqrt((1 + Lambda) / 2) * II
    K_1 = np.sqrt((1 - Lambda) / 2) * ZZ

    K0_I = Qp(K_0, II).tp()
    K1_I = Qp(K_1, II).tp()

    for _ in range(steps):
        rho_2qubit = (
            K0_I @ rho_2qubit @ K0_I.d()
            + K1_I @ rho_2qubit @ K1_I.d()
        )

    return rho_2qubit


def dephase_hub_qubit(rho, n_qubits, hub_idx, Lambda, steps):
    """
    Apply pure dephasing to one selected hub qubit in a composite state.
    """
    if not -1 <= Lambda <= 1:
        raise ValueError("Lambda must lie between -1 and 1.")

    if not 0 <= hub_idx < n_qubits:
        raise ValueError("hub_idx is outside the composite state.")

    if steps <= 0:
        return rho

    k0_ops = [II] * n_qubits
    k1_ops = [II] * n_qubits

    k0_ops[hub_idx] = np.sqrt((1 + Lambda) / 2) * II
    k1_ops[hub_idx] = np.sqrt((1 - Lambda) / 2) * ZZ

    K0 = Qp(k0_ops).tp()
    K1 = Qp(k1_ops).tp()

    for _ in range(steps):
        rho = K0 @ rho @ K0.d() + K1 @ rho @ K1.d()

    return rho


# ============================================================
# Protocol Implementations
# ============================================================
class StarProtocol:
    """Encapsulates quantum network entanglement swapping protocols."""

    @staticmethod
    def factory(
        link, noise=False, Lambda=None, rounds=None, verbose=False
    ):
        """Factory protocol for entanglement swapping in a quantum star network.

        Waits for all links to be generated before operations; all links
        accumulate dephasing noise according to w_i = t_max - r_i.
        Links are ordered by earliest arrival round.
        """
        # ----------------------------------------------------
        # 1. Initial State Setup & Ordering
        # ----------------------------------------------------
        N = 2 * link  # total number of qubits
        rho_link = [rho_0.copy() for _ in range(link)]

        # ----------------------------------------------------
        # 2. Dephasing Noise (All links wait for t_max)
        # ----------------------------------------------------
        if noise:
            if Lambda is None:
                raise ValueError(
                    "Parameter 'Lambda' is required when noise=True."
                )
            if rounds is None:
                rounds = [0] * link
            elif len(rounds) != link:
                raise ValueError(
                    f"Length of 'rounds' ({len(rounds)}) must match 'link' ({link})."
                )

            # Sort rounds in ascending order to order links by earliest arrival
            rounds = sorted(rounds)
            t_max = rounds[-1]
            w = [t_max - r for r in rounds]

            if verbose:
                print("rounds in which links are generated :", rounds)
                print("waiting time for each link :", w)

            for i in range(link):
                rho_link[i] = dephase_state_2qubit(rho_link[i], Lambda, w[i])

        # Composite state before gates
        rho = Qp(rho_link).tp()

        # ----------------------------------------------------
        # 3. Entangling CNOT Operations
        # ----------------------------------------------------
        opr1 = [II] * N
        opr1[1] = P_00
        A = Qp(opr1).tp()

        for i in range(2, N, 2):
            if i + 1 < N:
                opr2 = [II] * N
                opr2[1] = P_11
                opr2[i + 1] = XX
                cnot_gate = A + Qp(opr2).tp()
                rho = cnot_gate @ rho @ cnot_gate.d()

        # ----------------------------------------------------
        # 4. Spoke Ancilla Measurements & Feedforward X Corrections
        # ----------------------------------------------------
        t = [j + 1 for j in range(2, N, 2) if j + 1 < N]

        for step_idx, qubit_idx in enumerate(t):
            m1 = [II] * N
            m2 = [II] * N
            m1[qubit_idx] = P_00
            m2[qubit_idx] = P_11
            M_0 = Qp(m1).tp()
            M_1 = Qp(m2).tp()

            p_0 = np.real((M_0 @ rho).tr())
            p_1 = np.real((M_1 @ rho).tr())
            p_sum = p_0 + p_1
            prob = [p_0 / p_sum, p_1 / p_sum]

            outcome = np.random.choice(["0", "1"], p=prob)
            if verbose:
                print(f"Measurement outcome of q{qubit_idx} qubit : {outcome}")

            if outcome == "0":
                rho = (M_0 @ rho @ M_0.d()) / prob[0]
            else:
                rho = (M_1 @ rho @ M_1.d()) / prob[1]

            if int(outcome) == 1:
                x_gate_ops = [II] * N
                x_gate_ops[qubit_idx - 1] = XX
                X_m = Qp(x_gate_ops).tp()
                rho = X_m @ rho @ X_m.d()

        # ----------------------------------------------------
        # 5. Hub Hadamard, Measurement & Feedforward Z Correction
        # ----------------------------------------------------
        h = Q.Gate.H
        H_ops = [II] * N
        H_ops[1] = h
        H = Qp(H_ops).tp()
        rho = H @ rho @ H.d()

        z1_ops = [II] * N
        z2_ops = [II] * N
        z1_ops[1] = P_00
        z2_ops[1] = P_11
        z1 = Qp(z1_ops).tp()
        z2 = Qp(z2_ops).tp()

        p0_q1 = np.real((z1 @ rho).tr())
        p1_q1 = np.real((z2 @ rho).tr())
        prob_q1 = np.array([p0_q1, p1_q1])
        prob_q1 = prob_q1 / np.sum(prob_q1)

        outcome_q1 = np.random.choice(["0", "1"], p=prob_q1)
        if verbose:
            print("Measurement outcome of q1 qubit :", outcome_q1)

        if outcome_q1 == "0":
            rho = (z1 @ rho @ z1.d()) / prob_q1[0]
        else:
            rho = (z2 @ rho @ z2.d()) / prob_q1[1]

        if int(outcome_q1) == 1:
            z_ops = [II] * N
            z_ops[0] = ZZ
            Z_gate = Qp(z_ops).tp()
            rho = Z_gate @ rho @ Z_gate.d()

        # ----------------------------------------------------
        # 6. Partial Trace
        # ----------------------------------------------------
        trace_qubits = set([1] + t)
        rho_final = rho.ptr(trace_qubits)
        F = ghz_fidelity(rho_final)
        return rho_final, f"fidelity = {F:.15f}"

    @staticmethod
    def piecemaker(
        link, noise=False, Lambda=None, rounds=None, verbose=False
    ):
        """PieceMaker protocol for sequential quantum entanglement swapping.

        Links arrive in chronological order based on sorted generation rounds.
        Only the central hub qubit in memory incurs dephasing during inter-arrival waiting periods:
        (1) Link 1 waits for Link 2 (w_1 = r_{(1)} - r_{(0)} rounds).
        (2) The fused state waits for each incoming link k+1 (w_k = r_{(k)} - r_{(k-1)} rounds).
        """
        # ----------------------------------------------------
        # 1. Initial State Setup & Validation
        # ----------------------------------------------------
        N = 2 * link  # total number of qubits
        rho_link = [rho_0.copy() for _ in range(link)]

        if noise:
            if Lambda is None:
                raise ValueError(
                    "Parameter 'Lambda' is required when noise=True."
                )
            if rounds is None:
                rounds = [0] * link
            elif len(rounds) != link:
                raise ValueError(
                    f"Length of 'rounds' ({len(rounds)}) must match 'link' ({link})."
                )

            # Sort rounds in ascending order: earliest link arrives first
            rounds = sorted(rounds)

            # Step 1: Link 1 waits in memory until Link 2 arrives
            w_initial = rounds[1] - rounds[0]
            if verbose:
                print("rounds in which links are generated :", rounds)
                print(f"waiting time for 1st link before 1st fusion : {w_initial}")

            rho_link[0] = dephase_state_2qubit(rho_link[0], Lambda, w_initial)

        a = [rho_link[k] for k in range(1, len(rho_link))]

        # ----------------------------------------------------
        # 2. Sequential Swapping & Ancilla Measurements
        # ----------------------------------------------------
        rho = rho_link[0]
        d = 0
        e = 2

        for i in range(N - 1):
            dim = 2 * (i + 2) - d
            if dim <= N - d:
                rho = Qp(rho, a[i]).tp()

                # SWAP gate using general SWAP
                P = Q.SWAP(dim, dim - 3, dim - 2)
                rho = P @ rho @ P.d()

                # CNOT gate
                c = [II] * (dim - 1)
                c[-1] = CNOT
                Cx = Qp(c).tp()
                rho = Cx @ rho @ Cx.d()

                # Measurement operators
                m_0 = [II] * dim
                m_0[-1] = P_00
                M_0 = Qp(m_0).tp()

                m_1 = [II] * dim
                m_1[-1] = P_11
                M_1 = Qp(m_1).tp()

                p_0 = np.real((M_0 @ rho).tr())
                p_1 = np.real((M_1 @ rho).tr())
                p_sum = p_0 + p_1
                prob = [p_0 / p_sum, p_1 / p_sum]

                outcome = np.random.choice(["0", "1"], p=prob)
                if verbose:
                    print(
                        f"Measurement outcome of qubit (step {i + 1}) : {outcome}"
                    )

                if outcome == "0":
                    rho = (M_0 @ rho @ M_0.d()) / prob[0]
                else:
                    rho = (M_1 @ rho @ M_1.d()) / prob[1]

                # Feedforward X gate
                b_val = int(outcome)
                if b_val == 1:
                    X_m = [II] * dim
                    X_m[-3] = XX
                    X_m = Qp(X_m).tp()
                    rho = X_m @ rho @ X_m.d()

                # Subspace projection (exclude measured qubit and correct dims)
                M = [II] * dim
                M[-1] = base[b_val].d()
                M = Qp(M).tp()
                M.dims = [[2] * (dim - 1), [2] * dim]
                rho = M @ rho @ M.d()

                d = i + 1
                e = dim - 1

                # ----------------------------------------------------
                # Sequential Noise on Central Hub Qubit
                # ----------------------------------------------------
                # The central hub qubit lives at index e - 1.
                # If another link arrives next, the hub qubit waits until that link arrives.
                if noise and (i + 1 < link - 1):
                    next_link_idx = i + 2  # 0-indexed link number arriving next
                    curr_link_idx = i + 1  # link number that just completed fusion
                    w_step = rounds[next_link_idx] - rounds[curr_link_idx]
                    if verbose and w_step > 0:
                        print(
                            f"waiting time for hub qubit before link {next_link_idx + 1} arrives: {w_step}"
                        )
                    rho = dephase_hub_qubit(
                        rho=rho,
                        n_qubits=e,
                        hub_idx=e - 1,
                        Lambda=Lambda,
                        steps=w_step,
                    )

        # ----------------------------------------------------
        # 3. Central Hub Hadamard & Measurement
        # ----------------------------------------------------
        H_gate_single = Q.Gate.H
        H = [II] * e
        H[-1] = H_gate_single
        H_gate = Qp(H).tp()
        rho = H_gate @ rho @ H_gate.d()

        m1 = [II] * e
        m1[-1] = P_00
        M_0_q2 = Qp(m1).tp()

        m2 = [II] * e
        m2[-1] = P_11
        M_1_q2 = Qp(m2).tp()

        p_0 = np.real((M_0_q2 @ rho).tr())
        p_1 = np.real((M_1_q2 @ rho).tr())
        p_sum = p_0 + p_1
        prob_q2 = [p_0 / p_sum, p_1 / p_sum]

        outcome_q2 = np.random.choice(["0", "1"], p=prob_q2)
        if verbose:
            print("Measurement outcome of q2 qubit :", outcome_q2)

        if outcome_q2 == "0":
            rho = (M_0_q2 @ rho @ M_0_q2.d()) / prob_q2[0]
        else:
            rho = (M_1_q2 @ rho @ M_1_q2.d()) / prob_q2[1]

        # Feedforward Z gate on 1st qubit
        b2 = int(outcome_q2)
        if b2 == 1:
            Z1_m = [II] * e
            Z1_m[0] = ZZ
            Z1 = Qp(Z1_m).tp()
            rho = Z1 @ rho @ Z1.d()

        # Subspace projection (exclude measured central qubit and correct dims)
        M_final = [II] * e
        M_final[-1] = base[b2].d()
        M_final = Qp(M_final).tp()
        M_final.dims = [[2] * (e - 1), [2] * e]
        rho = M_final @ rho @ M_final.d()

        F = ghz_fidelity(rho)
        return rho, f"fidelity = {F:.15f}"


# Convenience top-level instances / functions:
protocol = StarProtocol()
factory_protocol = StarProtocol.factory
piecemaker_protocol = StarProtocol.piecemaker