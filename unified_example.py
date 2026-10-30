"""Script-level tour of the unified QNeCT simulator (no GUI needed)."""
from qrnetwork import QNeCTSimulator, SimulationConfig, StarConfig

sim = QNeCTSimulator()

# ---- Linear chain: one run per policy on identical hardware --------------
hw = SimulationConfig(rep_nodes=3, rep_spacing_km=30.0, source_state_fidelity=0.99,
                      bsm_fidelity=0.99, dephasing_param_s=0.01, seed=102)
for policy, res in sim.compare_policies(hw, runs=10).items():
    if isinstance(res, str):
        print(f"{policy:8s} skipped: {res}")
    else:
        print(f"{policy:8s} F = {res.fidelity_mean:.3f} +/- {res.fidelity_std:.3f}   rate = {res.rate_mean:.2f} pairs/s")

# ---- Star network: PieceMaker vs Factory ---------------------------------
star = StarConfig(n_links=3, noise=True, Lambda=0.9, rounds=(0, 2, 5), seed=7)
for proto, res in sim.compare_star_protocols(star, runs=10).items():
    print(f"{proto:10s} GHZ-3 fidelity = {res.fidelity_mean:.3f}   purity = {res.purity:.3f}")
