# EXTERNAL cross-check of the rotavirus U5MR modifier with metafor (independent engine).
# Reads rota_trials.json, recomputes logRR from the raw 2x2-ish counts with escalc,
# and fits an REML meta-regression of logRR on U5MR + a permutation test. Must match
# prep_rota.py's slope sign/magnitude and confirm the modifier is strong.
suppressMessages(library(metafor)); suppressMessages(library(jsonlite))
d <- fromJSON("F:/ubcma/borrowing/rota/rota_trials.json")$trials

# escalc log risk-ratio from cases/N (measure RR); continuity handled by metafor add=.5 to 0 cells
es <- escalc(measure="RR", ai=round(d$a), n1i=round(d$n1), ci=round(d$c), n2i=round(d$n2),
             add=1/2, to="only0")
d$yi <- es$yi; d$vi <- es$vi

cat(sprintf("k=%d  U5MR %.0f-%.0f\n", nrow(d), min(d$u5mr), max(d$u5mr)))
m0 <- rma(yi, vi, data=d, method="REML")
m1 <- rma(yi, vi, mods=~u5mr, data=d, method="REML")
cat(sprintf("REML meta-reg logRR ~ U5MR: slope=%.5f  se=%.5f  z=%.2f  p=%.4g  R2=%.1f%%\n",
            coef(m1)[2], m1$se[2], m1$zval[2], m1$pval[2], m1$R2))
set.seed(20260701)
pm <- permutest(m1, iter=5000)
cat(sprintf("permutest slope p = %.4g\n", pm$pval[2]))
# adjust for follow-up + product
m2 <- rma(yi, vi, mods=~u5mr+fu_end+factor(vaccine), data=d, method="REML")
cat(sprintf("adjusted (U5MR+fu+product): U5MR slope=%.5f p=%.4g\n", coef(m2)[2], m2$pval[2]))
