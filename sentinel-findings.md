# sentinel-findings.md

*Written by Sentinel — WARN-tier findings.*

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.774224+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.794662+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.835004+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.835042+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.840223+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.840285+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.841012+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.847085+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.847109+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.847124+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.854552+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.873114+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.927901+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.927928+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:19.961032+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.065673+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.318438+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.340627+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.355668+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373378+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373408+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373428+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373445+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373460+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373476+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373492+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:13:20.373508+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:13:22.030116+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:13:22.030116+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:13:22.030116+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:13:22.030116+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:13:22.030116+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.079426+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.079426+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:13:22.761393+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:13:24.187895+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:13:24.254132+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:13:31.279171+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.058776+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.072105+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.072135+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.076650+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.076707+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.082388+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.105873+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.105917+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.116901+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.134381+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142481+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142504+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142521+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142537+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142551+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142565+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142579+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.142606+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.152932+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.158001+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.168197+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.171562+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.181154+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.190559+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.204768+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.204789+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:15:30.204803+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:15:32.351318+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:15:32.351318+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:15:32.351318+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:15:32.351318+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:15:32.351318+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.413553+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.413553+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:15:32.999972+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:15:34.449498+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:15:34.685118+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:15:39.942520+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.909788+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.910540+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.910569+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.926938+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.926964+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.928999+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.934217+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938146+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938169+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938186+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938203+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938217+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938232+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938248+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.938261+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.942410+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.943041+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.947597+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:33.955767+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.004518+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.004540+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.004554+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.035909+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.041984+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.043337+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.043359+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:56:34.045456+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:56:36.520750+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:56:36.520750+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:56:36.520750+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:56:36.520750+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:56:36.520750+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:36.599744+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:36.599744+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:56:38.049928+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:56:39.620177+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:56:39.686037+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:56:45.142441+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.577184+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.585126+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.591979+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.592000+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.592015+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.594900+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.603165+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.628148+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.628277+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.632335+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.640725+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.640751+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.654737+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.654784+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.666469+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.667284+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.669707+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.678917+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.687973+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711483+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711507+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711524+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711539+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711554+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711568+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711583+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:13.711598+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:16.150739+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:16.150739+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:16.150739+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:16.150739+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:16.150739+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.207991+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.207991+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:16.924340+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:18.352221+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:57:18.421116+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:23.768958+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.383767+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.392329+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.393598+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.410034+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.410058+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.412260+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.412285+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.417680+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.417724+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.421875+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.423100+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.431947+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443759+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443779+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443795+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443809+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443822+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443835+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443849+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.443861+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.462157+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.507616+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.509162+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.530032+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.530061+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.530078+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:57:35.531677+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:37.298669+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:37.298669+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:37.298669+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:37.298669+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:57:37.298669+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:37.355324+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:37.355324+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:57:38.467459+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:57:40.068757+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:57:40.310060+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:57:48.333366+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:34`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.551344+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/test_nma.py:49`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.551402+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/agy_phase2_nma.py:38`
- **Detail:** pattern matched: scal = pd.read_csv(scalars_path).iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.569415+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_lor_expand.py:168`
- **Detail:** pattern matched: print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.571150+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/verify/codex_mahmood_nma.py:136`
- **Detail:** pattern matched: tau2 = float(scalars["tau2"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.573872+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:110`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.592870+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:113`
- **Detail:** pattern matched: return float(overall.loc[overall.method == method, "rmse"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.592892+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `scripts/reproduce_paper_results.py:118`
- **Detail:** pattern matched: return float(worst.loc[worst.method == method, "coverage"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.592917+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery-dta/dta_bakeoff.py:400`
- **Detail:** pattern matched: hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.605006+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/matched_coverage_bakeoff.py:351`
- **Detail:** pattern matched: hc0 = float(hc0.iloc[0]) if len(hc0) else None
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.610710+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/reference/test_netmeta_parity.py:53`
- **Detail:** pattern matched: scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.616360+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/xverify_codex_seatA/learned_verify.py:343`
- **Detail:** pattern matched: f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.618294+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:228`
- **Detail:** pattern matched: f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.620378+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/benchmark.py:229`
- **Detail:** pattern matched: f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.620401+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:49`
- **Detail:** pattern matched: h = sc[sc.method == "adaptshrink_ens"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625152+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:50`
- **Detail:** pattern matched: c = sc[sc.method == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625175+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:59`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625206+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:63`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is True
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625222+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:64`
- **Detail:** pattern matched: assert int(dom.iloc[0]["n_loss"]) == 0
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625236+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:71`
- **Detail:** pattern matched: v = pair[pair.comparator == "copas"].iloc[0]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625250+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:75`
- **Detail:** pattern matched: assert bool(dom.iloc[0]["dominates_field"]) is False
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625264+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/test_field_bakeoff.py:76`
- **Detail:** pattern matched: assert "copas" in dom.iloc[0]["loses_to"]
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.625278+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `nma/truth-recovery/nma_bakeoff.py:370`
- **Detail:** pattern matched: base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.627151+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `borrowing/field_scale/aact_expand.py:209`
- **Detail:** pattern matched: print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.641090+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:354`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.644189+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `doseresponse/drma.py:393`
- **Detail:** pattern matched: type_ = str(g[type_col].iloc[0])
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.644218+00:00

## [WARN] P1-empty-dataframe-access
- **Location:** `truth-recovery/field_rescore_interval.py:167`
- **Detail:** pattern matched: nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
- **Fix hint:** Guard with `if df.empty: return <sentinel>` or `if len(df) == 0: ...` immediately before the positional access, OR use `.iat[0]` / `.at[...]` with a prior existence check. If the file is a generator where this access is provably safe repo-wide, add `# sentinel:skip-file` near the top of the file.

- **Source:** MEMORY.md#top-5-cross-project-defects
- **When:** 2026-07-09T13:58:14.674307+00:00

## [WARN] P2-autogen-tracked
- **Location:** `DECISIONS.md`
- **Detail:** DECISIONS.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached DECISIONS.md` + append `DECISIONS.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:58:17.187301+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.jsonl`
- **Detail:** STUCK_FAILURES.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.jsonl` + append `STUCK_FAILURES.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:58:17.187301+00:00

## [WARN] P2-autogen-tracked
- **Location:** `STUCK_FAILURES.md`
- **Detail:** STUCK_FAILURES.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached STUCK_FAILURES.md` + append `STUCK_FAILURES.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:58:17.187301+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.jsonl`
- **Detail:** sentinel-findings.jsonl is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.jsonl` + append `sentinel-findings.jsonl` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:58:17.187301+00:00

## [WARN] P2-autogen-tracked
- **Location:** `sentinel-findings.md`
- **Detail:** sentinel-findings.md is auto-generated but tracked in git
- **Fix hint:** `git rm --cached sentinel-findings.md` + append `sentinel-findings.md` to .gitignore
- **Source:** lessons.md#portfolio-audit-patterns
- **When:** 2026-07-09T13:58:17.187301+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:204`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '4. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. *BMJ.* 199'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.240210+00:00

## [WARN] P0-citation-cascade
- **Location:** `manuscript/Transport_NMA.md:211`
- **Detail:** Reference line has author/year shape but no DOI/PMID/URL: '11. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequen'
- **Fix hint:** add a DOI (doi:10.X/Y), PMID, or canonical URL so the citation can be resolved through CrossRef / Semantic Scholar / OpenAlex per the Assurance Standard
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.240210+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_EXPANSION.md:48`
- **Detail:** document states 13 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_FIELD.md:437`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_BORROWING_REPLICATION.md:46`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `REPORT_DOSERESPONSE.md:114`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P=0.7') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT.md:134`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT2.md:15`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT3.md:20`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/REPORT_BORROWING_PILOT4.md:40`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `doseresponse/BORROWING_CONNECTION.md:72`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/AdaptShrink_StatMed.md:155`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `manuscript/Transport_NMA.md:22`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/NMA_PHASE2_REPORT.md:55`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/REPORT_NMA_PHASE2.md:35`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/SCOREBOARD_PHASE2.md:100`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 14 %') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `paper/manuscript.md:281`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/OPENDATA_SUFFICIENCY_REPORT.md:93`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `transport_nma/REPORT_TRANSPORT_NMA.md:144`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/NMA_SCOREBOARD.md:152`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REALHC_REPORT.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MAGNESIUM.md:9`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'OR 1.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `truth-recovery/REPORT_MATCHED_COVERAGE.md:179`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'P=0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_conformal_repair_wit.md:49`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'Odds Ratio):** $N_{\\text{LOR}} = 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_nma_inconsistency_wit.md:158`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup3_smallstudy_nma_deep.md:30`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'by 10%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup4_harmonize_review.md:57`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio from 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup5_dta_hsroc_deep.md:239`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p < 0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_aspirin.md:173`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'odds ratio of `-0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `verification/agy_sup_petpeese.md:78`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'by 94.4%') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `specs/doc-extraction/02-recommended-architecture.md:8`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/out/agy_xcheck_sufficiency.txt:16`
- **Detail:** document states 6 quantitative effect claim(s) (e.g. 'OR=0.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/sufficiency/agy_xcheck_prompt.txt:10`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.agy.txt:2`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_20958972.prompt.txt:9`
- **Detail:** document states 27 quantitative effect claim(s) (e.g. 'p = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_33191408.prompt.txt:9`
- **Detail:** document states 21 quantitative effect claim(s) (e.g. 'HR = 1.6') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/onc_40569207.prompt.txt:9`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.agy.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_26270946.prompt.txt:9`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_29626933.prompt.txt:9`
- **Detail:** document states 19 quantitative effect claim(s) (e.g. '95% CI 2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_32328953.prompt.txt:9`
- **Detail:** document states 15 quantitative effect claim(s) (e.g. 'OR 2.2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_34518159.prompt.txt:9`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/agy_xcheck/t2d_42014686.prompt.txt:9`
- **Detail:** document states 16 quantitative effect claim(s) (e.g. 'p < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_04.txt:28`
- **Detail:** document states 44 quantitative effect claim(s) (e.g. 'HR 2.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/onc_05.txt:21`
- **Detail:** document states 14 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_03.txt:21`
- **Detail:** document states 85 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_04.txt:27`
- **Detail:** document states 121 quantitative effect claim(s) (e.g. '3 Forest plot of the odds ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_prompts/t2d_05.txt:21`
- **Detail:** document states 34 quantitative effect claim(s) (e.g. '95% CI.') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_01.txt:6`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI: 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/onc_02.txt:9`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p = 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_01.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_04.txt:4`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/ft_raw/t2d_05.txt:136`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. '95% CI 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_00.txt:4`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'hazard ratio 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_01.txt:16`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'hazard ratio [HR], 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_02.txt:123`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. '15·1 vs 10·6 months; hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_03.txt:26`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'odds ratio, 0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_04.txt:10`
- **Detail:** document states 3 quantitative effect claim(s) (e.g. 'hazard ratio 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_05.txt:16`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'HR 0.9') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/onc_06.txt:2`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. '95% CI 8') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_02.txt:51`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_03.txt:10`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. 'P=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_04.txt:51`
- **Detail:** document states 7 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_05.txt:5`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p < .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_06.txt:54`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. '37 for placebo (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_07.txt:4`
- **Detail:** document states 8 quantitative effect claim(s) (e.g. 'P < 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_08.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. 'P = 0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_09.txt:3`
- **Detail:** document states 9 quantitative effect claim(s) (e.g. '2%) in the placebo group (hazard ratio') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_10.txt:3`
- **Detail:** document states 10 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_11.txt:12`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'P<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_12.txt:4`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'P = .0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_14.txt:8`
- **Detail:** document states 12 quantitative effect claim(s) (e.g. 'HR 0.3') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `regpub_pilot/data/llm_raw/t2d_15.txt:5`
- **Detail:** document states 5 quantitative effect claim(s) (e.g. '95% CI: 1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase2_mine_values.txt:3`
- **Detail:** document states 2 quantitative effect claim(s) (e.g. 'p=0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `nma/verify/phase3_verify_spec.md:54`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. '95% CI [2') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/bcg/REPORT_BORROWING_BCG.md:34`
- **Detail:** document states 4 quantitative effect claim(s) (e.g. 'p=0.1') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P1-claim-grounding
- **Location:** `borrowing/replication/REPORT_BORROWING_MULTISPECIALTY.md:16`
- **Detail:** document states 1 quantitative effect claim(s) (e.g. 'p<0.0') but carries no resolvable source identifier (DOI/PMID/NCT/URL) anywhere - the claims are ungrounded.
- **Fix hint:** add the DOI/PMID/NCT of the source each effect estimate comes from, or run the Overmind claim-grounding witness (overmind ground) to bind each claim to a corpus record
- **Source:** F:\e156\docs\assurance-standard.md#1-citation-verification
- **When:** 2026-07-09T13:58:17.882149+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:63`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:180`
- **Detail:** soft-overclaim word 'confirmed' — verify context is descriptive (e.g. 'confirmed cases') not causal (e.g. 'confirms the hypothesis')
- **Fix hint:** if context is causal, rewrite to 'supports' / 'is consistent with' / 'shows'. If descriptive, ignore.
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:72`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:79`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:80`
- **Detail:** causal-overclaim word 'eliminated' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:92`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:102`
- **Detail:** causal-overclaim word 'Proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:108`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:121`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:152`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:156`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P0-claim-language-workbook
- **Location:** `docs/EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md:158`
- **Detail:** causal-overclaim word 'proven' in rendered body — inappropriate for a 156-word meta-analytic claim
- **Fix hint:** rewrite the sentence with hedged language (e.g. 'consistent with', 'suggests', 'is associated with') and add an uncertainty qualifier if the evidence supports it
- **Source:** F:\e156\docs\assurance-standard.md#4-claim-language-checking
- **When:** 2026-07-09T13:58:19.341705+00:00

## [WARN] P1-cp1252-mojibake
- **Location:** `regpub_pilot/sufficiency/reviews.py:99`
- **Detail:** cp1252-mojibake of `—` (EM DASH) at line 99; 2 total recoverable sequence(s) in file — file was likely opened in a cp1252-defaulting editor and re-saved
- **Fix hint:** run `python F:/Sentinel/scripts/fix_cp1252_mojibake.py --repo <root> --apply` to repair in place, OR if the corruption dominates a diff `git checkout` the file and re-apply only the real change
- **Source:** lessons.md#portfolio-audit-patterns-learned-2026-04-16  (cp1252 save corruption — detect via mojibake)
- **When:** 2026-07-09T13:58:19.408304+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/aggregate_transport.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/agg/make_expansion_fig.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/prep_bcg.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/run_bcg.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/selfverify_bcg.py:11`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/bcg/xverify3_epan_jack.py:9`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_expand_ext.py:29`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_lor_expand.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/field_scale/aact_run_ext.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/prep_raudenbush.py:22`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/raudenbush/run_raudenbush.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate.py:12`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/aggregate_multispecialty.py:15`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/run_slice.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_slices.py:24`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/screen_v2.py:25`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_multispecialty.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/replication/selfverify_replication.py:13`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/prep_rota.py:36`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/run_rota.py:28`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/rota/selfverify_rota.py:14`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_doselink.py:26`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `borrowing/stage4_multi.py:20`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_emax_bakeoff.py:38`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `doseresponse/dr_target_dose.py:34`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_bp.py:16`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_corr_ci.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_depression_std.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_lipid.py:17`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/aact_kappa_sensitivity.py:19`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/export_records.py:10`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/tnma.py:40`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `transport_nma/transport_truthgate.py:64`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00

## [WARN] P1-module-stdout-reassign
- **Location:** `truth-recovery/magnesium_realtest.py:21`
- **Detail:** module-level `sys.stdout = io.TextIOWrapper(...)` without a `"pytest" not in sys.modules` guard — will corrupt pytest's I/O capture when imported
- **Fix hint:** Add `and "pytest" not in sys.modules` to the enclosing `if sys.platform == "win32":` condition, or move the reassignment inside a function called from main()
- **Source:** lessons.md#python-module--test-collection-traps  (Module-level sys.stdout reassignment kills pytest capture, 2026-04-16)
- **When:** 2026-07-09T13:58:24.790452+00:00
