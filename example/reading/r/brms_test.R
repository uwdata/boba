library(brms)

# read data
zinb <- read.csv("http://stats.idre.ucla.edu/stat/data/fish.csv")
zinb$camper <- factor(zinb$camper, labels = c("no", "yes"))
head(zinb)

# fit model
fit_zinb1 <- brm(count ~ persons + child + camper, data = zinb,
                 family = zero_inflated_poisson("log"))

# view results
summary(fit_zinb1)
pdf(file="out.pdf")
plot(fit_zinb1, pars = c("persons", "child", "camper"))
marginal_effects(fit_zinb1)

# get the full STAN log, for debugging purpose
# library(rstan)
# mc <- make_stancode(count ~ persons + child + camper, data = zinb,family = zero_inflated_poisson("log"))
# stan_model(model_code = mc, verbose = TRUE)

# Compilation error on macOS Majove
# These shell commands worked for me:
# xcode-select --install
# open /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg
