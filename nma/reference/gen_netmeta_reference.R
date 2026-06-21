# Generate netmeta reference outputs for canonical NMA networks.
# Outputs CSVs consumed by nma/reference/test_netmeta_parity.py to validate the
# Python graph-theoretic NMA engine to ~1e-6.
#
# Networks:
#   senn2013        : diabetes, contrast format, MULTI-ARM (mean differences)
#   smoking         : Hasselblad 1998 smoking cessation, arm-level binary -> logOR
#
# For each: dump the input contrasts (post-pairwise), per-comparison TE/seTE,
# tau2 (DL), Q/df, and the full league tables (common + random) of basic
# parameters vs reference.
suppressMessages(library(netmeta))
outdir <- file.path("nma", "reference")
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

dump_net <- function(net, tag) {
  # Treatment-effect matrices (TE, seTE) vs all treatments, common + random.
  write.csv(round(net$TE.common, 10),  file.path(outdir, paste0(tag, "_TE_common.csv")))
  write.csv(round(net$seTE.common, 10),file.path(outdir, paste0(tag, "_seTE_common.csv")))
  write.csv(round(net$TE.random, 10),  file.path(outdir, paste0(tag, "_TE_random.csv")))
  write.csv(round(net$seTE.random, 10),file.path(outdir, paste0(tag, "_seTE_random.csv")))
  # Scalars: tau2, tau, Q, df, I2.
  scal <- data.frame(
    tag = tag,
    k = net$k, m = net$m, n = net$n,
    tau2 = net$tau2, tau = net$tau,
    Q = net$Q, df.Q = net$df.Q,
    I2 = net$I2,
    reference.group = net$reference.group
  )
  write.csv(scal, file.path(outdir, paste0(tag, "_scalars.csv")), row.names = FALSE)
  cat(sprintf("[%s] n=%d treatments, k=%d studies, m=%d comparisons; tau2=%.8f Q=%.6f df=%d\n",
              tag, net$n, net$k, net$m, net$tau2, net$Q, net$df.Q))
  invisible(net)
}

# ---- Network 1: Senn2013 (contrast format, multi-arm) ----
data(Senn2013)
# Write the raw per-comparison input so Python reads the identical contrasts.
write.csv(Senn2013[, c("studlab","treat1","treat2","TE","seTE")],
          file.path(outdir, "senn2013_input.csv"), row.names = FALSE)
net1 <- netmeta(TE, seTE, treat1, treat2, studlab,
                data = Senn2013, sm = "MD", common = TRUE, random = TRUE,
                reference.group = "plac")
dump_net(net1, "senn2013")
# SUCRA / P-score (frequentist ranking) for ranking-parity checks.
ps1 <- netrank(net1, small.values = "desirable")
write.csv(data.frame(treat = names(ps1$ranking.common),
                     Pscore.common = as.numeric(ps1$ranking.common),
                     Pscore.random = as.numeric(ps1$ranking.random)),
          file.path(outdir, "senn2013_pscore.csv"), row.names = FALSE)

# ---- Network 2: smoking cessation (Hasselblad 1998), arm-level binary ----
data(smokingcessation)
smokingcessation$studlab <- paste0("S", seq_len(nrow(smokingcessation)))
# arm-based -> pairwise logOR contrasts (handles multi-arm correlation).
p2 <- pairwise(list(treat1, treat2, treat3),
               event = list(event1, event2, event3),
               n = list(n1, n2, n3),
               studlab = studlab, data = smokingcessation, sm = "OR")
write.csv(p2[, c("studlab","treat1","treat2","TE","seTE")],
          file.path(outdir, "smoking_input.csv"), row.names = FALSE)
net2 <- netmeta(p2, common = TRUE, random = TRUE)
dump_net(net2, "smoking")
ps2 <- netrank(net2, small.values = "undesirable")  # higher OR of cessation = good
write.csv(data.frame(treat = names(ps2$ranking.common),
                     Pscore.common = as.numeric(ps2$ranking.common),
                     Pscore.random = as.numeric(ps2$ranking.random)),
          file.path(outdir, "smoking_pscore.csv"), row.names = FALSE)

cat("\nReference generation complete. netmeta version:", as.character(packageVersion("netmeta")), "\n")
