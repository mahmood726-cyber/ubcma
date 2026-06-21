# validate_hsroc.R -- exact bivariate GLMM reference for the HSROC comparator.
#
# The Rutter-Gatsonis HSROC model is (Harbord 2007) a reparameterization of the
# bivariate generalized linear mixed model (Chu & Cole 2006) fit by the EXACT
# binomial likelihood -- as distinct from mada::reitsma, which uses the within-
# study normal approximation on the logit scale. The summary operating point
# (logit Se, logit Sp) must agree between the in-repo HSROC fit and lme4::glmer.
#
# This produces the gold-standard (Se,Sp) reference; the Python HSROC fit is
# checked against it in test_dta.py and verify_*.
suppressMessages({library(lme4); library(jsonlite)})

dat <- read.csv("truth-recovery-dta/canonical_counts.csv")
out <- list()
for (ds in unique(dat$dataset)) {
  d <- dat[dat$dataset == ds, ]
  # long format: 2 rows per study (sens row uses TP/FN; spec row uses TN/FP)
  long <- data.frame(
    study = rep(d$study, 2),
    grp   = factor(rep(c("sens", "spec"), each = nrow(d)), levels = c("sens","spec")),
    pos   = c(d$tp, d$tn),
    neg   = c(d$fn, d$fp)
  )
  fit <- tryCatch(
    glmer(cbind(pos, neg) ~ 0 + grp + (0 + grp | study),
          data = long, family = binomial,
          control = glmerControl(optimizer = "bobyqa",
                                  optCtrl = list(maxfun = 2e5))),
    error = function(e) NULL)
  if (is.null(fit)) { out[[ds]] <- list(ok = FALSE); next }
  fe <- fixef(fit)
  m1 <- as.numeric(fe["grpsens"]); m2 <- as.numeric(fe["grpspec"])
  vc <- VarCorr(fit)$study
  out[[ds]] <- list(
    ok = TRUE, k = nrow(d),
    m1_logit_sens = m1, m2_logit_spec = m2,
    sens_summary = plogis(m1), spec_summary = plogis(m2),
    tau_sens = sqrt(vc[1, 1]), tau_spec = sqrt(vc[2, 2]),
    rho = vc[1, 2] / sqrt(vc[1, 1] * vc[2, 2]))
  cat(sprintf("%-12s k=%2d glmm Se/Sp = %.4f / %.4f  (tau %.3f/%.3f rho %+.3f)\n",
              ds, nrow(d), plogis(m1), plogis(m2),
              sqrt(vc[1,1]), sqrt(vc[2,2]), vc[1,2]/sqrt(vc[1,1]*vc[2,2])))
}
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, digits = 10),
           "truth-recovery-dta/reference_glmm.json")
cat("wrote reference_glmm.json\n")
