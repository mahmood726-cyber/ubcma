## Harmonise ADDITIONAL real metadat meta-analyses into borrowing-field nodes.
## Authoritative effect computation via metafor::escalc (not hand-rolled).
##   12 raw-2x2 MAs -> log-OR (LOR family)
##    2 raw correlation MAs -> Fisher-z (COR family)
## Specialties are taken from metadat's own \concept{} topic tags, not guessed.
##
## Excluded as trial-overlap duplicates of MAs already in the committed corpus:
##   colditz1994  (identical BCG-vaccine data as dat.bcg)
##   egger2001    (IV-magnesium-in-MI; shares trials with the existing li2007)
## Output: corpus_nodes_new.csv  (appended by corpus.load_corpus(include_new=True))
suppressMessages({library(metadat); library(metafor)})
rows <- list(); k <- 0
addrow <- function(ma, family, specialty, yi, vi, year=NA){
  ok <- is.finite(yi) & is.finite(vi) & vi > 0
  for (i in which(ok)) {
    k <<- k + 1
    rows[[k]] <<- data.frame(ma=ma, family=family, specialty=specialty,
      yi=as.numeric(yi[i]), se=sqrt(as.numeric(vi[i])),
      year=ifelse(length(year) > 1, as.numeric(year[i]), as.numeric(year)))
  }
}
# ---- LOR family: raw 2x2 (ai,n1i,ci,n2i) -> escalc OR ----
an <- list(
  yusuf1985="cardiology", anand1999="cardiology", lau1992="cardiology",
  linde2005="psychiatry", nielweise2007="infectious_disease",
  graves2010="infectious_disease", lee2004="alternative_med",
  laopaiboon2015="pulmonology", hahn2001="pediatrics")
for (nm in names(an)) {
  data(list=paste0("dat.", nm), package="metadat"); e <- get(paste0("dat.", nm))
  yr <- if ("year" %in% names(e)) e$year else NA
  es <- escalc("OR", ai=e$ai, bi=e$n1i - e$ai, ci=e$ci, di=e$n2i - e$ci)
  addrow(nm, "LOR", an[[nm]], es$yi, es$vi, yr)
}
# hackshaw1998 = pre-computed log-OR (yi,vi)
data(dat.hackshaw1998, package="metadat"); e <- dat.hackshaw1998
addrow("hackshaw1998", "LOR", "oncology", e$yi, e$vi, e$year)
# ---- COR family: raw (ri,ni) -> escalc ZCOR ----
cors <- list(craft2003="psychology", cohen1981="education")
for (nm in names(cors)) {
  data(list=paste0("dat.", nm), package="metadat"); e <- get(paste0("dat.", nm))
  yr <- if ("year" %in% names(e)) e$year else NA
  es <- escalc("ZCOR", ri=e$ri, ni=e$ni)
  addrow(nm, "COR", cors[[nm]], es$yi, es$vi, yr)
}
out <- do.call(rbind, rows)
write.csv(out, "corpus_nodes_new.csv", row.names=FALSE)
cat("NEW nodes:", nrow(out), " MAs:", length(unique(out$ma)), "\n")
print(aggregate(yi ~ ma + family + specialty, out, length))
