"""sim_network.py -- synthetic dose-response networks for MBNMA validation.

Generates (agent, dose) networks with multi-arm studies and a known dose-
response truth. Two uses:
  * one fixed seeded dataset -> netmeta common-effect gold (saturated reduction).
  * many replicates with known linear/Emax truth -> parameter-recovery checks.

Node labels are "agent@dose"; placebo is "plac@0".
"""
from __future__ import annotations

import numpy as np

AGENTS = {
    "A": [1.0, 2.0, 4.0, 8.0],
    "B": [0.5, 1.0, 2.0],
}
REF = "plac@0"


def node_label(agent, dose):
    return f"{agent}@{dose:g}"


def parse_node(label):
    a, d = label.split("@")
    return a, float(d)


def true_delta(model, params, agent, dose):
    if agent == "plac" or dose == 0:
        return 0.0
    p = params[agent]
    if model == "linear":
        return p["beta"] * dose
    if model == "emax":
        return p["Emax"] * dose / (p["ED50"] + dose)
    if model == "exponential":
        return p["E"] * (1.0 - np.exp(-dose / p["L"]))
    raise ValueError(model)


def make_network(seed, model, params, n_studies=40, tau=0.0, arm_se=0.18):
    """Return (contrasts, truth_nodes). contrasts = list of (studlab,t1,t2,TE,seTE).

    Each study: reference arm + 1-2 active arms (multi-arm to exercise the
    shared-arm correlation). Arm means = true node delta + study RE + noise.
    """
    rng = np.random.default_rng(seed)
    nodes = [REF] + [node_label(a, d) for a, doses in AGENTS.items() for d in doses]
    truth = {nd: true_delta(model, params, *parse_node(nd)) for nd in nodes}
    contrasts = []
    for s in range(n_studies):
        # pick reference arm (often placebo) + active arms
        active = [nd for nd in nodes if nd != REF]
        k_active = rng.integers(1, 3)  # 1 or 2 active arms -> 2- or 3-arm study
        chosen = list(rng.choice(active, size=k_active, replace=False))
        arms = [REF] + chosen
        study_re = rng.normal(0, tau) if tau > 0 else 0.0
        means, ses = {}, {}
        for nd in arms:
            se = arm_se * (0.7 + 0.6 * rng.random())
            mean = truth[nd] + study_re + rng.normal(0, se)
            means[nd] = mean
            ses[nd] = se
        # emit ALL pairwise contrasts (netmeta requires the full set for
        # multi-arm studies; arm-level means keep them mutually consistent).
        for i in range(len(arms)):
            for j in range(i + 1, len(arms)):
                t1, t2 = arms[j], arms[i]
                te = means[t1] - means[t2]
                sete = float(np.sqrt(ses[t1] ** 2 + ses[t2] ** 2))
                contrasts.append((f"S{s}", t1, t2, float(te), sete))
    return contrasts, truth


def write_contrasts_csv(contrasts, path):
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["studlab", "treat1", "treat2", "TE", "seTE"])
        for studlab, t1, t2, te, se in contrasts:
            w.writerow([studlab, t1, t2, te, se])


if __name__ == "__main__":
    # fixed gold dataset (Emax truth, but the reduction test is truth-agnostic)
    params = {"A": {"Emax": 0.9, "ED50": 2.0}, "B": {"Emax": 0.6, "ED50": 1.0}}
    contrasts, truth = make_network(seed=20260630, model="emax", params=params,
                                    n_studies=45, tau=0.0)
    write_contrasts_csv(contrasts, "reference/mbnma_contrasts.csv")
    print(f"wrote {len(contrasts)} contrasts; nodes={list(truth)}")
