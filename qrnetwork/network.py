import numpy as np
from . import qteleportation
from . import primaryfn
from sympy import Matrix
import warnings
# Change the default warning format
def custom_warning_format(message, category, filename, lineno, line=None):
    return f"⚠️ {message}\n" # Just return warn message not category, filename, etc.
warnings.formatwarning = custom_warning_format
# Bell bases
bell_states = [primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.phi_minus, 
               primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.psi_minus]
# Possible Bell pairs for swap
swap_pairs = [np.kron(primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.phi_plus),
              np.kron(primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.phi_minus),
              np.kron(primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.psi_plus),
              np.kron(primaryfn.Q.Bell.phi_plus, primaryfn.Q.Bell.psi_minus),
              np.kron(primaryfn.Q.Bell.phi_minus, primaryfn.Q.Bell.phi_plus),
              np.kron(primaryfn.Q.Bell.phi_minus, primaryfn.Q.Bell.phi_minus),
              np.kron(primaryfn.Q.Bell.phi_minus, primaryfn.Q.Bell.psi_plus),
              np.kron(primaryfn.Q.Bell.phi_minus, primaryfn.Q.Bell.psi_minus),
              np.kron(primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.phi_plus),
              np.kron(primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.phi_minus),
              np.kron(primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.psi_plus),
              np.kron(primaryfn.Q.Bell.psi_plus, primaryfn.Q.Bell.psi_minus),
              np.kron(primaryfn.Q.Bell.psi_minus, primaryfn.Q.Bell.phi_plus),
              np.kron(primaryfn.Q.Bell.psi_minus, primaryfn.Q.Bell.phi_minus),
              np.kron(primaryfn.Q.Bell.psi_minus, primaryfn.Q.Bell.psi_plus),
              np.kron(primaryfn.Q.Bell.psi_minus, primaryfn.Q.Bell.psi_minus)]
swap_pairs_matrix = [primaryfn.Qp(b).op() for b in swap_pairs]
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

# def dephasing_coeff(T_p, T_dp, L):
#     c = 2 * 10**8  # speed of light in optical fiber (m/s)
#     t = T_p + 2*L/c
#     return (1 - np.exp(-t / T_dp)) / 2
def dephasing_coeff(T_p, T_dp, L):
    """
    Calculate the dephasing probability.

    Parameters
    ----------
    T_p : float
        Entanglement-generation time in seconds.
    T_dp : float
        Dephasing time in seconds.
    L : float
        Fiber length in kilometres.

    Returns
    -------
    float
        Dephasing probability p_deph.
    """
    if L < 0:
        raise ValueError("Fiber length L cannot be negative.")

    if T_p < 0:
        raise ValueError("Generation time T_p cannot be negative.")

    if T_dp <= 0:
        raise ValueError("Dephasing time T_dp must be positive.")

    c = 2 * 10**8  # Speed of light in optical fiber, m/s

    # Convert the fiber length from km to m.
    L_m = 1000 * L

    # Generation time + round-trip propagation time.
    t = T_p + 2 * L_m / c

    # Repository dephasing model.
    p_deph = (1 - np.exp(-t / T_dp)) / 2

    return p_deph


def clicking_coeff(eta, p_d):
    eta_eff = 1 - (1 - eta) * (1 - p_d)**2
    return (eta * (1 - p_d)) / eta_eff

def amp_damp_kraus(gamma):
    K0 = np.array([[1, 0],
                   [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)],
                   [0, 0]], dtype=complex)
    return [K0,K1]


class eswap:
    def __init__(self, node1, node2, tol=1e-10):
        self.qubits = [node1, node2]
        self.tol = tol

    def ket(self):
        full_state = np.kron(self.qubits[0], self.qubits[1])
        fidelities = [primaryfn.Qp(full_state, c).fid() for c in swap_pairs]
        j = int(np.argmax(fidelities))
        results = []
        for i, M in enumerate(bell_states):
            correction = pauli_corrections[j][i]
            opr = np.kron(np.kron(np.eye(2), primaryfn.Q(M).d()),correction) # Note first and last qubit give the desired state.
            post_meas = opr @ full_state
            prob = round(np.real((primaryfn.Qp(post_meas).ip()).item()),2)
            norm = np.sqrt(prob)
            if norm == 0:
                continue
            obtained_state = post_meas / norm
            fidelity = primaryfn.Qp(primaryfn.Q.Bell.phi_plus, obtained_state).fid()
            results.append({"measurement_outcome": f"Bell-{i+1}",
                            "probability": prob,
                            "fidelity": fidelity,
                            "obtained_entangled_state": obtained_state
                                })
        return results
    def density(self):
        full_state = np.kron(self.qubits[0], self.qubits[1])
        fidelities = [primaryfn.Qp(full_state, c).fid() for c in swap_pairs_matrix]
        j = int(np.argmax(fidelities))
        results = []
        for i, M in enumerate(bell_states):
            correction = pauli_corrections[j][i]
            opr = np.kron(np.kron(np.eye(2), primaryfn.Q(M).d()),correction)
            post_meas = opr @ full_state @ primaryfn.Q(opr).d() # @ is not allowed in our Qstate
            norm = np.trace(post_meas)
            prob = round(float(np.real(norm)), 2)
            if norm == 0:
                continue
            obtained_state = post_meas / norm
            # enforce Hermiticity & normalization
            obtained_state = (obtained_state + primaryfn.Q(obtained_state).d()) / 2
            obtained_state = obtained_state / np.trace(obtained_state)
            fidelity = primaryfn.Qp(desired_state, obtained_state).fid()
            results.append({"measurement_outcome": f"Bell-{i+1}",
                            "probability": prob,
                            "fidelity": fidelity,
                            "obtained_entangled_state": obtained_state
                                })
        return results
    def noise(self, L, T_p, T_dp, eta, p_d, loss=None): #L: Fiber length, T_p: Entanglement generation time, 
        # T_dp: Depahsing time, eta: Channel efficiency, p_d: Dark count probability
        rhoin = np.kron(self.qubits[0], self.qubits[1])
        # --- Amplitude damping ---
        if loss is not None:
            gamma = 1 - channel_efficiency(L, loss=loss)
        else:
            gamma = 1 - channel_efficiency(L)
        K = amp_damp_kraus(gamma)
        kraus_op_2q = [np.kron(np.kron(np.kron(np.eye(2), k1), k2), np.eye(2))
                       for k1 in K for k2 in K]
        rho1 = sum(primaryfn.Q(K) @ rhoin @ primaryfn.Q(K).d() for K in kraus_op_2q) 
        rho1 = rho1 / np.trace(rho1)
        # --- Dephasing ---
        lam_t = dephasing_coeff(T_p, T_dp, L)
        # For 2nd qubit
        lam_t_coeff2 = np.kron( np.kron(np.eye(2),primaryfn.Q.Pauli.Z), np.eye(4))
        rho2a = (1 - lam_t) * rho1 + lam_t * (lam_t_coeff2 @ rho1 @ primaryfn.Q(lam_t_coeff2).d())
        rho2b = rho2a / np.trace(rho2a)
        # For 3rd qubit
        lam_t_coeff3 = np.kron( np.kron(np.eye(4),primaryfn.Q.Pauli.Z), np.eye(2))
        rho2c = (1 - lam_t) * rho2b + lam_t * (lam_t_coeff3 @ rho2b @ primaryfn.Q(lam_t_coeff3).d())
        rho2 = rho2c / np.trace(rho2c)
        # --- Detector noise (clicking) ---
        alpha = clicking_coeff(eta, p_d)
        # alpha_coeff1 = alpha * np.eye(16)
        # alpha_coeff2 = ((1 - alpha) / 2) * np.eye(16)
        rho3 = alpha * rho2 + \
               ((1 - alpha) / 2)* rho2
        rho3 = rho3 / np.trace(rho3)
        # --- Fidelity with expected channels ---
        fidelities = [primaryfn.Qp(rho3, c).fid() for c in swap_pairs_matrix]
        j = int(np.argmax(fidelities))
        # --- Measurement and correction ---
        results = []
        for i, M in enumerate(bell_states):
            correction = pauli_corrections[j][i]
            opr = np.kron(np.kron(np.eye(2), primaryfn.Q(M).d()),correction)
            post_meas = opr @ rho3 @ primaryfn.Q(opr).d()
            norm = np.trace(post_meas)
            prob = round(float(np.real(norm)), 2)
            if norm == 0:
                continue
            obtained_state = post_meas / norm
            # enforce Hermiticity & normalization
            obtained_state = (obtained_state + primaryfn.Q(obtained_state).d()) / 2
            obtained_state = obtained_state / np.trace(obtained_state)
            fidelity = primaryfn.Qp(desired_state, obtained_state).fid()
            results.append({"measurement_outcome": f"Bell-{i+1}",
                            "probability": prob,
                            "fidelity": fidelity,
                            "obtained_entangled_state": obtained_state
                                })
        return results

# class QRep:
#     def __init__(self,state_shared,tol=1e-10):
#         self.state_shared = state_shared
#         self.tol = tol
#         self.noise_params = None
#     def noise(self, L, T_p, T_dp, eta, p_d, loss=None):
#         """Enable noisy swapping with given parameters"""
#         self.noise_params = {"L": L, "T_p": T_p, "T_dp": T_dp, "eta": eta, "p_d": p_d, "loss": loss}
#         return self

class QRep:
    def __init__(self, state_shared=None, tol=1e-10):
        self.state_shared = state_shared
        self.tol = tol
        self.noise_params = None

    def noise(self, L, T_p, T_dp, eta, p_d, loss=None):
        """
        Enable the repository noise configuration.

        L     : fiber length in km
        T_p   : generation-time contribution in seconds
        T_dp  : dephasing time in seconds
        eta   : channel-efficiency parameter
        p_d   : dark-count probability
        loss  : optional fiber loss in dB/km
        """
        if L < 0:
            raise ValueError("Fiber length L cannot be negative.")

        if T_p < 0:
            raise ValueError("Generation time T_p cannot be negative.")

        if T_dp <= 0:
            raise ValueError("Dephasing time T_dp must be positive.")

        if not 0 <= eta <= 1:
            raise ValueError("eta must be between 0 and 1.")

        if not 0 <= p_d <= 1:
            raise ValueError("p_d must be between 0 and 1.")

        self.noise_params = {
            "L": L,
            "T_p": T_p,
            "T_dp": T_dp,
            "eta": eta,
            "p_d": p_d,
            "loss": loss,
        }

        return self

    def Star(
        self,
        link,
        protocol="factory",
        rounds=None,
        verbose=False,
    ):
        """
        Run the star-network protocol.

        No noise:
            QRep().Star(link=3)

        With noise:
            QRep().noise(...).Star(link=3)

        protocol:
            "factory" or "piecemaker"
        """
        from .StarProtocol import StarProtocol

        if not isinstance(link, int) or isinstance(link, bool) or link < 2:
            raise ValueError("link must be an integer greater than or equal to 2.")

        if self.noise_params is None:
            noise = False
            Lambda = None

        else:
            noise = True

            L = self.noise_params["L"]
            T_p = self.noise_params["T_p"]
            T_dp = self.noise_params["T_dp"]

            p_deph = dephasing_coeff(T_p, T_dp, L)
            Lambda = 1 - 2 * p_deph

        protocol = protocol.lower()

        if protocol == "factory":
            return StarProtocol.factory(
                link=link,
                noise=noise,
                Lambda=Lambda,
                rounds=rounds,
                verbose=verbose,
            )

        elif protocol == "piecemaker":
            return StarProtocol.piecemaker(
                link=link,
                noise=noise,
                Lambda=Lambda,
                rounds=rounds,
                verbose=verbose,
            )

        else:
            raise ValueError(
                "protocol must be 'factory' or 'piecemaker'."
            )
    def linear(self):
        #---noisy case---
        if self.state_shared is None:
            raise ValueError(
                "Provide shared entangled states: QRep(state_shared).linear()"
            )
        if self.noise_params is not None:
            L, T_p, T_dp, eta, p_d, loss = (
                self.noise_params["L"],
                self.noise_params["T_p"],
                self.noise_params["T_dp"],
                self.noise_params["eta"],
                self.noise_params["p_d"],
                self.noise_params["loss"],
            )

            if all([primaryfn.Is(state).ket() for state in self.state_shared]):
                raise ValueError("Noise model requires density matrices, not kets.")

            if len(self.state_shared) == 1:
                raise ValueError("The shared entangled state should be greater than two.")
            elif len(self.state_shared) == 2:
                if loss is not None:
                    return eswap(self.state_shared[0], self.state_shared[1]).noise(L, T_p, T_dp, eta, p_d, loss)
                else:
                    # Raise a warning
                    # print("Warning: By default loss in fiber is taken as 0.2 dB/km") 
                    warnings.warn("By default loss in fiber is taken as 0.2 dB/km", UserWarning)
                    return eswap(self.state_shared[0], self.state_shared[1]).noise(L, T_p, T_dp, eta, p_d)
            else:
                current_state = self.state_shared[0]
                for i in range(1, len(self.state_shared)):
                    if loss is not None:
                        results = eswap(current_state, self.state_shared[i]).noise(L, T_p, T_dp, eta, p_d, loss)
                    else:
                        # Raise a warning
                        # print(" Warning: By default loss in fiber is taken as 0.2 dB/km.")
                        # With print command warning prints multiple times depending on loops size.
                        warnings.warn("By default loss in fiber is taken as 0.2 dB/km", UserWarning)
                        results = eswap(current_state, self.state_shared[i]).noise(L, T_p, T_dp, eta, p_d)
                    current_state = results[0]["obtained_entangled_state"]
                return results
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