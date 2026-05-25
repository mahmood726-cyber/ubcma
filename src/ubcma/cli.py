from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .data import MetaAnalysisDataset
from .model import UBCMAFit
from .simulation import benchmark, generate_synthetic_meta_analysis


def _parse_csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UBCMA prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fit_parser = subparsers.add_parser("fit", help="Fit UBCMA to a CSV")
    fit_parser.add_argument("csv_path", type=Path)
    fit_parser.add_argument("--effect", default="yi")
    fit_parser.add_argument("--se", default="sei")
    fit_parser.add_argument("--quality", default=None)
    fit_parser.add_argument("--moderators", default=None)
    fit_parser.add_argument("--design", default=None)
    fit_parser.add_argument("--design-reference", default=None)
    fit_parser.add_argument("--study-id", default=None)
    fit_parser.add_argument("--n-restarts", type=int, default=20)
    fit_parser.add_argument("--profile-ci", action="store_true", help="Compute profile likelihood CI for mu")
    fit_parser.add_argument("--bootstrap", type=int, default=0, help="Number of bootstrap replicates (0=skip)")

    diag_parser = subparsers.add_parser("diagnose", help="Run diagnostics on a fitted model")
    diag_parser.add_argument("csv_path", type=Path)
    diag_parser.add_argument("--effect", default="yi")
    diag_parser.add_argument("--se", default="sei")
    diag_parser.add_argument("--quality", default=None)
    diag_parser.add_argument("--moderators", default=None)
    diag_parser.add_argument("--design", default=None)
    diag_parser.add_argument("--design-reference", default=None)
    diag_parser.add_argument("--study-id", default=None)

    bayes_parser = subparsers.add_parser("fit-bayes", help="Bayesian UBCMA fit via PyMC")
    bayes_parser.add_argument("csv_path", type=Path)
    bayes_parser.add_argument("--effect", default="yi")
    bayes_parser.add_argument("--se", default="sei")
    bayes_parser.add_argument("--quality", default=None)
    bayes_parser.add_argument("--moderators", default=None)
    bayes_parser.add_argument("--design", default=None)
    bayes_parser.add_argument("--design-reference", default=None)
    bayes_parser.add_argument("--study-id", default=None)
    bayes_parser.add_argument("--chains", type=int, default=4)
    bayes_parser.add_argument("--draws", type=int, default=2000)
    bayes_parser.add_argument("--tune", type=int, default=1000)
    bayes_parser.add_argument("--target-accept", type=float, default=0.9)
    bayes_parser.add_argument(
        "--prior-scale",
        default="weakly_informative",
        choices=["informative", "weakly_informative", "diffuse"],
    )
    bayes_parser.add_argument("--prior-sensitivity", action="store_true")

    sim_parser = subparsers.add_parser("simulate", help="Generate a synthetic dataset")
    sim_parser.add_argument("--output", type=Path, required=True)
    sim_parser.add_argument("--seed", type=int, default=42)
    sim_parser.add_argument(
        "--include-latent",
        action="store_true",
        help="Also write a *_full.csv file with latent truth used only for method development.",
    )

    study_parser = subparsers.add_parser("study", help="Run the simulation study")
    study_parser.add_argument("--tier", default="pilot", choices=["pilot", "focused", "full"])
    study_parser.add_argument("--replicates", type=int, default=50)
    study_parser.add_argument("--seed", type=int, default=42)
    study_parser.add_argument("--output", type=Path, default=Path("results"))
    study_parser.add_argument(
        "--methods",
        default="dl,dl_hksj,reml,reml_hksj,trim_and_fill,pet_peese,copas,quality_effects,ubcma",
    )

    bench_parser = subparsers.add_parser(
        "benchmark",
        help="Run a synthetic benchmark under aligned assumptions",
    )
    bench_parser.add_argument("--replicates", type=int, default=1)
    bench_parser.add_argument("--seed", type=int, default=42)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "fit":
        data = MetaAnalysisDataset.from_csv(
            args.csv_path,
            effect_col=args.effect,
            se_col=args.se,
            quality_cols=_parse_csv_list(args.quality),
            moderator_cols=_parse_csv_list(args.moderators),
            design_col=args.design,
            design_reference=args.design_reference,
            study_id_col=args.study_id,
        )
        fitter = UBCMAFit(n_restarts=args.n_restarts)
        result = fitter.fit(data)
        print(result.to_text())
        if args.profile_ci:
            from .inference import profile_likelihood_ci
            ci = profile_likelihood_ci(result, data, fitter)
            print(f"\nProfile likelihood 95% CI for mu: [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")
        if args.bootstrap > 0:
            from .inference import bootstrap_ci
            bci = bootstrap_ci(data, fitter, n_boot=args.bootstrap)
            print(f"Bootstrap 95% CI for mu: [{bci['ci_low']:.4f}, {bci['ci_high']:.4f}] ({bci['n_failed']} failed)")
        print()
        print(result.study_table().to_string(index=False))
        return

    if args.command == "diagnose":
        data = MetaAnalysisDataset.from_csv(
            args.csv_path,
            effect_col=args.effect,
            se_col=args.se,
            quality_cols=_parse_csv_list(args.quality),
            moderator_cols=_parse_csv_list(args.moderators),
            design_col=args.design,
            design_reference=args.design_reference,
            study_id_col=args.study_id,
        )
        fitter = UBCMAFit(n_restarts=5)
        result = fitter.fit(data, allow_failed=True)
        from .diagnostics import (
            information_criteria,
            leave_one_out,
            standardized_residuals,
        )
        ic = information_criteria(result, data, fitter)
        print("Information criteria:")
        for model_name, vals in ic.items():
            print(f"  {model_name}: AIC={vals['aic']:.1f}  BIC={vals['bic']:.1f}  k={vals['n_params']}")
        resid = standardized_residuals(result)
        print(f"\nResiduals: mean={float(np.mean(resid)):.3f} sd={float(np.std(resid)):.3f}")
        print("\nLeave-one-out influence:")
        loo = leave_one_out(result, data, fitter)
        print(loo.to_string(index=False))
        return

    if args.command == "fit-bayes":
        from .bayesian import BayesianUBCMAFit as _BayesFitter
        data = MetaAnalysisDataset.from_csv(
            args.csv_path,
            effect_col=args.effect,
            se_col=args.se,
            quality_cols=_parse_csv_list(args.quality),
            moderator_cols=_parse_csv_list(args.moderators),
            design_col=args.design,
            design_reference=args.design_reference,
            study_id_col=args.study_id,
        )
        scale_map = {"informative": 0.5, "weakly_informative": 1.0, "diffuse": 3.0}
        fitter = _BayesFitter()
        if args.prior_sensitivity:
            results = fitter.prior_sensitivity(
                data, chains=args.chains, draws=args.draws, tune=args.tune
            )
            for name, res in results.items():
                print(f"\n--- {name} (scale={scale_map[name]}) ---")
                print(res.to_text())
        else:
            result = fitter.fit(
                data,
                chains=args.chains,
                draws=args.draws,
                tune=args.tune,
                target_accept=args.target_accept,
                prior_scale=scale_map[args.prior_scale],
            )
            print(result.to_text())
        return

    if args.command == "simulate":
        published, full = generate_synthetic_meta_analysis(seed=args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        published.to_csv(args.output, index=False)
        print(f"saved published dataset to {args.output}")
        if args.include_latent:
            full_path = args.output.with_name(args.output.stem + "_full.csv")
            full.to_csv(full_path, index=False)
            print(f"saved latent development dataset to {full_path}")
        return

    if args.command == "study":
        from .simulation_study import compute_metrics, format_table, run_tier
        methods = [m.strip() for m in args.methods.split(",")]
        output_dir = str(args.output / args.tier)
        full_df = run_tier(args.tier, methods, args.replicates, args.seed, output_dir)
        metrics = compute_metrics(full_df)
        print(f"\n{format_table(metrics)}")
        print(f"\nResults saved to {output_dir}")
        return

    if args.command == "benchmark":
        result = benchmark(
            replicates=args.replicates,
            seed=args.seed,
            progress=True,
        )
        print(result.to_string(index=False))
        print()
        print(result[["ubcma_bias", "wls_bias"]].mean().rename("mean_bias").to_string())
        print()
        print(result[["ubcma_bias", "wls_bias"]].abs().mean().rename("mean_abs_bias").to_string())
        print()
        print("note: this benchmark is an aligned synthetic check, not broad comparative evidence.")
        return

    raise RuntimeError(f"Unhandled command: {args.command}")
