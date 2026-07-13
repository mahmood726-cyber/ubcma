suppressMessages(library(metadat))
has_json <- requireNamespace("jsonlite", quietly = TRUE)
targets <- c("dat.axfors2021", "dat.hartmannboyce2018", "dat.karner2014")
out <- list()
for (n in targets) {
  data(list = n)
  d <- get(n)
  nctcol <- names(d)[sapply(d, function(c) any(grepl("NCT[0-9]{5}", as.character(c))))]
  cat("===", n, "=== rows", nrow(d), "\n")
  cat("  cols:", paste(names(d), collapse=" ; "), "\n")
  cat("  nct_col:", paste(nctcol, collapse=","), "\n")
  out[[n]] <- list(cols = names(d), nrow = nrow(d), nctcol = nctcol, rows = d)
}
if (has_json) {
  writeLines(jsonlite::toJSON(out, dataframe = "rows", auto_unbox = TRUE, na = "null"),
             "F:/ubcma/regpub_pilot/data/metadat_nct.json")
  cat("wrote data/metadat_nct.json\n")
} else {
  for (n in targets) {
    write.csv(out[[n]]$rows, paste0("F:/ubcma/regpub_pilot/data/", n, ".csv"), row.names = FALSE)
  }
  cat("wrote per-dataset CSVs (jsonlite absent)\n")
}
