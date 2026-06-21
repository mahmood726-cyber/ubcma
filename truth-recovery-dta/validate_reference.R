# Reference DTA fits for validating the Python bivariate estimator.
# Exports canonical 2x2 datasets + mada::reitsma summary estimates to JSON.
suppressMessages({library(mada); library(jsonlite)})

emit <- function(name, d) {
  # d must have columns TP, FP, FN, TN
  fit <- reitsma(d, method = "ml")           # ML to match the Python ML fit
  s <- summary(fit)
  co <- coef(fit)                             # matrix: row "(Intercept)", cols tsens/tfpr
  # mada models logit(sens) and logit(FPR)=logit(1-spec).
  m1 <- as.numeric(co["(Intercept)", "tsens"])  # logit sens
  m_fpr <- as.numeric(co["(Intercept)", "tfpr"]) # logit FPR
  m2 <- -m_fpr                                 # logit spec = -logit FPR
  V <- vcov(fit)[1:2, 1:2]                     # cov of (logit sens, logit fpr)
  Sig <- fit$Psi                              # between-study covariance (sens, fpr)
  list(
    name = name,
    counts = list(TP = d$TP, FP = d$FP, FN = d$FN, TN = d$TN),
    m1_logit_sens = m1,
    m2_logit_spec = m2,
    sens_summary = plogis(m1),
    spec_summary = plogis(m2),
    V_sens_fpr = as.numeric(V),               # 2x2 row-major (sens, fpr)
    Psi_sens_fpr = as.numeric(Sig),
    auc = as.numeric(s$AUC$AUC)
  )
}

out <- list()

# Canonical mada datasets (all carry TP/FN/FP/TN columns).
for (nm in c("AuditC", "smoking", "Dementia", "skin_tests", "SAQ")) {
  d <- tryCatch({ data(list = nm, package = "mada"); get(nm) },
                error = function(e) NULL)
  if (is.null(d)) { cat("skip", nm, "(not found)\n"); next }
  cn <- toupper(names(d)); names(d) <- cn
  if (!all(c("TP", "FN", "FP", "TN") %in% cn)) {
    cat("skip", nm, "(no 2x2 cols)\n"); next
  }
  fit <- tryCatch(emit(nm, data.frame(TP=d$TP, FP=d$FP, FN=d$FN, TN=d$TN)),
                  error = function(e) { cat("fit fail", nm, ":", conditionMessage(e), "\n"); NULL })
  if (!is.null(fit)) out[[nm]] <- fit
}

writeLines(toJSON(out, auto_unbox = TRUE, digits = 10),
           "truth-recovery-dta/reference_fits.json")
cat("wrote truth-recovery-dta/reference_fits.json\n")
for (nm in names(out)) {
  o <- out[[nm]]
  cat(sprintf("%-12s sens=%.5f spec=%.5f m1=%.5f m2=%.5f auc=%.4f k=%d\n",
              nm, o$sens_summary, o$spec_summary, o$m1_logit_sens,
              o$m2_logit_spec, o$auc, length(o$counts$TP)))
}
