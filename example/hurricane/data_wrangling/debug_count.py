# a helper script to count which universes are missing
# for debug purposes

import os

TOTAL = 864

fs = []
for f in os.listdir(os.path.join(os.getcwd(), 'multiverse/results/')):
    name, ext = os.path.splitext(f)
    if ext == '.txt':
        fs.append(int(name.split('_')[1]))

fs.sort()

j = 0
res = []
for i in range(TOTAL):
    if i != fs[j] - 1:
        res.append(i + 1)
    else:
        j += 1

print(res)
