library(rstan)
library(readr)
library(tidyverse)

dir = './results'
fs = list.files(dir, pattern='^loglik')
if (length(fs) < 1) {
  stop('No matching files found, pattern: loglik_*.csv')
}

dfs = lapply(fs, function (f) {
  read_csv(file.path(dir, f), col_types='d')
})
uids = lapply(fs, function (f) {
  res = strsplit(strsplit(f, '_')[[1]][2], '\\.')[[1]][1]
  return(strtoi(res))
})

m = bind_cols(dfs) %>% as.matrix
weights = loo::stacking_weights(m)
res = enframe(c(weights)) %>%
  select(-name) %>%
  add_column(unlist(uids)) %>%
  rename(weights = 1, uid = 2)
write_csv(res, './weights.csv')
