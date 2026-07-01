"""mbnma.py -- model-based dose-response network meta-analysis (frequentist).

A network where the "treatments" are (agent, dose) combinations. Instead of
estimating one free relative effect per (agent, dose) node -- the saturated /
"split" NMA -- a model-based NMA constrains the nodes of each agent to lie on a
parametric DOSE-RESPONSE curve f_a(dose; psi_a) with f_a(0)=0. This is the
frequentist analogue of the Bayesian MBNMAdose framework (Pedder et al. 2019).

Why it is just the NMA likelihood with a constraint
---------------------------------------------------
Reuse the verified netmeta-parity contrast machinery in `nma_core`:
  * `_assemble` builds the contrast incidence B (rows = study contrasts,
    +1/-1 over node columns) and the block-diagonal GLS weight W = V^-1 with the
    correct multi-arm shared-arm correlation (tau^2/2 off-diagonal).
Pick the network reference r (placebo). Every contrast row equals delta_{t1} -
delta_{t2} where delta_t = effect(node t) - effect(r) and delta_r = 0. With the
reference column dropped from B (B_red), the model is simply

    y = B_red @ delta + error,   Cov(error) = W^{-1}.

A dose-response model replaces the free delta by delta = h(psi):
  * 'nma'    (saturated): delta free            -> identical to standard NMA.
  * 'linear':  delta_t = beta_{a(t)} * dose_t   -> delta = M psi (GLS, closed form).
  * 'exponential': delta_t = E_a * (1 - exp(-dose_t / L_a)).
  * 'emax':    delta_t = Emax_a * dose_t / (ED50_a + dose_t).
The linear/saturated models are linear in psi (one GLS solve); exponential and
Emax are nonlinear and fit by Gauss-Newton GLS.

Validation
----------
The saturated model reduces EXACTLY (to ~1e-9) to R `netmeta`'s common-effect
treatment effects vs reference -- see test_mbnma.py / reference/mbnma_gold.json.
That proves the network likelihood is correct; the dose-response models are
constrained least-squares on the same correct likelihood, checked by parameter
recovery on simulated networks with known truth.

JAGS / `MBNMAdose` is not installed in this environment, so an exact match to the
Bayesian package is not attempted here; the netmeta reduction is the external
anchor and is documented as such (see REPORT_DOSERESPONSE.md).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "nma"))
from nma_core import Comparison, _assemble, _dl_tau2  # noqa: E402


@dataclass
class MBNMAFit:
    model: str
    agents: list           # active agents (excludes reference)
    psi: dict              # agent -> parameter dict
    psi_vcov: np.ndarray   # covariance of the stacked parameter vector
    treatments: list       # all node labels (reference first)
    ref: str
    delta: np.ndarray      # fitted node effects vs reference (len = n nodes; ref=0)
    delta_se: np.ndarray
    tau2: float
    converged: bool
    loglik: float = float("nan")


def _build(comparisons, ref, tau2):
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comparisons]
    treats = []
    for c in comps:
        for t in (c.t1, c.t2):
            if t not in treats:
                treats.append(t)
    if ref not in treats:
        raise ValueError(f"reference {ref!r} not in network")
    # reference first for stable indexing
    treats = [ref] + [t for t in treats if t != ref]
    tidx = {t: i for i, t in enumerate(treats)}
    B, W, y, _ = _assemble(comps, tidx, len(treats), tau2=tau2)
    ridx = tidx[ref]
    keep = [i for i in range(len(treats)) if i != ridx]
    B_red = B[:, keep]                 # m x (n-1), columns = non-ref nodes
    node_order = [treats[i] for i in keep]
    return treats, node_order, B_red, W, y


def _agent_dose(node, parse):
    a, d = parse(node)
    return a, float(d)


def _linear_design(node_order, parse, agents):
    """delta = M psi, columns = agents, entry = dose for that node's agent."""
    M = np.zeros((len(node_order), len(agents)))
    aidx = {a: j for j, a in enumerate(agents)}
    for i, node in enumerate(node_order):
        a, dose = _agent_dose(node, parse)
        M[i, aidx[a]] = dose
    return M


def _active_agents(node_order, parse):
    ags = []
    for node in node_order:
        a, _ = _agent_dose(node, parse)
        if a not in ags:
            ags.append(a)
    return ags


def fit_mbnma(comparisons, *, ref, parse, model="linear", random=False,
              max_iter=200, tol=1e-12):
    """Fit a model-based dose-response NMA from contrast data.

    comparisons : iterable of (studlab, t1, t2, te, se) or Comparison.
    ref         : reference node label (placebo), delta=0.
    parse       : node-label -> (agent, dose). Reference may parse to any agent;
                  its dose-response is not estimated (delta_ref=0 by construction).
    model       : 'nma' | 'linear' | 'exponential' | 'emax'.
    random      : if True, add a common tau^2 (generalized DL from the saturated
                  fit) to the weights before fitting.
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comparisons]

    tau2 = 0.0
    if random:
        treats0, _, _, _, _ = _build(comps, ref, 0.0)
        tidx0 = {t: i for i, t in enumerate(treats0)}
        df_Q = max(len(comps) - (len(treats0) - 1), 0)
        tau2, *_ = _dl_tau2(comps, tidx0, len(treats0), df_Q)

    treats, node_order, B_red, W, y = _build(comps, ref, tau2)
    agents = _active_agents(node_order, parse)

    if model in ("nma", "linear"):
        if model == "nma":
            X = B_red
            ncol = X.shape[1]
        else:
            M = _linear_design(node_order, parse, agents)
            X = B_red @ M
            ncol = len(agents)
        XtW = X.T @ W
        A = XtW @ X
        Vpsi = np.linalg.pinv(A, rcond=1e-14)
        psi_vec = Vpsi @ (XtW @ y)
        converged = True
        ll = float("nan")
    else:
        psi_vec, Vpsi, converged, ll = _gauss_newton(
            B_red, W, y, node_order, parse, agents, model, max_iter, tol)

    # Map psi back to node effects delta and their SEs.
    delta_nodes, J = _delta_and_jac(psi_vec, node_order, parse, agents, model)
    delta_se_nodes = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", J, Vpsi, J), 0.0))

    # full node list incl reference (delta=0)
    full_delta = np.zeros(len(treats))
    full_se = np.zeros(len(treats))
    pos = {t: i for i, t in enumerate(treats)}
    for node, dv, sev in zip(node_order, delta_nodes, delta_se_nodes):
        full_delta[pos[node]] = dv
        full_se[pos[node]] = sev

    psi = _unpack_psi(psi_vec, agents, model)
    return MBNMAFit(model=model, agents=agents, psi=psi, psi_vcov=Vpsi,
                    treatments=treats, ref=ref, delta=full_delta,
                    delta_se=full_se, tau2=float(tau2), converged=converged,
                    loglik=ll)


# --- nonlinear dose-response maps ----------------------------------------- #
def _dr_value(model, dose, params):
    if model == "exponential":
        E, L = params
        return E * (1.0 - np.exp(-dose / L))
    if model == "emax":
        Emax, ED50 = params
        return Emax * dose / (ED50 + dose)
    raise ValueError(model)


def _dr_grad(model, dose, params):
    """d delta / d params at this dose."""
    if model == "exponential":
        E, L = params
        ex = np.exp(-dose / L)
        return np.array([1.0 - ex, -E * ex * dose / (L * L)])
    if model == "emax":
        Emax, ED50 = params
        return np.array([dose / (ED50 + dose), -Emax * dose / (ED50 + dose) ** 2])
    raise ValueError(model)


_NP = {"exponential": 2, "emax": 2}


def _delta_and_jac(psi_vec, node_order, parse, agents, model):
    """node effects delta(psi) and Jacobian d delta / d psi (len_nodes x len_psi)."""
    n = len(node_order)
    if model in ("nma",):
        return psi_vec.copy(), np.eye(n)
    if model == "linear":
        M = _linear_design(node_order, parse, agents)
        return M @ psi_vec, M
    npar = _NP[model]
    aidx = {a: j for j, a in enumerate(agents)}
    delta = np.zeros(n)
    J = np.zeros((n, len(agents) * npar))
    for i, node in enumerate(node_order):
        a, dose = _agent_dose(node, parse)
        j = aidx[a]
        p = psi_vec[j * npar:(j + 1) * npar]
        delta[i] = _dr_value(model, dose, p)
        J[i, j * npar:(j + 1) * npar] = _dr_grad(model, dose, p)
    return delta, J


def _gauss_newton(B_red, W, y, node_order, parse, agents, model, max_iter, tol):
    npar = _NP[model]
    # data-driven starts: Emax/E ~ max |delta|, ED50/L ~ median dose
    doses = [d for d in (_agent_dose(nd, parse)[1] for nd in node_order) if d > 0]
    med = float(np.median(doses)) if doses else 1.0
    psi = np.tile([0.0, max(med, 1e-3)], len(agents)).astype(float)
    # crude E start from a saturated solve
    Xn = B_red
    sat = np.linalg.pinv(Xn.T @ W @ Xn, rcond=1e-14) @ (Xn.T @ W @ y)
    aidx = {a: j for j, a in enumerate(agents)}
    for j, a in enumerate(agents):
        vals = [sat[i] for i, nd in enumerate(node_order)
                if _agent_dose(nd, parse)[0] == a]
        psi[j * npar] = max(np.max(np.abs(vals)) * np.sign(np.mean(vals)), 1e-3) if vals else 0.1
    prev = np.inf
    converged = False
    for _ in range(max_iter):
        delta, Jd = _delta_and_jac(psi, node_order, parse, agents, model)
        resid = y - B_red @ delta
        G = B_red @ Jd                    # m x npsi
        GtW = G.T @ W
        A = GtW @ G
        step = np.linalg.solve(A + 1e-10 * np.eye(A.shape[0]), GtW @ resid)
        # damped update keeping scale params positive
        lam = 1.0
        for _bt in range(30):
            cand = psi + lam * step
            ok = all(cand[j * npar + 1] > 1e-8 for j in range(len(agents)))
            if ok:
                d2, _ = _delta_and_jac(cand, node_order, parse, agents, model)
                r2 = y - B_red @ d2
                obj = float(r2 @ W @ r2)
                if obj < prev or _bt == 29:
                    psi = cand
                    break
            lam *= 0.5
        obj = float((y - B_red @ _delta_and_jac(psi, node_order, parse, agents, model)[0])
                    @ W @ (y - B_red @ _delta_and_jac(psi, node_order, parse, agents, model)[0]))
        if abs(prev - obj) < tol:
            converged = True
            prev = obj
            break
        prev = obj
    delta, Jd = _delta_and_jac(psi, node_order, parse, agents, model)
    G = B_red @ Jd
    Vpsi = np.linalg.pinv(G.T @ W @ G, rcond=1e-14)
    return psi, Vpsi, converged, -0.5 * prev


def _unpack_psi(psi_vec, agents, model):
    if model in ("nma",):
        return {"delta_free": psi_vec.tolist()}
    if model == "linear":
        return {a: {"beta": float(psi_vec[j])} for j, a in enumerate(agents)}
    npar = _NP[model]
    names = {"exponential": ("E", "L"), "emax": ("Emax", "ED50")}[model]
    out = {}
    for j, a in enumerate(agents):
        p = psi_vec[j * npar:(j + 1) * npar]
        out[a] = {names[0]: float(p[0]), names[1]: float(p[1])}
    return out


def predict_dose(fit: MBNMAFit, agent, dose, parse=None):
    """Predicted effect of `agent` at `dose` vs reference, from fitted psi."""
    if fit.model == "linear":
        return fit.psi[agent]["beta"] * dose
    if fit.model == "exponential":
        p = (fit.psi[agent]["E"], fit.psi[agent]["L"])
        return _dr_value("exponential", dose, p)
    if fit.model == "emax":
        p = (fit.psi[agent]["Emax"], fit.psi[agent]["ED50"])
        return _dr_value("emax", dose, p)
    raise ValueError("predict_dose needs a parametric model")
