# Independent-engine (base R) re-derivation of the consolidation headline.
# Reads the committed trials.json, re-implements the 5-way real-LOO transport &
# relevance priors FROM SCRATCH in R (independent of the Python code), and recomputes
#   - per-trial paired delta d_i = |mu_tran_i - y_i| - |mu_rel_i - y_i|  at central bw
#   - per-slice mean d, the pooled per-trial mean, the sign count
#   - an EXACT binomial sign test and a sign-flip permutation p
# No metafor needed; this is a distinct-language witness of the new distribution-free result.
suppressWarnings(suppressMessages(library(jsonlite)))

# ---- Mandel-Paule/DL REML pooler for the 'nma' prior (matches mp_reml) ----
mp_reml <- function(y, s) {
  v <- s^2; if (length(y) == 1) return(c(y[1], s[1]))
  tau2 <- 0
  for (it in 1:100) {
    w <- 1/(v + tau2); mu <- sum(w*y)/sum(w)
    Q <- sum(w*(y-mu)^2); den <- sum(w) - sum(w^2)/sum(w)
    if (Q <= length(y)-1 || den <= 0) break
    nt <- tau2 + (Q-(length(y)-1))/den
    if (abs(nt-tau2) < 1e-8) { tau2 <- max(nt,0); break }
    tau2 <- max(nt,0)
  }
  w <- 1/(v+tau2); c(sum(w*y)/sum(w), sqrt(1/sum(w)))
}

# ---- LOO-safe RE(DL) meta-regression slope of y on x (donors only) ----
re_slope <- function(x, y, s) {
  n <- length(y); if (n < 4 || sd(x) < 1e-9) return(0)
  X <- cbind(1, x); w <- 1/pmax(s^2, 1e-12)
  XtWX <- t(X) %*% (X*w); beta <- solve(XtWX, t(X*w) %*% y)
  resid <- y - X %*% beta; Qres <- sum(w*resid^2)
  trace <- sum(w) - sum(diag(solve(XtWX) %*% (t(X) %*% (X*(w^2)))))
  tau2 <- if (trace > 0) max(0,(Qres-(n-2))/trace) else 0
  W2 <- 1/(s^2+tau2); as.numeric(solve(t(X)%*%(X*W2), t(X*W2)%*%y)[2])
}

# ---- one prior (Gaussian kernel x precision) for relevance/transport ----
prior_one <- function(xt, xs, ys, ses, bw, mode) {
  prec <- 1/pmax(ses^2, 1e-12)
  if (mode == "nma") return(mp_reml(ys, ses))
  k <- exp(-0.5*((xs - xt)/bw)^2); w <- k*prec
  if (mode == "relevance") { yeff <- ys } else {
    b <- re_slope(xs, ys, ses); yeff <- ys + b*(xt - xs)
  }
  ws <- sum(w); if (ws <= 0) return(c(NaN, Inf))
  mu <- sum(w*yeff)/ws
  within <- sum(w^2*ses^2)/ws^2; between <- sum(w*(yeff-mu)^2)/ws
  c(mu, sqrt(max(within+between, 1e-9)))
}

loo_delta <- function(tr, cov) {
  y <- sapply(tr, function(t) t$y); s <- sapply(tr, function(t) t$se)
  x <- sapply(tr, function(t) t[[cov]]); n <- length(y); bw <- sd(x)  # central bw = SD
  d <- numeric(n)
  for (i in 1:n) {
    m <- setdiff(1:n, i)
    mu_t <- prior_one(x[i], x[m], y[m], s[m], bw, "transport")[1]
    mu_r <- prior_one(x[i], x[m], y[m], s[m], bw, "relevance")[1]
    d[i] <- abs(mu_t - y[i]) - abs(mu_r - y[i])
  }
  d
}

# run from repo root:
bcg <- fromJSON("borrowing/bcg/bcg_trials.json", simplifyVector = FALSE)$trials
rota <- fromJSON("borrowing/rota/rota_trials.json", simplifyVector = FALSE)$trials

d_bcg <- loo_delta(bcg, "ablat")
d_rota <- loo_delta(rota, "u5mr")
cat(sprintf("R engine  BCG   k=%d  mean d = %+.4f\n", length(d_bcg), mean(d_bcg)))
cat(sprintf("R engine  rota  k=%d  mean d = %+.4f\n", length(d_rota), mean(d_rota)))

d_all <- c(d_bcg, d_rota)
nneg <- sum(d_all < 0); n <- length(d_all)
cat(sprintf("R engine  pooled per-trial mean d = %+.4f ; %d/%d favour transport\n",
            mean(d_all), nneg, n))

# exact binomial sign test (one-sided: more negatives than 0.5)
p_sign <- binom.test(nneg, n, 0.5, alternative = "greater")$p.value
cat(sprintf("R engine  exact binomial sign test one-sided p = %.4f\n", p_sign))

# sign-flip permutation on the mean (one-sided mean<0)
set.seed(101); B <- 100000; obs <- mean(d_all)
pm <- replicate(B, mean(sample(c(-1,1), n, replace=TRUE) * abs(d_all)))
cat(sprintf("R engine  sign-flip permutation one-sided p(mean<0) = %.4f\n",
            (1 + sum(pm <= obs))/(B+1)))

# Wilcoxon one-sided
cat(sprintf("R engine  Wilcoxon signed-rank one-sided p = %.4f\n",
            wilcox.test(d_all, alternative="less")$p.value))
