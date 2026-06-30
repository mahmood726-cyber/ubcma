suppressMessages(library(dosresmeta)); suppressMessages(library(rms))
data(alcohol_crc)
out <- list()

## --- First-stage covariance for study 1 (atm) -- validates GL reconstruction ---
d1 <- subset(alcohol_crc, id=="atm")
S1 <- with(d1, covar.logrr(cases=cases, n=peryears, y=logrr, v=se^2, type=type, covariance="gl"))
out$study1_cov <- S1
out$study1_adjcounts <- with(d1, grl(logrr, se^2, cases, peryears, type))

## --- Two-stage LINEAR, REML and fixed ---
lin_reml <- dosresmeta(formula=logrr~dose, id=id, type=type, se=se, cases=cases, n=peryears,
                       data=alcohol_crc, method="reml", covariance="gl")
lin_fixed <- dosresmeta(formula=logrr~dose, id=id, type=type, se=se, cases=cases, n=peryears,
                        data=alcohol_crc, method="fixed", covariance="gl")
out$linear_reml_coef <- coef(lin_reml)
out$linear_reml_vcov <- vcov(lin_reml)
out$linear_reml_tau2 <- lin_reml$Psi
out$linear_fixed_coef <- coef(lin_fixed)
out$linear_fixed_vcov <- vcov(lin_fixed)
## per-study first-stage linear slopes + var
out$linear_ml_b <- lin_reml$bi
out$linear_ml_Slist1 <- lin_reml$Slist[[1]]

## --- Two-stage RCS spline (knots at 10,28,50 percentiles default of dosresmeta) ---
k <- quantile(alcohol_crc$dose, c(.1,.5,.9))
spl_reml <- dosresmeta(formula=logrr~rcs(dose, k), id=id, type=type, se=se, cases=cases, n=peryears,
                       data=alcohol_crc, method="reml", covariance="gl")
out$spline_knots <- as.numeric(k)
out$spline_reml_coef <- coef(spl_reml)
out$spline_reml_vcov <- vcov(spl_reml)
out$spline_reml_Psi <- spl_reml$Psi
## predicted logRR at dose=25 vs 0 (a standard reported contrast)
xref <- 0; xtar <- 25
out$spline_pred25 <- predict(spl_reml, newdata=data.frame(dose=c(0,25)), expo=FALSE)

library(jsonlite)
writeLines(toJSON(out, digits=12, auto_unbox=TRUE, pretty=TRUE), "ref_alcohol_crc.json")
cat("OK\n")
cat("linear reml slope:", coef(lin_reml), " se:", sqrt(vcov(lin_reml)), " tau2:", lin_reml$Psi, "\n")
