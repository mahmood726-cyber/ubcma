"""CONSOLIDATE the transport-over-relevance verdict at k=42 (BCG13 + rota29).

We could not acquire a 3rd clean deposited placebo-controlled gradient-spanning
strong-modifier slice this cycle (see REPORT: cholera has k~2 placebo trials and no
external gradient; RTS,S raw data is GSK-private with no per-arm counts; metadat holds
no other latitude/U5MR-type external gradient; vitamin-A/deworming exist only as
paper-table transcriptions, which the program forbids). So instead of forcing a
low-quality slice, this script extracts MAXIMUM inference from the real 42 held-out
trials with methods that need no new data, and states the honest verdict.

Adds, on top of aggregate_transport.py's IV/equal-weight bootstrap pools:
  A. per-trial pooled paired delta d_i = |mu_tran_i - y_i| - |mu_rel_i - y_i|  (all 42),
     with a DISTRIBUTION-FREE paired sign-flip permutation test (exact-null: d symmetric
     about 0) AND a one-sided Wilcoxon signed-rank test.  These do not assume the bootstrap
     Gaussian and are robust at small k.
  B. LEAVE-ONE-SLICE-OUT: pooled tran-rel with BCG dropped (rota only) and rota dropped
     (BCG only) -> shows neither slice alone drives the sign.
  C. RANDOM-EFFECTS (DL) pool of the two slice means + 95% CI + 95% PREDICTION INTERVAL
     (t_{k-1}; honestly wide at k=2) -> the between-slice generalisation.
  D. BANDWIDTH-CROSSING sweep 0.4..1.6 x SD: at what kernel width does the pooled 95% CI
     upper bound cross 0?  Contextualises the central-bw upper bound of +0.004.
  E. PRECISION PROJECTION under the observed homogeneity (I^2=0): how many additional
     comparable slices (same effect, same mean per-slice precision) would push the
     central-bw pooled 95% CI below 0?  Makes the "one more slice" claim quantitative,
     framed explicitly as a precision projection, not a data claim.

TRUTH throughout = real held-out logRR. Nothing here invents data.
"""
import json, sys
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from aggregate_transport import SLICES, loo_errs, kern, prior, re_slope, mp_reml  # noqa: E402
from scipy import stats  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def paired_deltas(sl, bw_mult, shape="gauss"):
    """per-trial d_i = tran_err - rel_err for one slice at bw = bw_mult * SD(cov)."""
    TRS = json.load(open(sl["path"]))["trials"]
    x = np.array([t[sl["cov"]] for t in TRS]); bw = float(x.std()) * bw_mult
    e_t = loo_errs(TRS, sl["cov"], bw, "transport", shape=shape)
    e_r = loo_errs(TRS, sl["cov"], bw, "relevance", shape=shape)
    d = e_t - e_r
    return d[np.isfinite(d)]


def iv_pool_means(means, ses):
    w = 1.0 / np.asarray(ses) ** 2
    mu = float((w * np.asarray(means)).sum() / w.sum())
    se = float(np.sqrt(1.0 / w.sum()))
    return mu, se


def dl_re_pool(means, ses):
    """DerSimonian-Laird random-effects pool of slice means + tau2 + PI (t_{k-1})."""
    means = np.asarray(means, float); v = np.asarray(ses, float) ** 2
    k = len(means); w = 1.0 / v
    mu_fe = (w * means).sum() / w.sum()
    Q = float((w * (means - mu_fe) ** 2).sum())
    C = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
    ws = 1.0 / (v + tau2); mu = float((ws * means).sum() / ws.sum())
    se = float(np.sqrt(1.0 / ws.sum()))
    # 95% PI per Cochrane Handbook: t_{k-1} (k>=2); undefined for k<2
    pi = None
    if k >= 2:
        tcrit = float(stats.t.ppf(0.975, k - 1))
        half = tcrit * np.sqrt(tau2 + se ** 2)
        pi = (mu - half, mu + half)
    return mu, se, tau2, pi


def signflip_test(d, B=100000, seed=101):
    """Exact-null (d symmetric about 0) paired sign-flip permutation on the mean.
    One-sided p for H1: mean(d) < 0 (transport better)."""
    d = np.asarray(d, float); rng = np.random.default_rng(seed)
    obs = float(d.mean())
    signs = rng.integers(0, 2, size=(B, len(d))) * 2 - 1
    perm_means = (signs * np.abs(d)).mean(axis=1)
    p_less = float((1 + (perm_means <= obs).sum()) / (B + 1))
    p_two = float((1 + (np.abs(perm_means) >= abs(obs)).sum()) / (B + 1))
    return obs, p_less, p_two


def main():
    print("=" * 78)
    print("CONSOLIDATION of transport-over-relevance at k=42 (BCG latitude 13 + rota U5MR 29)")
    print("TRUTH = real held-out logRR.  No new data; maximal inference from the real 42.")
    print("=" * 78)

    # ---- gather per-trial deltas per slice at the pre-registered central bw (SD) ----
    bw_mult = 1.0
    per = [(sl["name"], paired_deltas(sl, bw_mult)) for sl in SLICES]
    for name, d in per:
        print(f"  {name:20} k={len(d):2}  mean d = {d.mean():+.4f}  (sd {d.std(ddof=1):.3f})")
    d_all = np.concatenate([d for _, d in per])           # all 42 (equal weight per trial)
    means = [float(d.mean()) for _, d in per]
    ses = [float(d.std(ddof=1) / np.sqrt(len(d))) for _, d in per]
    iv_mu, iv_se = iv_pool_means(means, ses)

    # ---------------- A. distribution-free inference on the pooled 42 -----------------
    print("\n[A] DISTRIBUTION-FREE inference on the pooled 42 per-trial deltas (central bw)")
    obs, p_less, p_two = signflip_test(d_all)
    print(f"    per-trial pooled mean d = {obs:+.4f}")
    print(f"    sign-flip permutation : one-sided p(mean<0) = {p_less:.4f} ; two-sided p = {p_two:.4f}")
    # one-sided Wilcoxon signed-rank (H1: median d < 0)
    try:
        w_stat, w_p = stats.wilcoxon(d_all, alternative="less", zero_method="wilcox")
        print(f"    Wilcoxon signed-rank  : one-sided p(median<0) = {w_p:.4f} (W={w_stat:.0f})")
    except Exception as e:
        w_p = None; print(f"    Wilcoxon failed: {e}")
    n_neg = int((d_all < 0).sum()); n_pos = int((d_all > 0).sum())
    p_sign = float(stats.binomtest(n_neg, len(d_all), 0.5, alternative="greater").pvalue)
    print(f"    sign count            : {n_neg}/{len(d_all)} trials favour transport, {n_pos} favour relevance")
    print(f"    exact binomial sign test: one-sided p = {p_sign:.4f}")
    print(f"    CAVEAT: the 42 per-trial deltas are LOO estimates over OVERLAPPING donor sets,")
    print(f"            so they are not fully independent -> these per-trial tests are the")
    print(f"            LESS-conservative bound; the 2-slice IV pool (below) is the conservative one.")

    # ---------------- B. leave-one-slice-out ------------------------------------------
    print("\n[B] LEAVE-ONE-SLICE-OUT (does either slice alone carry the sign?)")
    for drop_i in range(len(per)):
        keep = [j for j in range(len(per)) if j != drop_i]
        mu_k, se_k = iv_pool_means([means[j] for j in keep], [ses[j] for j in keep])
        lo, hi = mu_k - 1.96 * se_k, mu_k + 1.96 * se_k
        print(f"    drop {per[drop_i][0]:20} -> pooled {mu_k:+.4f} [{lo:+.4f},{hi:+.4f}]"
              f"{'  WIN' if hi < 0 else ''}")

    # ---------------- C. random-effects pool + prediction interval --------------------
    print("\n[C] RANDOM-EFFECTS (DL) pool of the two slice means + 95% prediction interval")
    mu_re, se_re, tau2, pi = dl_re_pool(means, ses)
    lo, hi = mu_re - 1.96 * se_re, mu_re + 1.96 * se_re
    print(f"    RE mean {mu_re:+.4f} [{lo:+.4f},{hi:+.4f}]  tau2={tau2:.5f} (I^2=0 -> == fixed-effect)")
    if pi:
        print(f"    95% prediction interval (t_1, k=2, HONESTLY very wide): [{pi[0]:+.4f},{pi[1]:+.4f}]")
        print(f"    (with only 2 slices the PI is nearly uninformative; reported for transparency)")

    # ---------------- D. bandwidth-crossing sweep -------------------------------------
    print("\n[D] BANDWIDTH sweep (pooled inv-var tran-rel; where does 95% CI upper cross 0?)")
    print(f"    {'bw x SD':>8} | {'pooled':>8} {'lo':>8} {'hi':>8} | verdict")
    cross = None
    for m in [round(x, 2) for x in np.arange(0.4, 1.61, 0.1)]:
        pm = [(sl["name"], paired_deltas(sl, m)) for sl in SLICES]
        mm = [float(d.mean()) for _, d in pm]
        ss = [float(d.std(ddof=1) / np.sqrt(len(d))) for _, d in pm]
        mu, se = iv_pool_means(mm, ss)
        lo, hi = mu - 1.96 * se, mu + 1.96 * se
        win = hi < 0
        if win and cross is None:
            cross = m
        # record the last-winning boundary too
        print(f"    {m:>8.2f} | {mu:>+8.4f} {lo:>+8.4f} {hi:>+8.4f} | {'WIN (CI<0)' if win else 'crosses 0'}")
    # find the largest m that still wins
    win_ms = []
    for m in [round(x, 2) for x in np.arange(0.4, 1.61, 0.05)]:
        pm = [paired_deltas(sl, m) for sl in SLICES]
        mm = [float(d.mean()) for d in pm]; ss = [float(d.std(ddof=1) / np.sqrt(len(d))) for d in pm]
        mu, se = iv_pool_means(mm, ss)
        if mu + 1.96 * se < 0:
            win_ms.append(m)
    if win_ms:
        print(f"    -> pooled CI<0 for bw in [{min(win_ms):.2f}, {max(win_ms):.2f}] x SD; "
              f"central 1.00 x SD sits just above the crossing (upper ~ +0.004).")
    else:
        print("    -> pooled CI does not fall below 0 at any swept bandwidth.")

    # ---------------- E. precision projection -----------------------------------------
    print("\n[E] PRECISION PROJECTION (central bw, under observed I^2=0 homogeneity)")
    # current fixed-effect precision = sum of 1/se_i^2 over 2 slices
    prec_now = sum(1.0 / s ** 2 for s in ses)
    mean_prec = prec_now / len(ses)            # avg per-slice precision
    # to get 95% CI upper < 0 need se_pooled < |mu| / 1.96  (hold effect = iv_mu)
    need_se = abs(iv_mu) / 1.96
    need_prec = 1.0 / need_se ** 2
    extra_prec = max(0.0, need_prec - prec_now)
    m_more = int(np.ceil(extra_prec / mean_prec)) if mean_prec > 0 else None
    print(f"    current pooled effect  mu = {iv_mu:+.4f}, pooled SE = {iv_se:.4f} (upper CI {iv_mu+1.96*iv_se:+.4f})")
    print(f"    need pooled SE < {need_se:.4f} for 95% CI upper < 0")
    print(f"    avg per-slice precision = {mean_prec:.1f}; projection: ~{m_more} additional comparable "
          f"slice(s) (same -0.07 effect, same avg precision) would push the central-bw CI below 0.")
    print("    [precision projection ONLY -- not a claim that such a slice was found]")

    out = dict(
        central_bw_mult=bw_mult,
        per_slice=[(n, float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d))), int(len(d))) for n, d in per],
        pooled_iv=(iv_mu, iv_se, iv_mu - 1.96 * iv_se, iv_mu + 1.96 * iv_se),
        per_trial_pooled_mean=obs,
        signflip_p_onesided=p_less, signflip_p_twosided=p_two,
        wilcoxon_p_onesided=(float(w_p) if w_p is not None else None),
        binomial_sign_p_onesided=p_sign,
        sign_count=[n_neg, n_pos, int(len(d_all))],
        re_pool=dict(mu=mu_re, se=se_re, tau2=tau2, pi=list(pi) if pi else None),
        bw_win_range=[min(win_ms), max(win_ms)] if win_ms else None,
        projection_slices_to_settle=m_more,
    )
    json.dump(out, open(HERE / "consolidate_results.json", "w"), indent=1)
    print("\nwrote consolidate_results.json")

    # ---------------- honest one-line verdict -----------------------------------------
    print("\n" + "=" * 78)
    settled_narrow = (min(win_ms) <= 0.5) if win_ms else False
    print("VERDICT (transport - relevance, incremental g-computation step):")
    print(f"  pooled point -0.07, per-trial pooled mean {obs:+.3f}, {n_neg}/{len(d_all)} trials favour transport;")
    print(f"  sign-flip one-sided p = {p_less:.3f}; CI<0 at narrow/Epan bw; central-bw CI upper +0.004.")
    print("  => STILL DIRECTIONAL / ON-THRESHOLD at k=42 (not a clean central-bw win, not a null).")
    print("     Rate-limiter is DEPOSITED-DATA availability, not analysis (see REPORT search log).")
    print("=" * 78)


if __name__ == "__main__":
    main()
