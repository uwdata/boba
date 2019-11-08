# create user library if it does not exist
repo = "http://cran.us.r-project.org"
lib = Sys.getenv("R_LIBS_USER")
dir.create(lib)

# install required packages
if(!require(readr)) install.packages("readr", lib, repos=repo)
if(!require(MASS)) install.packages("MASS", lib, repos=repo)
if(!require(tidyverse)) install.packages("tidyverse", lib, repos=repo)
if(!require(broom.mixed)) install.packages("broom.mixed", lib, repos=repo)
