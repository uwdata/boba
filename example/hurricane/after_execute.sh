boba merge estimate_{}.csv -b ./results --out estimate.csv
boba merge uncertainty_{}.csv -b ./results --out uncertainty.csv
boba merge null_{}.csv -b ./results --out null.csv

Rscript stacking_weights.R