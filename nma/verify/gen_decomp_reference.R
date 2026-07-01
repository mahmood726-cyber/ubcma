# Generate netmeta's design-by-treatment Q decomposition reference for the
# canonical networks, to independently check Component C's q_decomposition.
# netmeta::decomp.design returns Q.het (within designs) and Q.inc (between
# designs) with their df -- the authoritative source for the inconsistency split.
suppressMessages(library(netmeta))
cat("netmeta version:", as.character(packageVersion("netmeta")), "\n")

run <- function(path, sm, name) {
  d <- read.csv(path, stringsAsFactors = FALSE)
  net <- netmeta(TE, seTE, treat1, treat2, studlab, data = d, sm = sm,
                 common = TRUE, random = TRUE)
  dc <- decomp.design(net)
  # Q decomposition table (whole network row)
  qd <- dc$Q.decomp
  cat("\n==", name, "==\n")
  print(qd)
  out <- data.frame(
    network = name,
    Q_total = qd["Total", "Q"], df_total = qd["Total", "df"],
    Q_het = qd["Within designs", "Q"], df_het = qd["Within designs", "df"],
    Q_inc = qd["Between designs", "Q"], df_inc = qd["Between designs", "df"],
    tau2 = net$tau2
  )
  out
}

a <- run("nma/reference/senn2013_input.csv", "MD", "senn2013")
b <- run("nma/reference/smoking_input.csv", "OR", "smoking")
res <- rbind(a, b)
write.csv(res, "nma/verify/decomp_reference.csv", row.names = FALSE)
cat("\nWrote nma/verify/decomp_reference.csv\n")
print(res)
