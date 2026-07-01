suppressMessages({ok <- require(metafor, quietly=TRUE)})
if(!ok){cat("NO_METAFOR\n"); quit(status=0)}
d <- read.csv("F:/public-data/metadat/dat.bcg.csv")
# per-trial logRR + SE from 2x2 (escalc measure RR)
es <- escalc(measure="RR", ai=tpos, bi=tneg, ci=cpos, di=cneg, data=d)
cat(sprintf("metafor escalc logRR range: %.3f..%.3f  SE range: %.3f..%.3f\n",
            min(es$yi), max(es$yi), min(sqrt(es$vi)), max(sqrt(es$vi))))
# random-effects meta-regression on absolute latitude
m <- rma(yi, vi, mods=~ablat, data=es, method="REML")
cat(sprintf("metafor RE meta-reg: slope=%.4f  z=%.2f  p=%.4g  tau2=%.4f  R2=%.1f%%\n",
            coef(m)["ablat"], m$zval[2], m$pval[2], m$tau2, m$R2))
set.seed(20260630)
pm <- permutest(m, iter=5000)
cat(sprintf("metafor permutest p(ablat)=%.4f\n", pm$pval[2]))
