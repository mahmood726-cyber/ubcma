# Generate reference Henmi-Copas (2010) CIs from metafor::hc for validating the
# Python port in src/ubcma/robust_methods.py:henmi_copas.
# Usage: R_LIBS_USER=<userlib> Rscript truth-recovery/validate_henmi_copas.R
.libPaths(Sys.getenv("R_LIBS_USER"))
suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

set.seed(20260620)
datasets <- list()
for (d in 1:25) {
  k <- sample(5:40, 1)
  se <- runif(k, 0.05, 0.40)
  vi <- se^2
  tau <- runif(1, 0, 0.30)
  yi <- rnorm(k, 0.20 + rnorm(k, 0, tau), se)
  res <- rma(yi = yi, vi = vi, method = "DL")
  hcres <- hc(res, level = 95, control = list(tol = 1e-12, maxiter = 100000))
  datasets[[d]] <- list(
    yi = yi, vi = vi,
    beta = hcres$beta, se = hcres$se,
    ci_lb = hcres$ci.lb, ci_ub = hcres$ci.ub
  )
}
writeLines(toJSON(datasets, digits = 12, auto_unbox = TRUE),
           "truth-recovery/hc_reference.json")
cat("wrote truth-recovery/hc_reference.json with", length(datasets), "datasets\n")
