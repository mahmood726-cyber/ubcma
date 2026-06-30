suppressMessages(library(dosresmeta)); suppressMessages(library(jsonlite))
data(alcohol_crc)
# Harrell restricted cubic spline basis (norm=2: divide nonlinear terms by (t_k - t_1)^2)
rcs_basis <- function(x, knots){
  k <- length(knots); t <- knots
  X <- matrix(0, length(x), k-1)
  X[,1] <- x
  denom <- (t[k]-t[k-1])
  scale <- (t[k]-t[1])^2
  cub <- function(u) pmax(u,0)^3
  for(j in 1:(k-2)){
    X[,j+1] <- ( cub(x-t[j]) - cub(x-t[k-1])*(t[k]-t[j])/denom + cub(x-t[k])*(t[k-1]-t[j])/denom ) / scale
  }
  X
}
knots <- as.numeric(quantile(alcohol_crc$dose, c(.1,.5,.9)))
B <- rcs_basis(alcohol_crc$dose, knots)
colnames(B) <- c("b1","b2")
dd <- cbind(alcohol_crc, B)
spl_fixed <- dosresmeta(formula=logrr~b1+b2, id=id, type=type, se=se, cases=cases, n=peryears,
                        data=dd, method="fixed", covariance="gl")
spl_reml <- dosresmeta(formula=logrr~b1+b2, id=id, type=type, se=se, cases=cases, n=peryears,
                       data=dd, method="reml", covariance="gl")
out <- list(
  knots=knots,
  basis_dose25 = as.numeric(rcs_basis(25, knots)),
  spline_fixed_coef = as.numeric(coef(spl_fixed)),
  spline_fixed_vcov = vcov(spl_fixed),
  spline_reml_coef  = as.numeric(coef(spl_reml)),
  spline_reml_vcov  = vcov(spl_reml),
  spline_reml_Psi   = spl_reml$Psi
)
writeLines(toJSON(out, digits=14, auto_unbox=TRUE, pretty=TRUE), "ref_spline.json")
cat("FIXED coef:", coef(spl_fixed), "\n")
cat("REML  coef:", coef(spl_reml), "\n")
cat("REML Psi:\n"); print(spl_reml$Psi)
cat("basis(25):", as.numeric(rcs_basis(25,knots)), "\n")
