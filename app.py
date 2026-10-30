"""
QNeCT Streamlit GUI - Quantum Network and Communication Toolbox
================================================================
One full-pack simulator. The sidebar picks a topology and a protocol:

    Linear -> Analytical chain   ideal / noisy Bell-pair swapping
    Linear -> ASAP | Last | Nesting     discrete-event RepeaterSimulation
    Star   -> PieceMaker | Factory      StarProtocol (GHZ distribution)

Tabs: Simulation, Plots (sweeps and protocol comparisons), Documentation and
Other Tools (state utilities, entanglement check, teleportation, channel fidelity).

Run with:
    streamlit run app.py
"""

import dataclasses
import warnings

import numpy as np
import pandas as pd
import streamlit as st

# Imports for GUI documentations
import re
from html import escape
from pathlib import Path
import streamlit.components.v1 as components

from qrnetwork import (Q, Qp, Is, Ebit, Teleport, QChannel, eswap, QRep, SimulationConfig, StarConfig, QNeCTSimulator, MAX_STAR_LINKS)


# Setting layout and page title
st.set_page_config(page_title="Quantum Repeater Network Simulator", layout="wide")

# Mappings that maps the chosen labels (e.g., \(\vert{}\Phi^+\rangle\)) to internal database.
BELL_STATES = {
    "phi_plus": Q.Bell.phi_plus,
    "phi_minus": Q.Bell.phi_minus,
    "psi_plus": Q.Bell.psi_plus,
    "psi_minus": Q.Bell.psi_minus,
}
BELL_LABELS = {
    "Bell State |\u03a6+\u27e9": "phi_plus",
    "Bell State |\u03a6-\u27e9": "phi_minus",
    "Bell State |\u03a8+\u27e9": "psi_plus",
    "Bell State |\u03a8-\u27e9": "psi_minus",
}


# It safely standardizes diverse structural inputs (custom Q wrappers, symbolic SymPy matrices, or basic nested lists)
# down to an explicit, uniform, complex numpy.ndarray layout before it hits display layers.
def to_display_matrix(x):
    """Convert Q / sympy.Matrix / ndarray into a plain complex ndarray."""
    if hasattr(x, "state"):        # Q instance
        return np.asarray(x.state)
    try:
        return np.array(x.tolist(), dtype=complex)   # sympy Matrix
    except AttributeError:
        return np.asarray(x, dtype=complex)


# Converts complex array tensors into a user-friendly Pandas Dataframe. 
# Using np.vectorize translates standard engineering notation (e.g., 0.5+0.2j) into clean text layouts (0.5000+0.2000i) for structured UI rendering.
def matrix_to_dataframe(arr, decimals=4):
    arr = to_display_matrix(arr)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    formatted = np.vectorize(
        lambda z: f"{np.real(z):.{decimals}f}{'+' if np.imag(z) >= 0 else '-'}{abs(np.imag(z)):.{decimals}f}i"
    )(arr)
    return pd.DataFrame(formatted)


# Formats numeric arrays into standard LaTeX \begin{bmatrix} structures. 
# If the imaginary component falls below a decimal threshold, it truncates the term entirely to display a clean real float.
def to_bmatrix_latex(x, decimals=2):
    """Render a ket/density matrix as a LaTeX bmatrix (like the original app)."""
    arr = to_display_matrix(x)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    rows = []
    for row in arr:
        cells = []
        for v in np.atleast_1d(row):
            re, im = float(np.real(v)), float(np.imag(v))
            if abs(im) < 10 ** (-decimals):
                cells.append(f"{re:.{decimals}f}")
            else:
                sign = "+" if im >= 0 else "-"
                cells.append(f"{re:.{decimals}f}{sign}{abs(im):.{decimals}f}i")
        rows.append(" & ".join(cells))
    return r"\begin{bmatrix}" + r" \\ ".join(rows) + r"\end{bmatrix}"

# Generates dynamic vector graphics strings (SVGs) for linear networks.
def draw_topology_svg(n_repeaters, total_distance):
    """
    Build a linear repeater-chain diagram (End A -- R1 -- ... -- End B) as raw
    SVG. SVG is vector graphics, so it stays perfectly sharp at any zoom or
    screen density -- unlike a matplotlib PNG rendered at a fixed pixel size,
    which is what was causing the blurriness.
    """
    n_links = n_repeaters + 1
    n_nodes = n_repeaters + 2
    link_len = total_distance / n_links

    spacing = 140
    margin = 70
    width = spacing * (n_nodes - 1) + 2 * margin
    height = 160
    y = height / 2
    xs = [margin + i * spacing for i in range(n_nodes)]
    labels = ["End A"] + [f"R{i + 1}" for i in range(n_repeaters)] + ["End B"]

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%; height:auto; display:block; font-family:-apple-system,Segoe UI,Roboto,sans-serif;">',
        """
        <defs>
          <radialGradient id="endGrad" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stop-color="#60a5fa"/>
            <stop offset="100%" stop-color="#1d4ed8"/>
          </radialGradient>
          <radialGradient id="dotGrad" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stop-color="#fcd34d"/>
            <stop offset="100%" stop-color="#d97706"/>
          </radialGradient>
        </defs>
        """,
    ]

    # Loops through nodes to draw fiber optic links. It calculates spatial midpoints ((x1 + x2) / 2) to center specific per-link distance labels.
    # Links (lines + per-link distance label)
    for i in range(n_nodes - 1):
        x1, x2 = xs[i], xs[i + 1]
        parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#9ca3af" stroke-width="2.5"/>')
        mid = (x1 + x2) / 2
        parts.append(
            f'<text x="{mid}" y="{y + 26}" text-anchor="middle" font-size="11" fill="#6b7280">{link_len:.1f} km</text>'
        )

    # Renders user nodes as blue spheres (url(#endGrad)) 
    # and active repeater stations as distinct dual-memory white cards containing localized yellow memory wells (url(#dotGrad)).
    for i, (x, label) in enumerate(zip(xs, labels)):
        if i == 0 or i == n_nodes - 1:
            parts.append(f'<circle cx="{x}" cy="{y}" r="20" fill="url(#endGrad)" stroke="#1e3a8a" stroke-width="1.5"/>')
        else:
            parts.append(
                f'<rect x="{x - 28}" y="{y - 20}" width="56" height="40" rx="9" '
                f'fill="#ffffff" stroke="#374151" stroke-width="1.5"/>'
            )
            parts.append(f'<circle cx="{x - 10}" cy="{y}" r="8" fill="url(#dotGrad)"/>')
            parts.append(f'<circle cx="{x + 10}" cy="{y}" r="8" fill="url(#dotGrad)"/>')
        parts.append(
            f'<text x="{x}" y="{y - 34}" text-anchor="middle" font-size="13" font-weight="700" '
            f'fill="#111827">{label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts), n_links

# Drives the Analytical Linear Simulation backend.
def run_repeater_simulation(distance, n_repeaters, bell_key, noise_enabled, T_p_us, T2_ms, eta, p_d, fiber_loss):
    """Core simulation used by the Simulation tab and the Plots sweeps."""
    n_links = n_repeaters + 1
    link_length = distance / n_links
    custom = not isinstance(bell_key, str)      # Bell key OR a 4x4 density matrix
    base_ket = None if custom else BELL_STATES[bell_key]     

    if noise_enabled:
        # shared = [Qp(base_ket).op() for _ in range(n_links)]
        shared = [Q(bell_key) if custom else Qp(base_ket).op() for _ in range(n_links)]
        rep = QRep(shared).noise(L=distance, T_p=T_p_us * 1e-6, T_dp=T2_ms * 1e-3, eta=eta, p_d=p_d, loss=fiber_loss
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = rep.linear()
    else:
        # shared = [base_ket for _ in range(n_links)]
        shared = [Q(bell_key) if custom else base_ket for _ in range(n_links)]
        results = QRep(shared).linear()

    total_p = sum(r["probability"] for r in results) or 1.0
    avg_fidelity = sum(r["probability"] * r["fidelity"] for r in results) / total_p
    best = max(results, key=lambda r: r["probability"])
    return {
        "link_length": link_length,
        "n_links": n_links,
        "results": results,
        "avg_fidelity": avg_fidelity,
        "final_state": best["obtained_entangled_state"],
    }




# Computes the angular coordinates (2π k / N) needed to space out peripheral user nodes in a balanced star pattern around the centralized network hub.
# where k is the index of the current node being placed and N is the total number of links
def draw_star_svg(n_links):
    """Star network diagram: a central hub with `n_links` spoke end-nodes (vector SVG)."""
    size = 360
    cx = cy = size / 2
    radius = 130
    parts = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%; max-width:420px; height:auto; display:block; margin:0 auto; '
        f'font-family:-apple-system,Segoe UI,Roboto,sans-serif;">',
        """
        <defs>
          <radialGradient id="endGradS" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#1d4ed8"/>
          </radialGradient>
          <radialGradient id="hubGradS" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stop-color="#fcd34d"/><stop offset="100%" stop-color="#d97706"/>
          </radialGradient>
        </defs>
        """,
    ]
    pts = []
    for k in range(n_links):
        ang = -np.pi / 2 + 2 * np.pi * k / n_links
        pts.append((cx + radius * np.cos(ang), cy + radius * np.sin(ang)))
    # Connects lines from the center hub to each user node
    for x, y in pts:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#9ca3af" stroke-width="2.5"/>')
    # Hub: one memory dot per link, arranged on a small ring inside the hub box
    ring_r = 12 if n_links <= 3 else 22
    dot_r = 8 if n_links <= 3 else 6
    parts.append(
        f'<rect x="{cx - 38}" y="{cy - 38}" width="76" height="76" rx="12" fill="#ffffff" '
        f'stroke="#374151" stroke-width="1.5"/>'
    )
    for k in range(n_links):
        a = -np.pi / 2 + 2 * np.pi * k / n_links
        parts.append(
            f'<circle cx="{cx + ring_r * np.cos(a):.1f}" cy="{cy + ring_r * np.sin(a):.1f}" '
            f'r="{dot_r}" fill="url(#hubGradS)"/>'
        )
    parts.append(
        f'<text x="{cx}" y="{cy + 54}" text-anchor="middle" font-size="12" font-weight="700" fill="#111827">Hub</text>'
    )
    for i, (x, y) in enumerate(pts):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="18" fill="url(#endGradS)" stroke="#1e3a8a" stroke-width="1.5"/>')
        ty = y - 26 if y < cy else y + 36
        parts.append(
            f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle" font-size="12" font-weight="700" '
            f'fill="#111827">User {i + 1}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# Sanitizes string parameters into clean integer tuples to construct the arrival timeline metrics required by Star topology runs
def parse_rounds(text, n_links):
    """'0, 2, 5' -> (0, 2, 5); raises ValueError with a readable message."""
    try:
        vals = tuple(int(v) for v in text.replace(";", ",").split(",") if v.strip() != "")
    except ValueError:
        raise ValueError("Generation rounds must be whole numbers separated by commas, e.g. 0, 2, 5.")
    if len(vals) != n_links:
        raise ValueError(f"Enter exactly {n_links} generation rounds (got {len(vals)}).")
    if min(vals) < 0:
        raise ValueError("Generation rounds must be >= 0.")
    return vals


def state_to_latex(rho, symbol, max_dim=8, decimals=2):
    """LaTeX bmatrix for small states; None for large ones (caller falls back to a table)."""
    arr = to_display_matrix(rho)
    if arr.shape[0] > max_dim:
        return None
    return f"{symbol} = {to_bmatrix_latex(arr, decimals)}"


def populations_df(rho):
    """Diagonal of a density matrix as a basis-state -> probability table."""
    arr = to_display_matrix(rho)
    n = int(np.log2(arr.shape[0]))
    return pd.DataFrame(
        {"Basis state": [format(i, f"0{n}b") for i in range(arr.shape[0])], "Probability": np.real(np.diag(arr))}
    ).set_index("Basis state")

# Parses user-submitted text fields into custom complex arrays. It replaces standard imaginary indicators (i) 
# with Python-compliant format styles (j) before casting. It also performs trace normalization 
# and validates that the matrix is positive semi-definite to ensure it forms a physically valid density matrix (ρ).
def parse_density_matrix(text, tol=1e-8):
    rows = [r for r in text.strip().splitlines() if r.strip()]
    try:
        arr = np.array(
            [[complex(c.replace(" ", "").replace("i", "j")) for c in r.replace(";", ",").split(",") if c.strip()] for r in rows],
            dtype=complex,
        )
    except ValueError:
        raise ValueError("Could not read the matrix. Use one row per line, entries separated by commas (e.g. 0.5, 0, 0, 0.5).")
    if arr.shape != (4, 4):
        raise ValueError(f"Expected a 4x4 matrix (two qubits per link), got {arr.shape}.")
    if not np.allclose(arr, arr.conj().T, atol=tol):
        raise ValueError("Matrix is not Hermitian (rho must equal its conjugate transpose).")
    tr = np.real(np.trace(arr))
    if tr <= tol:
        raise ValueError("Trace must be positive.")
    note = ""
    if abs(tr - 1) > 1e-6:
        arr = arr / tr
        note = f"Trace was {tr:.4g}; matrix normalised to trace 1."
    if np.min(np.linalg.eigvalsh(arr)) < -1e-8:
        raise ValueError("Matrix is not positive semidefinite (has a negative eigenvalue).")
    return arr, note

def linear_results_df(result):
    return pd.DataFrame(result.links) if result.links else pd.DataFrame(columns=["run", "fidelity", "created_time_s"])



# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.markdown(
    """
    <div style="
        text-align:center;
        padding: 1.2rem 1.5rem 1.1rem 1.5rem;
        margin-bottom: 1.2rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 45%, #3b82f6 100%);
        box-shadow: 0 8px 24px rgba(29, 78, 216, 0.25);
    ">
        <div style="display:flex; align-items:center; justify-content:center; gap:14px;">
            <svg width="46" height="46" viewBox="0 0 46 46" xmlns="http://www.w3.org/2000/svg">
                <circle cx="8" cy="23" r="6" fill="#fcd34d"/>
                <circle cx="38" cy="8" r="6" fill="#fcd34d"/>
                <circle cx="38" cy="38" r="6" fill="#fcd34d"/>
                <line x1="8" y1="23" x2="38" y2="8" stroke="#e5e7eb" stroke-width="2.5"/>
                <line x1="8" y1="23" x2="38" y2="38" stroke="#e5e7eb" stroke-width="2.5"/>
                <line x1="38" y1="8" x2="38" y2="38" stroke="#e5e7eb" stroke-width="2.5" stroke-dasharray="3,3"/>
            </svg>
            <h1 style="
                margin:0;
                color:#ffffff;
                font-size:4.5rem;
                font-weight:600;
                letter-spacing:1px;
                text-shadow: 0 2px 10px rgba(0,0,0,0.15);
            ">QNeCT</h1>
        </div>
        <p style="color:#dbeafe; font-size:2rem; margin:0.5rem 0 0 0; letter-spacing:0.3px;">
            Quantum Network and Communication Toolbox
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)



# ----------------------------------------------------------------------
# Sidebar: Simulation Parameters  (topology -> protocol -> parameters)
# ----------------------------------------------------------------------
simulator = QNeCTSimulator()

LINEAR_ANALYTICAL = "Analytical chain"
LINEAR_PROTOCOLS = {"ASAP": "asap", "Last": "last", "Nesting": "nesting"}
STAR_PROTOCOL_LABELS = {"PieceMaker": "piecemaker", "Factory": "factory"}


# Renders the structural topology selection menu in the sidebar panel
st.sidebar.header("Simulation Parameters")
topology = st.sidebar.selectbox("Topology", ["Linear", "Star"], key="topology")

# Handles parameter inputs for the linear topology model.
if topology == "Linear":
    protocol_label = st.sidebar.selectbox(
        "Protocol",
        [LINEAR_ANALYTICAL] + list(LINEAR_PROTOCOLS.keys()),
        key="linear_protocol",
        help="Analytical: Bell-state chain with optional per-link noise (QRep). "
        "ASAP / Last / Nesting: discrete-event simulation of probabilistic sources, "
        "memories and Bell-state measurements (RepeaterSimulation).",
    )
    mode = "analytical" if protocol_label == LINEAR_ANALYTICAL else "linear"
else:
    protocol_label = st.sidebar.selectbox("Protocol", list(STAR_PROTOCOL_LABELS.keys()), key="star_protocol")
    mode = "star"

# Defaults so every name exists whichever mode is active
distance, n_repeaters, n_links = 100, 3, 3
dist_state_label = list(BELL_LABELS.keys())[0]
noise_enabled, T_p_us, T2_ms, eta, p_d, fiber_loss = False, 1.0, 1.0, 0.90, 1e-8, 0.20
linear_cfg = star_cfg = None
CUSTOM_STATE = "Custom density matrix"
DEFAULT_CUSTOM_RHO = "0.4, 0, 0, 0.4\n0, 0.1, 0, 0\n0, 0, 0.1, 0\n0.4, 0, 0, 0.4"   # Werner, p = 0.8
custom_rho = None
cfg_error = None
runs, seed = 1, None

# ---- Linear (shared) ----
# If the nesting policy is active, it swaps the standard integer slider for a structured select_slider restricted to valid values (\(2^k-1\)).
if topology == "Linear":
    distance = st.sidebar.slider("Total Distance (km)", min_value=1, max_value=1000, value=100, key="distance")
    if mode == "linear" and LINEAR_PROTOCOLS[protocol_label] == "nesting":
        n_repeaters = st.sidebar.select_slider(
            "Number of Repeaters (2^k - 1)", options=[1, 3, 7], value=3, key="n_repeaters_nesting"
        )
    else:
        n_repeaters = st.sidebar.slider("Number of Repeaters", min_value=1, max_value=10, value=3, key="n_repeaters")

# ---- Linear: analytical ----
if mode == "analytical":
    with st.sidebar.expander("Distributed State", expanded=True):
        dist_state_label = st.selectbox(
            "Select Distributed State", list(BELL_LABELS.keys()) + [CUSTOM_STATE], key="dist_state"
        )
        if dist_state_label == CUSTOM_STATE:
            rho_text = st.text_area(
                "Density matrix (4x4, one row per line)", value=DEFAULT_CUSTOM_RHO, height=130,
                key="custom_rho_text",
                help="Entries separated by commas. Complex numbers: 0.5+0.1j. "
                "The same state is distributed over every link.",
            )
            try:
                custom_rho, rho_note = parse_density_matrix(rho_text)
                if rho_note:
                    st.caption(rho_note)
            except ValueError as e:
                cfg_error = str(e)
    dist_key = custom_rho if dist_state_label == CUSTOM_STATE else BELL_LABELS[dist_state_label]

    with st.sidebar.expander("Noise Parameters", expanded=False):
        noise_enabled = st.checkbox("Enable Noise Model", value=False, key="noise_enabled")
        T_p_us = st.number_input(
            "Entanglement Preparation Time (\u00b5s)", min_value=0.0, value=1.00, step=0.1, key="T_p_us"
        )
        T2_ms = st.number_input("Memory Dephasing Time T\u2082 (ms)", min_value=0.001, value=10.00, step=1.0, key="T2_ms")
        eta = st.slider("Detector Efficiency", 0.0, 1.0, 0.90, 0.01, key="eta")
        p_d = st.number_input("Dark Count Probability", min_value=0.0, value=1e-8, format="%.2e", key="p_d")
        fiber_loss = st.number_input("Fiber Loss (dB/km)", min_value=0.01, value=0.20, step=0.01, key="fiber_loss")

# ---- Linear: discrete-event (asap / last / nesting) ----
# Bundles active parameter states directly into a discrete-event SimulationConfig object.
if mode == "linear":
    policy = LINEAR_PROTOCOLS[protocol_label]

    with st.sidebar.expander("Source & Laser", expanded=False):
        source_efficiency = st.number_input(
            "Source efficiency (per photon)", min_value=1e-12, max_value=1.0, value=1e-8, format="%.1e", key="src_eff"
        )
        source_fidelity = st.slider("Source state fidelity", 0.25, 1.0, 0.99, 0.005, key="src_fid")
        laser_pulsed = st.checkbox("Pulsed laser", value=True, key="laser_pulsed")
        laser_power = st.number_input("Average laser power (mW)", min_value=0.0001, value=0.04, format="%.4f", key="laser_p")
        laser_rate = st.number_input("Laser repetition rate (MHz)", min_value=1.0, value=100.0, key="laser_r")
        laser_wl = st.number_input("Laser wavelength (nm)", min_value=100.0, value=405.0, key="laser_wl")

    with st.sidebar.expander("Detector & Fibre", expanded=False):
        det_rate = st.number_input("Detector / clock rate (MHz)", min_value=0.1, value=25.0, key="det_r")
        dark_rate = st.number_input("Dark count rate (Hz)", min_value=0.0, value=100.0, key="dark_r")
        det_window_ns = st.number_input("Detection window (ns)", min_value=0.1, value=8.0, key="det_w")
        att_len = st.number_input("Fibre attenuation length (km)", min_value=1.0, value=22.0, key="att_len")

    with st.sidebar.expander("Memory & BSM", expanded=False):
        dephasing_s = st.number_input("Memory dephasing time (s)", min_value=1e-6, value=0.01, format="%.4f", key="deph_s")
        bsm_fid = st.slider("BSM fidelity", 0.25, 1.0, 0.99, 0.005, key="bsm_fid")

    with st.sidebar.expander("Run Settings", expanded=False):
        n_target = st.number_input("End-to-end links to generate", min_value=1, value=1, step=1, key="n_target")
        n_slots = st.number_input(
            "Parallel memory slots (ASAP only)", min_value=1, value=1, step=1, key="n_slots",
            disabled=(policy != "asap"),
        )

    try:
        linear_cfg = SimulationConfig(
            rep_nodes=int(n_repeaters),
            rep_spacing_km=distance / (n_repeaters + 1),
            attenuation_length_km=att_len,
            source_efficiency=source_efficiency,
            source_state_fidelity=source_fidelity,
            laser_pulsed=laser_pulsed,
            laser_power_avg_mW=laser_power,
            laser_rep_rate_MHz=laser_rate,
            laser_wavelength_nm=laser_wl,
            detector_rep_rate_MHz=det_rate,
            dark_count_rate_hz=dark_rate,
            detection_window_s=det_window_ns * 1e-9,
            dephasing_param_s=dephasing_s,
            bsm_fidelity=bsm_fid,
            swap_policy=policy,
            n_target_links=int(n_target),
            n_parallel_slots=int(n_slots) if policy == "asap" else 1,
            seed=None,  # filled in below once the seed widget is read
        )
    except ValueError as e:
        cfg_error = str(e)

    if policy == "asap" and n_repeaters >= 4:
        st.sidebar.warning("ASAP with 4+ repeaters can take a long time (tens of seconds or more).")

# ---- Star ----
if mode == "star":
    star_protocol = STAR_PROTOCOL_LABELS[protocol_label]
    max_links = MAX_STAR_LINKS[star_protocol]
    n_links = st.sidebar.slider(
        "Number of Links (users)", min_value=2, max_value=max_links, value=min(3, max_links), key=f"n_links_{star_protocol}",
        help=f"{protocol_label} is limited to {max_links} links (dense density-matrix simulation).",
    )
    if star_protocol == "factory" and n_links >= 5:
        st.sidebar.warning("Factory with 5 links takes several seconds per run.")

    with st.sidebar.expander("Hub Memory Noise", expanded=True):
        star_noise = st.checkbox("Enable hub dephasing", value=True, key="star_noise")
        star_lambda = st.slider(
            "Dephasing parameter \u039b (1 = perfect memory)", 0.0, 1.0, 0.95, 0.01, key="star_lambda", disabled=not star_noise
        )
        rounds_mode = st.radio(
            "Link generation rounds",
            ["All in round 0", "Manual", "Random (geometric)"],
            index=1,
            key="rounds_mode",
            disabled=not star_noise,
        )
        manual_rounds_text = st.text_input(
            "Rounds (comma-separated)",
            value=", ".join(str(2 * i) for i in range(n_links)),
            key=f"rounds_text_{n_links}",
            disabled=(not star_noise or rounds_mode != "Manual"),
        )
        gen_prob = st.slider(
            "Per-round generation probability", 0.05, 1.0, 0.5, 0.05, key="gen_prob",
            disabled=(not star_noise or rounds_mode != "Random (geometric)"),
        )

    try:
        star_rounds = None
        star_gen_prob = None
        if star_noise and rounds_mode == "Manual":
            star_rounds = parse_rounds(manual_rounds_text, n_links)
        elif star_noise and rounds_mode == "Random (geometric)":
            star_gen_prob = gen_prob
        star_cfg = StarConfig(
            n_links=n_links, protocol=star_protocol, noise=star_noise,
            Lambda=star_lambda if star_noise else None, rounds=star_rounds, gen_prob=star_gen_prob, seed=None,
        )
    except ValueError as e:
        cfg_error = str(e)

# ---- Repetitions & seed (discrete-event and star modes) ----
# Provides control over random result generation.
if mode in ("linear", "star"):
    with st.sidebar.expander("Repetitions & Seed", expanded=False):
        runs = int(st.number_input("Independent runs (averaged)", min_value=1, max_value=500, value=1, step=1, key="runs"))
        use_seed = st.checkbox("Fix random seed", value=False, key="use_seed")
        seed_val = int(st.number_input("Seed", min_value=0, value=102, step=1, key="seed", disabled=not use_seed))
        seed = seed_val if use_seed else None
    if linear_cfg is not None:
        linear_cfg = dataclasses.replace(linear_cfg, seed=seed)
    if star_cfg is not None:
        star_cfg = dataclasses.replace(star_cfg, seed=seed)

if cfg_error:
    st.sidebar.error(cfg_error)

run_clicked = st.sidebar.button("Run Simulation", width="stretch", disabled=bool(cfg_error))

# Handles layout execution commands. Clicking the run button resets error metrics and dispatches the execution request.
if run_clicked:
    st.session_state["last_error"] = None
    try:
        if mode == "analytical":
            sim = run_repeater_simulation(
                distance, n_repeaters, BELL_LABELS[dist_state_label], noise_enabled, T_p_us, T2_ms, eta, p_d, fiber_loss
            )
            st.session_state["last_sim"] = {"kind": "analytical", "data": sim, "noise": noise_enabled}
        else:
            bar = st.sidebar.progress(0.0, text="Running simulation...")
            res = simulator.run(
                linear_cfg if mode == "linear" else star_cfg,
                runs=runs,
                progress=lambda done, total: bar.progress(done / total, text=f"Run {done}/{total}"),
            )
            bar.empty()
            st.session_state["last_sim"] = {"kind": mode, "data": res, "cfg": linear_cfg if mode == "linear" else star_cfg}
    except ValueError as e:
        st.session_state["last_sim"] = None
        st.session_state["last_error"] = str(e)

# Only show a stored result if it belongs to the currently selected mode
_stored = st.session_state.get("last_sim")
last = _stored if (_stored and _stored["kind"] == mode) else None

# Set documentation background
APP_DIR = Path(__file__).resolve().parent

def find_doc_file():
    folders = [APP_DIR, APP_DIR / "docs", APP_DIR.parent]
    for pattern in (r"index\.md", r"index.*\.md"):
        for folder in folders:
            if folder.is_dir():
                for p in sorted(folder.iterdir()):
                    if p.is_file() and re.fullmatch(pattern, p.name.strip(), flags=re.I):
                        return p
    return None

DOC_FILE = find_doc_file()

@st.cache_data(show_spinner=False)
def load_markdown_doc(path_str, mtime):
    text = Path(path_str).read_text(encoding="utf-8")
    text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)   # Jekyll front matter
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)                          # HTML comments
    return text

def _mermaid(code):
    height = 340 if code.count("\n") <= 6 else 780
    page = ('<div style="background:#ffffff;border-radius:8px;padding:8px;">'
            f'<pre class="mermaid">{escape(code)}</pre></div>'
            '<script type="module">'
            'import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";'
            'mermaid.initialize({startOnLoad: true, theme: "neutral"});'
            "</script>")
    if hasattr(st, "iframe"):
        st.iframe(page, height=height)
    else:
        components.html(page, height=height, scrolling=True)

def render_markdown(text):
    parts = re.split(r"```mermaid\s*\n(.*?)```", text, flags=re.S)   # [text, diagram, text, ...]
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                st.markdown(part)
        else:
            _mermaid(part.strip())

# ----------------------------------------------------------------------
# Main tabs
# ----------------------------------------------------------------------
# Divides the workspace layout into four dedicated structural views.
tab_sim, tab_plots, tab_docs, tab_tools = st.tabs(["Simulation", "Plots", "Documentation", "Other Tools"])


def _mean_pm(mean, std, runs_, digits=4):
    return f"{mean:.{digits}f}" + (f" \u00b1 {std:.{digits}f}" if runs_ > 1 else "")


# ---------------- Simulation tab ----------------
# Serves as the primary data cockpit. It checks the type profile of the last run to dynamically render relevant results, 
# using four-column horizontal metric rows to display network rates, execution times, and mean deviations clearly.
with tab_sim:
    st.subheader("Selected Network Topology")
    if topology == "Linear":
        topo_svg, n_links_lin = draw_topology_svg(n_repeaters, distance)
        st.markdown(
            f'<div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:12px; '
            f'padding:1rem 0.5rem;">{topo_svg}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"Linear topology ({protocol_label}): {n_repeaters} repeater(s), {n_links_lin} link(s), "
            f"~{distance / n_links_lin:.2f} km per link"
        )
    else:
        st.markdown(
            f'<div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:12px; '
            f'padding:1rem 0.5rem;">{draw_star_svg(n_links)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Star topology ({protocol_label}): {n_links} links fused at the hub into a {n_links}-party GHZ state")

    st.subheader("Simulation Output")
    if st.session_state.get("last_error"):
        st.error(st.session_state["last_error"])

    if last is None:
        st.info("Configure parameters in the sidebar and click **Run Simulation**.")

    # ---- analytical (QRep) ----
    elif last["kind"] == "analytical":
        sim = last["data"]
        st.success("Simulation Completed")
        state_label = r"\rho_{\text{final}}" if last["noise"] else r"|\psi_{\text{final}}\rangle"
        st.markdown("### Final Entangled State")
        st.latex(f"{state_label} = {to_bmatrix_latex(sim['final_state'])}")

        st.markdown("### Fidelity")
        st.latex(rf"\mathcal{{F}} = {sim['avg_fidelity']:.2f}")

        with st.expander("Per-outcome measurement details"):
            df = pd.DataFrame(sim["results"])[["measurement_outcome", "probability", "fidelity"]]
            st.dataframe(df, width="stretch")
            st.download_button("Download results as CSV", df.to_csv(index=False).encode(), "qrn_results.csv", "text/csv")

    # ---- linear discrete-event (asap / last / nesting) ----
    elif last["kind"] == "linear":
        res = last["data"]
        st.success(f"Simulation Completed \u2013 {res.protocol.upper()} policy, {res.runs} run(s)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Average fidelity", _mean_pm(res.fidelity_mean, res.fidelity_std, res.runs))
        c2.metric("Entanglement rate (pairs/s)", f"{res.rate_mean:.3f}")
        c3.metric("Mean time per run (s)", f"{res.sim_time_mean:.4g}")
        c4.metric("Links generated", len(res.links))

        if res.final_state is not None:
            st.markdown("### Final Entangled State")
            st.latex(state_to_latex(res.final_state, r"\rho_{\text{final}}"))
            st.markdown("### Fidelity")
            st.latex(rf"\mathcal{{F}}_{{|\Phi^+\rangle}} = {res.fidelity_mean:.2f}")

        with st.expander("Per-link details"):
            df = linear_results_df(res)
            st.dataframe(df, width="stretch")
            st.download_button("Download results as CSV", df.to_csv(index=False).encode(), "qrn_linear_results.csv", "text/csv")
        with st.expander("Derived hardware quantities"):
            st.write(
                {
                    "Pair-generation probability per trial": res.extra["pairgen_prob_pertrial"],
                    "Channel efficiency (per half-link)": res.extra["channel_efficiency"],
                    "Spacing between nodes (km)": res.extra["rep_spacing_km"],
                }
            )

    # ---- star (piecemaker / factory) ----
    elif last["kind"] == "star":
        res = last["data"]
        cfg = last["cfg"]
        st.success(f"Simulation Completed \u2013 {res.protocol.capitalize()} protocol, {res.runs} run(s)")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{res.target} fidelity", _mean_pm(res.fidelity_mean, res.fidelity_std, res.runs))
        c2.metric("Purity Tr(\u03c1\u00b2) (last run)", f"{res.purity:.4f}")
        c3.metric("Parties sharing the state", res.extra["n_links"])
        if res.extra["rounds"] is not None:
            st.caption(f"Link generation rounds used (last run): {res.extra['rounds']} \u00b7 \u039b = {res.extra['Lambda']}")

        st.markdown("### Final Shared State")
        latex = state_to_latex(res.final_state, r"\rho_{\text{final}}")
        if latex:
            st.latex(latex)
        else:
            st.caption("State is larger than 8\u00d78; showing basis-state populations (diagonal of \u03c1).")
        st.bar_chart(populations_df(res.final_state))

        st.markdown("### Fidelity")
        st.latex(rf"\mathcal{{F}}_{{\text{{GHZ}}_{{{res.extra['n_links']}}}}} = {res.fidelity_mean:.2f}")

        with st.expander("Per-run fidelities"):
            df = pd.DataFrame({"run": range(1, res.runs + 1), "fidelity": res.fidelities})
            st.dataframe(df, width="stretch", hide_index=True)
            st.download_button("Download results as CSV", df.to_csv(index=False).encode(), "qrn_star_results.csv", "text/csv")

# ---------------- Plots tab ----------------
with tab_plots:
    # ---------- Linear / analytical sweeps ----------
    # Clicking the compute button triggers sequential data runs across a range of coordinates (using np.linspace), 
    # packaging the results into a dataframe to render smooth line charts of fidelity scaling.
    if mode == "analytical":
        st.subheader("Fidelity vs. Distance")
        st.caption("Sweeps total distance (current repeater count and noise settings held fixed).")
        if st.button("Compute distance sweep", disabled=bool(cfg_error)):
            distances = np.linspace(10, 300, 15)
            fids = [
                run_repeater_simulation(
                    d, n_repeaters, BELL_LABELS[dist_state_label], noise_enabled, T_p_us, T2_ms, eta, p_d, fiber_loss
                )["avg_fidelity"]
                for d in distances
            ]
            df_d = pd.DataFrame({"Distance (km)": distances, "Fidelity": fids}).set_index("Distance (km)")
            st.line_chart(df_d)

        st.subheader("Fidelity vs. Number of Repeaters")
        st.caption("Sweeps repeater count (current distance and noise settings held fixed).")
        if st.button("Compute repeater-count sweep", disabled=bool(cfg_error)):
            rep_counts = list(range(1, 11))
            fids_r = [
                run_repeater_simulation(
                    distance, r, BELL_LABELS[dist_state_label], noise_enabled, T_p_us, T2_ms, eta, p_d, fiber_loss
                )["avg_fidelity"]
                for r in rep_counts
            ]
            df_r = pd.DataFrame({"Number of Repeaters": rep_counts, "Fidelity": fids_r}).set_index("Number of Repeaters")
            st.line_chart(df_r)

        st.subheader("Measurement Outcome Probabilities (last run)")
        if last:
            df_p = pd.DataFrame(last["data"]["results"])[["measurement_outcome", "probability"]].set_index("measurement_outcome")
            st.bar_chart(df_p)
        else:
            st.info("Run a simulation on the **Simulation** tab first.")

    # ---------- Linear discrete-event: policy comparison ----------
    # Automates comparative network analysis. It feeds current hardware variables into all three routing strategies simultaneously 
    # and generates comparative bar charts to contrast protocol throughput and fidelity trade-offs.
    elif mode == "linear":
        st.subheader("Compare Swap Policies (ASAP vs Last vs Nesting)")
        st.caption(
            "Runs all three policies on the current hardware parameters. "
            "Nesting is skipped unless the repeater count is 2^k \u2212 1 (1, 3, 7). "
            "Uses the *Independent runs* setting from the sidebar."
        )
        if linear_cfg is None:
            st.warning("Fix the invalid parameters in the sidebar first.")
        elif st.button("Compare policies"):
            bar = st.progress(0.0, text="Comparing policies...")
            cmp = simulator.compare_policies(
                linear_cfg, runs=runs, progress=lambda d, t: bar.progress(d / t, text=f"Policy {d}/{t}")
            )
            bar.empty()
            ok = {k: v for k, v in cmp.items() if not isinstance(v, str)}
            for k, v in cmp.items():
                if isinstance(v, str):
                    st.info(f"{k.upper()} skipped: {v}")
            if ok:
                df_c = pd.DataFrame(
                    {
                        "Policy": [k.upper() for k in ok],
                        "Fidelity": [v.fidelity_mean for v in ok.values()],
                        "Rate (pairs/s)": [v.rate_mean for v in ok.values()],
                    }
                ).set_index("Policy")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("Average fidelity")
                    st.bar_chart(df_c[["Fidelity"]])
                with col_b:
                    st.caption("Entanglement rate (pairs/s)")
                    st.bar_chart(df_c[["Rate (pairs/s)"]])
                st.dataframe(df_c, width="stretch")

        st.subheader("Per-run Fidelity (last run)")
        if last and last["kind"] == "linear" and last["data"].runs > 1:
            st.line_chart(pd.DataFrame({"Fidelity": last["data"].fidelities}, index=range(1, last["data"].runs + 1)))
        elif last and last["kind"] == "linear":
            st.info("Set *Independent runs* > 1 in the sidebar to see run-to-run variation.")
        else:
            st.info("Run a simulation on the **Simulation** tab first.")

    # ---------- Star: protocol comparison / Lambda sweep ----------
    else:
        st.subheader("PieceMaker vs Factory \u2013 Fidelity vs. Dephasing \u039b")
        st.caption(
            "Sweeps \u039b with the current number of links and link-generation settings. "
            "Hub dephasing must be enabled in the sidebar. Factory is only computed up to its size limit."
        )
        if star_cfg is None:
            st.warning("Fix the invalid parameters in the sidebar first.")
        elif not star_cfg.noise:
            st.info("Enable **hub dephasing** in the sidebar to sweep \u039b.")
        elif st.button("Compute \u039b sweep"):
            lambdas = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            series = {"piecemaker": [], "factory": []}
            bar = st.progress(0.0, text="Sweeping \u039b...")
            total = len(lambdas) * 2
            done = 0
            for lam in lambdas:
                for proto in series:
                    done += 1
                    try:
                        r = simulator.run(dataclasses.replace(star_cfg, protocol=proto, Lambda=lam), runs=runs)
                        series[proto].append(r.fidelity_mean)
                    except ValueError:
                        series[proto].append(np.nan)
                    bar.progress(done / total, text=f"{done}/{total}")
            bar.empty()
            df_l = pd.DataFrame(
                {"PieceMaker": series["piecemaker"], "Factory": series["factory"]}, index=pd.Index(lambdas, name="\u039b")
            )
            st.line_chart(df_l)
            st.dataframe(df_l, width="stretch")

        st.subheader("Basis-state Populations (last run)")
        if last and last["kind"] == "star":
            st.bar_chart(populations_df(last["data"].final_state))
        else:
            st.info("Run a simulation on the **Simulation** tab first.")


# ---------------- Documentation tab ----------------
with tab_docs:
    if DOC_FILE is not None:
        render_markdown(load_markdown_doc(str(DOC_FILE), DOC_FILE.stat().st_mtime))
    else:
        st.warning(f"Documentation file (index.md) not found. app.py is running from **{APP_DIR}**. "
                   "Put index.md in that folder (or in a `docs` subfolder).")
        seen = sorted(repr(p.name) for p in APP_DIR.iterdir() if p.suffix.lower() in (".md", ".txt", ".markdown"))
        st.caption("Markdown/text files found in that folder: " + (", ".join(seen) if seen else "none"))


# ---------------- Other Tools tab (bonus, from the previous version of this file) ----------------
# An independent testing playground that lets users evaluate individual components like state verification utilities, 
# concurrence calculations via Ebit, or teleportation channels, bypasses the full network topology setup.
with tab_tools:
    st.write("Standalone utilities from the `qrnetwork` package, useful outside the repeater-network workflow.")
    tool = st.selectbox(
        "Choose a tool",
        ["State Utilities (Q)", "Entanglement Check (Ebit)", "Teleportation (Teleport)", "Channel Fidelity (QChannel)"],
    )

    if tool == "State Utilities (Q)":
        col1, col2 = st.columns(2)
        with col1:
            kind = st.selectbox("State type", ["Random pure state", "Random mixed state", "Bell state"])
        with col2:
            n_qubits = st.slider("Number of qubits", 1, 3, 1, disabled=(kind == "Bell state"))

        if kind == "Random pure state":
            state = Q.rand.p(n_qubits)
        elif kind == "Random mixed state":
            state = Q.rand.m(n_qubits)
        else:
            bell_name = st.selectbox("Bell state", list(BELL_STATES.keys()))
            state = BELL_STATES[bell_name]

        st.dataframe(matrix_to_dataframe(state))
        q = Q(state)
        c1, c2, c3 = st.columns(3)
        c1.metric("Norm  Q(state).n()", q.n())
        c2.metric("Purity  Q(state).purity()", q.purity())
        is_ket = Is(state).ket()
        c3.metric("Is ket?", "Yes" if is_ket else "No")

        d1, d2 = st.columns(2)
        with d1:
            st.caption("Dagger - `Q(state).d()`")
            st.dataframe(matrix_to_dataframe(q.d()))
        with d2:
            st.caption("Normalized - `Q(state).u()`")
            st.dataframe(matrix_to_dataframe(q.u()))
        if is_ket:
            st.caption("Density matrix - `Q(state).dm()`")
            st.dataframe(matrix_to_dataframe(q.dm()))

    elif tool == "Entanglement Check (Ebit)":
        rep = st.selectbox("Representation", ["Ket vector", "Density matrix (Werner state)"])
        if rep == "Ket vector":
            bell_name = st.selectbox("Base Bell state", list(BELL_STATES.keys()))
            state = BELL_STATES[bell_name]
        else:
            bell_name = st.selectbox("Base Bell state", list(BELL_STATES.keys()))
            p = st.slider("Werner mixing parameter p", 0.0, 1.0, 0.8, 0.01)
            state = Q.Werner(p, state=BELL_STATES[bell_name])
        st.dataframe(matrix_to_dataframe(state))
        st.metric("Concurrence (Ebit)", round(float(Ebit(state)), 4))
        st.caption("0 -> separable, non-zero -> entangled (max 1 for a maximally entangled state).")

    elif tool == "Teleportation (Teleport)":
        mode = st.radio("Input type", ["Pure state (ket)", "Mixed state (density matrix)"], horizontal=True)
        channel_choice = st.selectbox("Entangled channel", list(BELL_STATES.keys()) + ["Werner state"])
        if channel_choice == "Werner state":
            base = st.selectbox("Werner base Bell state", list(BELL_STATES.keys()), key="werner_base_tel")
            p = st.slider("Werner mixing parameter p", 0.5, 1.0, 0.9, 0.01, key="werner_p_tel")
            channel = Q.Werner(p, state=BELL_STATES[base])
        else:
            channel = BELL_STATES[channel_choice]
            if mode == "Mixed state (density matrix)":
                channel = Q(channel).dm()

        if st.button("Run teleportation"):
            try:
                qS = Q.rand.p(1) if mode == "Pure state (ket)" else Q.rand.m(1)
                st.caption("Input state to teleport")
                st.dataframe(matrix_to_dataframe(qS))
                result = Teleport(qS, channel)
                rows = [
                    {"Measurement outcome": r["measurement_outcome"], "Probability": r["probability"], "Fidelity": r["fidelity"]}
                    for r in result.results["results"]
                ]
                st.dataframe(pd.DataFrame(rows))
                st.caption("Local unitary matrix (Bell basis -> computational basis)")
                st.dataframe(matrix_to_dataframe(result.results["Local unitary matrix"]))
            except ValueError as e:
                st.error(str(e))

    elif tool == "Channel Fidelity (QChannel)":
        channel_choice = st.selectbox("Entangled channel", list(BELL_STATES.keys()) + ["Werner state"])
        iterations = st.slider("Iterations", 5, 500, 50, 5)
        if channel_choice == "Werner state":
            base = st.selectbox("Werner base Bell state", list(BELL_STATES.keys()), key="werner_base_qc")
            p = st.slider("Werner mixing parameter p", 0.5, 1.0, 0.9, 0.01, key="werner_p_qc")
            channel = Q.Werner(p, state=BELL_STATES[base])
        else:
            channel = BELL_STATES[channel_choice]

        if st.button("Run channel simulation"):
            try:
                result = QChannel(channel, iteration=iterations).teleport()
                st.metric("Average fidelity", result["Average fidelity"])
            except ValueError as e:
                st.error(str(e))

st.sidebar.markdown("---")
st.sidebar.caption("QNeCT \u00b7 built on NumPy, SciPy, SymPy")
