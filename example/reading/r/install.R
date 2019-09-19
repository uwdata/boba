# create user library if it does not exist
repo = "http://cran.us.r-project.org"
lib = Sys.getenv("R_LIBS_USER")
dir.create(lib)

# configure C++ toolchain on Linux in order to use RStan
# https://github.com/stan-dev/rstan/wiki/Installing-RStan-on-Linux
dotR <- file.path(Sys.getenv("HOME"), ".R")
if (!file.exists(dotR)) dir.create(dotR)
M <- file.path(dotR, "Makevars")
if (!file.exists(M)) file.create(M)
cat("\nCXX14FLAGS=-O3 -march=native -mtune=native -fPIC",
    "CXX14=g++", # or clang++ but you may need a version postfix
    file = M, sep = "\n", append = TRUE)

# install required packages
if(!require(readr)) install.packages("readr", lib, repos=repo)
if(!require(lmerTest)) install.packages("lmerTest", lib, repos=repo)
if(!require(brms)) install.packages("brms", lib, repos=repo)
if(!require(car)) install.packages("car", lib, repos=repo)
if(!require(psych)) install.packages("psych", lib, repos=repo)
if(!require(scales)) install.packages("scales", lib, repos=repo)
if(!require(ordinal)) install.packages("ordinal", lib, repos=repo)
