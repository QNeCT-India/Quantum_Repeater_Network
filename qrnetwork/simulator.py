"""
Unified QNeCT simulator
=======================

One entry point for every network simulation in the package:

    Topology   Protocol / policy          Engine
    ---------  -------------------------  ---------------------------------------
    linear     "asap"                     RepeaterSimulation  (discrete-event)
    linear     "last"                     RepeaterSimulation  (discrete-event)
    linear     "nesting"                  RepeaterSimulation  (discrete-event)
    star       "piecemaker"               StarProtocol.piecemaker
    star       "factory"                  StarProtocol.factory

(The older analytical Bell-state chain, ``QRep``, is untouched and is still
available for ideal/noisy-link swapping; the GUI calls it directly.)

Usage
-----
    from qrnetwork import QNeCTSimulator, SimulationConfig, StarConfig

    sim = QNeCTSimulator()
    res = sim.run(SimulationConfig(rep_nodes=3, swap_policy="nesting", seed=1), runs=20)
    res = sim.run(StarConfig(n_links=3, protocol="piecemaker", noise=True, Lambda=0.9,
                             rounds=(0, 2, 5)), runs=10)
    print(res.fidelity_mean, res.rate_mean)

Everything returned is a plain ``UnifiedResult`` so that scripts and the
Streamlit GUI can treat linear and star runs identically.
"""
# All annotations are stored as strings ('List[int]', 'Node' )
# Forward references become trivial, you can writedef f(x: Node) -> Node:even if class Nodeappears later.
from __future__ import annotations
# The dataclasses module helps you write classes that mainly store data by generating methods like __init__, __repr__, and comparisons.
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

from .primaryfn import Q
from .star_protocol import StarProtocol
from .linear_noisy_sim import SimulationConfig, RepeaterSimulation, SwapPolicy

# Establishes global configuration bounds.
# Dense density-matrix simulations experience exponential space/time growth (\(4^{N}\) operations).
# These constants protect hardware memory from crashing during execution.
LINEAR_POLICIES = tuple(p.value for p in SwapPolicy)      # ("last", "nesting", "asap")
STAR_PROTOCOLS = ("piecemaker", "factory")
MAX_STAR_LINKS = {"piecemaker": 9, "factory": 5}
MIN_STAR_LINKS = 2


# ---------------------------------------------------------------------------
# Star configuration / helpers
# ---------------------------------------------------------------------------
# Marks the class as frozen=True to make instances immutable and hashable, preventing accidental parameter modification mid-simulation.
@dataclass(frozen=True)
class StarConfig:
    """ Defines structural fields for star topologies,n.

    n_links   : number of spokes (= number of end parties sharing the GHZ state)
    protocol  : "piecemaker" (sequential fusion) or "factory" (wait for all links)
    noise     : apply hub-memory dephasing while links wait
    Lambda    : dephasing parameter per round, in [0, 1]  (1 = noiseless memory)
    rounds    : round in which each link was generated (len == n_links). If None and
                gen_prob is given, rounds are drawn from Geometric(gen_prob) per link;
                if both are None, all links are generated in round 0 (no waiting).
    gen_prob  : per-round link generation probability, used only if rounds is None
    seed      : reproducibility seed (None -> non-deterministic)
    """
    n_links: int = 3
    protocol: str = "piecemaker"
    noise: bool = False
    Lambda: float | None = None
    rounds: tuple[int, ...] | None = None
    gen_prob: float | None = None
    seed: int | None = None

    # A special dataclass hook that runs automatically after __init__() to enforce input validation and domain constraints before simulation setup
    def __post_init__(self) -> None:
        # Enforces foundational boundaries on structural protocols and prevents simulation complexity configurations that exceed safe computational boundaries.
        if self.protocol not in STAR_PROTOCOLS:
            raise ValueError(f"protocol must be one of {STAR_PROTOCOLS}, got {self.protocol!r}")
        if self.n_links < MIN_STAR_LINKS:
            raise ValueError(f"n_links must be >= {MIN_STAR_LINKS}")
        if self.n_links > MAX_STAR_LINKS[self.protocol]:
            raise ValueError(
                f"{self.protocol} is limited to {MAX_STAR_LINKS[self.protocol]} links "
                f"(density-matrix size grows as 4^(2*links))."
            )
        # Conditionally validates physical bounds for noise-handling variables.
        if self.noise:
            if self.Lambda is None or not (0.0 <= self.Lambda <= 1.0):
                raise ValueError("Lambda must be in [0, 1] when noise is enabled.")
            if self.rounds is not None and len(self.rounds) != self.n_links:
                raise ValueError(f"'rounds' needs {self.n_links} entries, got {len(self.rounds)}.")
            if self.rounds is not None and min(self.rounds) < 0:
                raise ValueError("'rounds' entries must be >= 0.")
            if self.gen_prob is not None and not (0.0 < self.gen_prob <= 1.0):
                raise ValueError("gen_prob must be in (0, 1].")

# Constructs an ideal reference column vector for an n-qubit GHZ state.
def ghz_state(n: int) -> Q:
    """(|0...0> + |1...1>)/sqrt(2) as a Column Vector wrapped in a Q instance."""
    v = np.zeros((2 ** n, 1), dtype=complex)
    v[0, 0] = v[-1, 0] = 1 / np.sqrt(2)
    return Q(v)

# Calculates the state fidelity (\(\langle\text{GHZ}_n\vert{} \rho \vert{}\text{GHZ}_n\rangle\)).
def ghz_fidelity(rho: Q | np.ndarray, n: int) -> float:
    r = rho if isinstance(rho, Q) else Q(rho)
    g = ghz_state(n)
    return float(np.real((g.d() @ r @ g).item()))

# Computes the mixedness metric (Tr(ρ²))
def purity(rho: Q | np.ndarray) -> float:
    """Compute the purity of the state (Tr(rho^2)) via the internal Q method."""
    r = rho if isinstance(rho, Q) else Q(rho)
    return float(r.purity())


# ---------------------------------------------------------------------------
# Unified result
# ---------------------------------------------------------------------------
# Defines a standardized format for saving results.
@dataclass
class UnifiedResult:
    topology: str                        # "linear" | "star"
    protocol: str                        # asap / last / nesting / piecemaker / factory
    runs: int
    fidelities: list[float]              # one value per run (linear: mean over its links)
    fidelity_mean: float
    fidelity_std: float
    rate_mean: float | None = None       # pairs/s, linear only
    sim_time_mean: float | None = None   # s, linear only
    final_state: Any = None              # density matrix of the last run (Q)
    target: str = ""                     # "Bell |phi+>" or "GHZ_n"
    purity: float | None = None          # star only (last run)
    links: list[dict] = field(default_factory=list)   # linear: per completed link
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------
class QNeCTSimulator:
    """Single facade over the linear discrete-event and star simulators."""

   #  A helper method that allows UI utilities or execution engines to discover supported configuration types dynamically.
    @staticmethod
    def protocols(topology: str) -> tuple[str, ...]:
        topology = topology.lower()
        if topology == "linear":
            return ("asap", "last", "nesting")
        if topology == "star":
            return STAR_PROTOCOLS
        raise ValueError("topology must be 'linear' or 'star'")

    # The calling function doesn't need to know the inner workings of different network types. 
    # It passes a configuration file, and this method safely handles routing.
    def run(self, config: SimulationConfig | StarConfig, runs: int = 1, progress=None) -> UnifiedResult:
        """Run `runs` independent repetitions and aggregate.

        progress : optional callable(done:int, total:int) for GUIs.
        Seeded configs use seed, seed+1, ... so repetitions differ but stay reproducible.
        """
        if runs < 1:
            raise ValueError("runs must be >= 1")
        if isinstance(config, SimulationConfig):
            return self._run_linear(config, runs, progress)
        if isinstance(config, StarConfig):
            return self._run_star(config, runs, progress)
        raise TypeError("config must be a SimulationConfig or StarConfig")

    # -- linear -------------------------------------------------------------
    def _run_linear(self, cfg: SimulationConfig, runs: int, progress) -> UnifiedResult:
        fids, rates, times, links, last_rho = [], [], [], [], None
        for i in range(runs):
            # dataclasses.replace(cfg, seed=cfg.seed + i) creates a unique pseudo-random sequence for each iteration
            c = cfg if cfg.seed is None else dataclasses.replace(cfg, seed=cfg.seed + i)
            res = RepeaterSimulation(c).run()          # a fresh simulation each time (state is consumed)
            fids.append(res.average_fidelity)
            rates.append(res.entanglement_rate)
            times.append(res.total_sim_time)
            for l in res.completed_links:
                links.append({"run": i + 1, "fidelity": l.fidelity, "created_time_s": l.created_time})
                last_rho = l.rho
            if progress:
                # progress(i + 1, runs) fires an optional GUI-bound callback to track execution progress.
                progress(i + 1, runs)
        # Aggregates raw list metrics into mathematical averages and spreads, then structures the results into a standardized UnifiedResult format.
        return UnifiedResult(
            topology="linear", protocol=str(SwapPolicy(cfg.swap_policy).value), runs=runs,
            fidelities=fids, fidelity_mean=float(np.mean(fids)), fidelity_std=float(np.std(fids)),
            rate_mean=float(np.mean(rates)), sim_time_mean=float(np.mean(times)),
            final_state=last_rho, target="Bell |\u03a6+\u27e9", links=links,
            extra={"rep_nodes": cfg.rep_nodes, "rep_spacing_km": cfg.rep_spacing_km,
                   "pairgen_prob_pertrial": cfg.pairgen_prob_pertrial,
                   "channel_efficiency": cfg.channel_efficiency},
        )

    # -- star ---------------------------------------------------------------
    def _run_star(self, cfg: StarConfig, runs: int, progress) -> UnifiedResult:
        # Uses Python reflection (getattr) to dynamically extract the protocol function ("piecemaker" or "factory") 
        # from the StarProtocol class based on user config strings.
        fn = getattr(StarProtocol, cfg.protocol)
        rng = np.random.default_rng(cfg.seed)
        fids, last_rho, used_rounds = [], None, None
        saved = np.random.get_state()
        try:
            if cfg.seed is not None:
                np.random.seed(cfg.seed)
            # Executes individual runs for star topologies
            for i in range(runs):
                rounds = None
                if cfg.noise:
                    if cfg.rounds is not None:
                        rounds = list(cfg.rounds)
                    elif cfg.gen_prob is not None:
                        # If timelines aren't explicitly provided, it models arrival distributions using a geometric random process (1/gen_prob).
                        rounds = [int(rng.geometric(cfg.gen_prob)) for _ in range(cfg.n_links)]
                last_rho = fn(cfg.n_links, cfg.noise, cfg.Lambda, rounds)
                used_rounds = sorted(rounds) if rounds is not None else None
                fids.append(ghz_fidelity(last_rho, cfg.n_links))
                if progress:
                    progress(i + 1, runs)
        # A finally safety block ensures that even if an execution exception crashes the loop mid-run, 
        # NumPy's original global random seed state is restored safely.
        finally:
            np.random.set_state(saved)

        return UnifiedResult(
            topology="star", protocol=cfg.protocol, runs=runs, fidelities=fids,
            fidelity_mean=float(np.mean(fids)), fidelity_std=float(np.std(fids)),
            final_state=last_rho, target=f"GHZ-{cfg.n_links}", purity=purity(last_rho),
            extra={"n_links": cfg.n_links, "rounds": used_rounds, "Lambda": cfg.Lambda},
        )

    # Automates parameter sweeps by cloning a baseline configuration dataclass and using dictionary unpacking (**{field_name: v}) 
    # to swap specific parameter values iteratively across iterations.
    def sweep(self, base: SimulationConfig | StarConfig, field_name: str, values: Sequence,
              runs: int = 1, progress=None) -> list[UnifiedResult]:
        """Re-run `base` with one field replaced by each value (via dataclasses.replace)."""
        out = []
        for k, v in enumerate(values):
            out.append(self.run(dataclasses.replace(base, **{field_name: v}), runs=runs))
            if progress:
                progress(k + 1, len(values))
        return out

    # Compares linear network routing policies side-by-side using the same hardware configuration 
    def compare_policies(self, base: SimulationConfig, runs: int = 1, policies: Sequence[str] | None = None,
                         progress=None) -> dict[str, UnifiedResult | str]:
        """Run every linear policy on the same hardware config.

        Policies that are invalid for `base` (e.g. nesting with rep_nodes != 2^k-1) are
        returned as an explanatory string instead of a result.
        """
        out: dict[str, UnifiedResult | str] = {}
        pols = list(policies or self.protocols("linear"))
        for k, p in enumerate(pols):
            try:
                out[p] = self.run(dataclasses.replace(base, swap_policy=p), runs=runs)
            except ValueError as e:
                out[p] = str(e)
            if progress:
                progress(k + 1, len(pols))
        return out

    # Provides a structured mechanism for running star network simulations across all active protocols using matching hardware bounds.
    def compare_star_protocols(self, base: StarConfig, runs: int = 1, progress=None) -> dict[str, UnifiedResult | str]:
        out: dict[str, UnifiedResult | str] = {}
        for k, p in enumerate(STAR_PROTOCOLS):
            try:
                out[p] = self.run(dataclasses.replace(base, protocol=p), runs=runs)
            except ValueError as e:
                out[p] = str(e)
            if progress:
                progress(k + 1, len(STAR_PROTOCOLS))
        return out

# Provides a simple global functional shortcut so that external scripts don't have to manually illustrate a full QNeCTSimulator object for basic,
# single-line executions
def simulate(config: SimulationConfig | StarConfig, runs: int = 1) -> UnifiedResult:
    """Shortcut: ``simulate(cfg, runs=10)``."""
    return QNeCTSimulator().run(config, runs=runs)
