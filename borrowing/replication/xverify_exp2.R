suppressMessages(library(metafor))
r <- read.csv("F:/public-data/metadat/dat.raudenbush1985.csv")
m <- rma(yi, vi, mods=~weeks, data=r, method="REML")
cat(sprintf("raudenbush  weeks slope=%.4f z=%.2f p=%.4g  permp=%.4f\n",
    coef(m)["weeks"], m$zval[2], m$pval[2], permutest(m,iter=5000)$pval[2]))
k <- read.csv("F:/public-data/metadat/dat.kalaian1996.csv"); k <- k[!is.na(k$hrs),]
mk <- rma(yi, vi, mods=~hrs, data=k, method="REML")
cat(sprintf("kalaian     hrs   slope=%.4f z=%.2f p=%.4g  permp=%.4f\n",
    coef(mk)["hrs"], mk$zval[2], mk$pval[2], permutest(mk,iter=5000)$pval[2]))
