#!/bin/bash

set -ex

mkdir -p stitch
for i in img/*.pto; do
  rm -f temp*.tif
  nona -o temp $i
  enblend temp*.tif -o "stitch/$(basename $i | sed s/.pto//g).jpg"
done
