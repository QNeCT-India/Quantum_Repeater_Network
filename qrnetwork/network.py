from __future__ import annotations
import numpy as np
from . import qteleportation
from . import primaryfn
from . import Q
from sympy import Matrix
import warnings
from dataclasses import dataclass, field
from enum import Enum, auto
# Change the default warning format
def custom_warning_format(message, category, filename, lineno, line=None):
    return f"⚠️ {message}\n" # Just return warn message not category, filename, etc.
warnings.formatwarning = custom_warning_format
# Bell bases
bell_states = [primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.phi_minus, 
               primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.psi_minus]
Qp = primaryfn.Qp
# Possible Bell pairs for swap: index 4*a + b  <->  (Bell_a, Bell_b)
swap_pairs = [Qp(a, b).tp() for a in bell_states for b in bell_states]
swap_pairs_matrix = [Qp(b).op() for b in swap_pairs]
# We want to obtain the desired state (phi_plus) after each swap.
desired_state = primaryfn.Q(primaryfn.Q.Bell.phi_plus).dm()
# desired_state = np.outer(qteleportation.Bell.phi_plus,qteleportation.Bell.phi_plus.conj())

# Pauli corrections tables to get phi_plus after swap.
pauli_corrections = [
    [primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y],
    [primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X],
    [primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z],
    [1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I],
    [primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X],
    [primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y],
    [1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I],
    [primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z],
    [primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z],
    [1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I],
    [primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y],
    [primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X],
    [1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I],
    [primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z],
    [primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.I, 1j*primaryfn.Q.Pauli.Y, primaryfn.Q.Pauli.X],
    [primaryfn.Q.Pauli.I, primaryfn.Q.Pauli.Z, primaryfn.Q.Pauli.X, 1j*primaryfn.Q.Pauli.Y]
]
def channel_efficiency(L, L_att=22, loss=None):
    if loss is not None:
        L_att = 10 * np.log10(np.e) / loss   # compute from loss in dB/km
    return np.exp(-L / L_att)

def dephasing_coeff(T_p, T_dp, L):
    c = 2 * 10**8  # speed of light in optical fiber (m/s)
    t = T_p + 2*L/c
    # t = T_p + 2*(L*1e3)/c          # FIX: L is in km -> metres
    return (1 - np.exp(-t / T_dp)) / 2

# def clicking_coeff(eta_c, eta_d, p_d):
#     arrive = eta_c 
#     no_arrive = 1- eta_c
#     click = arrive * eta_d * (1-p_d)+ no_arrive * p_d
#     no_click = no_arrive * (1 - p_d)
#     eta_eff = click + no_click
#     right_click = arrive * eta_d * (1-p_d)
#     # eta_eff = arrive * eta_d * (1 - p_d) + left * p_d 
#     return right_click / eta_eff

# def clicking_coeff(eta, p_d):
#     eta_eff = 1 - (1 - eta) * (1 - p_d)**2
#     # eta_eff = 1 - (1 - eta) * (1 - p_d) 
#     return (eta * (1 - p_d)) / eta_eff

def clicking_coeff(eta_c, eta_d, p_d):
    eta_eff = 1 - (1 - eta_c) * (1 - p_d)**2
    # eta_eff = 1 - (1 - eta) * (1 - p_d) 
    return (eta_c * eta_d *(1 - p_d)) / eta_eff

def amp_damp_kraus(gamma):
    K0 = np.array([[1, 0],
                   [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)],
                   [0, 0]], dtype=complex)
    return [K0,K1]

# ---- Noise helpers: built only from Q / Qp operations (ptr, expand_mixed, tp, d, @, +, scalar *) ----
_I, _X, _Y, _Z = Q.Pauli.I, Q.Pauli.X, Q.Pauli.Y, Q.Pauli.Z

def dark_count(rho, alpha):
    """Dark counts on the receiving (2nd) qubit: alpha*rho + (1-alpha)*tr_2(rho) (x) I/2."""
    rho = Q(rho)
    if alpha >= 1:
        return rho
    mixed = rho.ptr([1]).expand_mixed([0], 2)          # tr_2(rho) (x) I/2
    return alpha * rho + (1 - alpha) * mixed

def dephase(rho, qubit, x):
    """Z-dephasing on `qubit` (0 or 1) of a 2-qubit state; x = exp(-t/T_dp), lambda = (1-x)/2."""
    rho = Q(rho)
    lam = (1 - x) / 2
    if lam == 0:
        return rho
    Zq = Qp(_Z, _I).tp() if qubit == 0 else Qp(_I, _Z).tp()
    return (1 - lam) * rho + lam * (Zq @ rho @ Zq.d())

def bsm_noise(rho4, lam):
    """lam*rho + (1-lam)/4 tr_{12}(rho) (x) 1 on the two measured qubits (qubits 1 and 2 of 4)."""
    rho4 = Q(rho4)
    if lam >= 1:
        return rho4
    mixed = rho4.ptr([1, 2]).expand_mixed([0, 3], 4)   # tr_{12}(rho) (x) I/4
    return lam * rho4 + (1 - lam) * mixed

class eswap:
    """Entanglement swapping of two pairs (qubits 0-1 and 2-3, Bell measurement on qubits 1 and 2).
    The result is always Pauli-corrected towards |phi+> on qubits 0 and 3."""
    def __init__(self, node1, node2, tol=1e-10):
        self.qubits = [node1, node2]
        self.tol = tol

    @staticmethod
    def _nearest_bell(rho):
        """Index of the Bell state with the largest overlap <B|rho|B> (works for kets and density matrices)."""
        rho = Q(rho)
        if rho.state.shape[1] == 1:                                      # ket
            return int(np.argmax([abs((M.d() @ rho).item()) for M in bell_states]))
        return int(np.argmax([np.real((M.d() @ rho @ M).item()) for M in bell_states]))

    def ket(self):
        full_state = Qp(*self.qubits).tp()
        fidelities = [Qp(full_state, c).fid() for c in swap_pairs]
        j = int(np.argmax(fidelities))
        results = []
        for i, M in enumerate(bell_states):
            correction = pauli_corrections[j][i]
            opr = Qp(Q.Pauli.I, M.d(), correction).tp()     # I (x) <Bell_i| (x) correction; first and last qubit remain
            post_meas = opr @ full_state
            p = float(np.real((Qp(post_meas).ip()).item()))   # exact probability
            if p < self.tol:
                continue
            obtained_state = post_meas / np.sqrt(p)           # normalised with the exact probability
            fidelity = Qp(Q.Bell.phi_plus, obtained_state).fid()
            results.append({"measurement_outcome": f"Bell-{i+1}",
                            "probability": round(p, 2),
                            "fidelity": fidelity,
                            "obtained_entangled_state": obtained_state
                                })
        return results

    def density(self):
        full_state = Qp(*self.qubits).tp()
        a, b = self._nearest_bell(self.qubits[0]), self._nearest_bell(self.qubits[1])
        j = 4 * a + b                                         # same index as argmax over swap_pairs_matrix
        results = []
        for i, M in enumerate(bell_states):
            correction = pauli_corrections[j][i]
            opr = Qp(Q.Pauli.I, M.d(), correction).tp()
            post_meas = opr @ full_state @ opr.d()
            norm = float(np.real(post_meas.tr()))
            if norm < self.tol:
                continue
            obtained_state = post_meas / norm
            # enforce Hermiticity & normalization
            obtained_state = (obtained_state + obtained_state.d()) / 2
            obtained_state = obtained_state / float(np.real(obtained_state.tr()))
            fidelity = Qp(desired_state, obtained_state).fid()
            results.append({"measurement_outcome": f"Bell-{i+1}",
                            "probability": round(norm, 2),
                            "fidelity": fidelity,
                            "obtained_entangled_state": obtained_state
                                })
        return results

    def noise(self, lam=1.0):
        """Swap of two 2-qubit density matrices with an optionally imperfect Bell measurement.

        lam : Bell-measurement ideality (1 = perfect), see bsm_noise().
        Returns (outcomes, rho_avg):
          outcomes - list of (probability, Pauli-corrected 4x4 state of qubits 0 and 3), one per BSM outcome
          rho_avg  - outcome-averaged corrected state (use this as the input of the next swap in a chain)
        """
        a, b = self._nearest_bell(self.qubits[0]), self._nearest_bell(self.qubits[1])
        rho4 = bsm_noise(Qp(*self.qubits).tp(), lam)
        outcomes, avg = [], Q(np.zeros((4, 4)))
        for k, M in enumerate(bell_states):
            opr = Qp(Q.Pauli.I, M.d(), pauli_corrections[4 * a + b][k]).tp()   # I (x) <Bell_k| (x) correction
            post = opr @ rho4 @ opr.d()
            p = float(np.real(post.tr()))
            if p < self.tol:
                continue
            cond = post / p
            cond = (cond + cond.d()) / 2
            outcomes.append((p, cond))
            avg = avg + p * cond
        return outcomes, avg / float(np.real(avg.tr()))

class QRep:
    def __init__(self,state_shared,tol=1e-10):
        self.state_shared = state_shared
        self.tol = tol
        self.noise_params = None
    def noise(self, L, T_p, T_dp, eta, p_d, loss=None):
        """Noisy swapping; all links are generated at the same time (no waiting-time dephasing), ideal BSM.

        L    : link length (km)
        T_p  : pair preparation time (s)  - accepted but unused here (it only matters for timing)
        T_dp : memory dephasing time (s)
        eta  : detection / coupling efficiency (multiplies the fibre transmission)
        p_d  : dark-count probability per detection window
        loss : fibre loss in dB/km (None -> attenuation length 22 km, i.e. ~0.2 dB/km)
        """
        self.noise_params = {"L": L, "T_p": T_p, "T_dp": T_dp, "eta": eta, "p_d": p_d, "loss": loss}
        return self

    def linear(self):
        #---noisy case---
        if self.noise_params is not None:
            q = self.noise_params
            n = len(self.state_shared)
            if all([primaryfn.Is(state).ket() for state in self.state_shared]):
                raise ValueError("Noise model requires density matrices, not kets.")
            if n == 1:
                raise ValueError("The shared entangled state should be greater than two.")
            if not all(np.abs(primaryfn.Ebit(d)) > self.tol for d in self.state_shared):
                raise ValueError("The shared states are not entangled.")

            c = 2e8                                                    # speed of light in fibre (m/s)
            # identical for every link (equal length, simultaneous generation)
            links = len(self.state_shared)
            L = q["L"]/links                          
            eta_arr = channel_efficiency(L, loss=q["loss"])   # arrival probability per trial
            alpha = clicking_coeff(eta_arr, q["eta"], q["p_d"])
            # alpha = clicking_coeff(eta_arr, q["p_d"])                  # prob. a click is a real photon
            t1 = L * 1e3 / c                                      # one-way fibre time (s); L is in km
            x_src = np.exp(-2 * t1 / q["T_dp"])                        # source-side qubit stored 2d/c
            x_dst = np.exp(-t1 / q["T_dp"])                            # receiving-side qubit stored d/c

            links = []
            for i, rho in enumerate(self.state_shared):
                r = dark_count(rho, alpha)                             # on the received qubit
                if i > 0:                                              # end stations hold no memory
                    r = dephase(r, 0, x_src)
                if i < n - 1:
                    r = dephase(r, 1, x_dst)
                links.append(r)

            current = links[0]
            for i in range(1, n):                                      # ideal BSM, outcome-averaged + Pauli frame
                outcomes, current = eswap(current, links[i]).noise()

            phi = Q.Bell.phi_plus
            return [{"measurement_outcome": f"Bell-{k + 1}",
                     "probability": prob,
                     "fidelity": float(np.real((phi.d() @ cond @ phi).item())),   # <Phi+|rho|Phi+>
                     "obtained_entangled_state": cond}
                    for k, (prob, cond) in enumerate(outcomes)]
        # --- noiseless case ---
        if all([primaryfn.Is(state).ket() for state in self.state_shared]): #Check dimensions
            purity = [primaryfn.Q(c).u() for c in self.state_shared]
            ent_val = [primaryfn.Ebit(d) for d in self.state_shared]
            if all(v >= self.tol for v in ent_val):
                if len(self.state_shared) == 1:
                    raise ValueError("The shared entangled state should be greater than two.")
                elif len(self.state_shared) == 2:
                    output = eswap(self.state_shared[0], self.state_shared[1]).ket()
                    return output
                elif len(self.state_shared) > 2:
                    #measurements = []
                    current_state = self.state_shared[0]
                    for i in range(1, len(self.state_shared)):
                        results = eswap(current_state, self.state_shared[i]).ket()
                        #measurements.append(results)
                        current_state = results[0]["obtained_entangled_state"]
                    return results #measurements
            else:
                raise ValueError("The shared states are not not entangled.")
        elif all([primaryfn.Is(state).square() for state in self.state_shared]):
            purity = [primaryfn.Q(c).u() for c in self.state_shared]
            ent_val = [primaryfn.Ebit(d) for d in self.state_shared]
            if all(np.abs(c) > self.tol for c in ent_val):
                if len(self.state_shared) == 1:
                    raise ValueError("The shared entangled state should be greater than two.")
                elif len(self.state_shared) == 2:
                    output = eswap(self.state_shared[0], self.state_shared[1]).density()
                    return output
                elif len(self.state_shared) > 2:
                    current_state = self.state_shared[0]
                    for i in range(1, len(self.state_shared)):
                        results = eswap(current_state, self.state_shared[i]).density()
                        #measurements.append(results)
                        current_state = results[0]["obtained_entangled_state"]
                    return results #measurements
            else:
                raise ValueError("The shared states are not entangled.")
        else:
            raise ValueError("Incorrect dimensions of the shared state.")


# ---------------------------------------------------------------------------
# Chain Topology & Memory Slots
# ---------------------------------------------------------------------------
class SlotStatus(Enum):
    EMPTY = auto()
    PENDING = auto()
    READY = auto()


@dataclass
class MemorySlot:
    owner_node: Node
    faces_node: Node
    status: SlotStatus = SlotStatus.EMPTY
    link: Link | None = None


@dataclass
class Link:
    rho: Q
    ready_time: float
    left_slot: MemorySlot
    right_slot: MemorySlot

    @property
    def left_node(self) -> Node:
        return self.left_slot.owner_node

    @property
    def right_node(self) -> Node:
        return self.right_slot.owner_node


@dataclass
class Node:
    index: int
    is_end_node: bool
    left_slots: list[MemorySlot] = field(default_factory=list)    #List of parallel 'left memory slots'
    right_slots: list[MemorySlot] = field(default_factory=list)   #List of parallel 'right memory slots'


class RepeaterChain:
    def __init__(self, rep_nodes: int, n_parallel_slots: int):
        if rep_nodes < 1:
            raise ValueError("rep_nodes must be >= 1 (need at least one repeater)")
        if n_parallel_slots < 1:
            raise ValueError("n_parallel_slots must be >= 1")

        self.rep_nodes = rep_nodes
        self.n_parallel_slots = n_parallel_slots
        self.nodes: list[Node] = [Node(index=i, is_end_node=(i == 0 or i == self.rep_nodes + 1)) for i in self.nodes_indices()]
        for i in self.links_indices():
            j = i + 1
            for _ in range(n_parallel_slots):
                ith_mem = MemorySlot(owner_node= self.nodes[i], faces_node= self.nodes[j])
                jth_mem = MemorySlot(owner_node=self.nodes[j], faces_node=self.nodes[i])
                self.nodes[i].right_slots.append(ith_mem)
                self.nodes[j].left_slots.append(jth_mem)

    def nodes_indices(self) -> range:
        return range(self.rep_nodes + 2)

    def repeater_indices(self) -> range:
        return range(1, self.rep_nodes + 1)

    def links_indices(self) -> range:
        return range(self.rep_nodes + 1)