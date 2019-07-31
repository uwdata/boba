#!/bin/sh

prefix=./code/universe_
suffix=.py
num=6
i=1

while [ $i -le $num ]
do
  echo "python $prefix$i$suffix"
  python $prefix$i$suffix
  i=$(( i+1 ))
done
