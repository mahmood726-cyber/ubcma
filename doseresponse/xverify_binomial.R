# External gold-standard for the one-stage random-effects logistic dose-response
# (drma_binomial.fit_logistic_dr) on the real dose-toxicity slice dat.ursino2021.
# lme4::glmer with adaptive Gauss-Hermite quadrature is the reference; the Python
# fit must match its fixed effects, their SEs, and the study RE SD.
suppressWarnings(suppressMessages(library(lme4)))
d <- read.csv("F:/public-data/metadat/dat.ursino2021.csv")
d$dose100 <- d$dose / 100
d$fail <- d$total - d$events

cat("=== glmer random-intercept logistic dose-response, nAGQ=15 (PRIMARY reference) ===\n")
m <- glmer(cbind(events, fail) ~ dose100 + (1 | study), data = d,
           family = binomial, nAGQ = 15)
co <- summary(m)$coefficients
cat(sprintf("  b0 = %.7f (se %.7f)\n", co[1, 1], co[1, 2]))
cat(sprintf("  b1 = %.7f (se %.7f)   [logit per 100 dose-units]\n", co[2, 1], co[2, 2]))
cat(sprintf("  study RE SD sigma = %.7f\n", as.data.frame(VarCorr(m))$sdcor[1]))
cat(sprintf("  logLik = %.6f  (isSingular=%s)\n\n", as.numeric(logLik(m)), isSingular(m)))

cat("=== nAGQ sensitivity (should be stable; Laplace nAGQ=1 differs slightly) ===\n")
for (q in c(1, 7, 15, 25)) {
  mq <- glmer(cbind(events, fail) ~ dose100 + (1 | study), data = d,
              family = binomial, nAGQ = q)
  cq <- summary(mq)$coefficients
  cat(sprintf("  nAGQ=%2d : b1=%.7f  sigma=%.7f  logLik=%.5f\n",
              q, cq[2, 1], as.data.frame(VarCorr(mq))$sdcor[1], as.numeric(logLik(mq))))
}
