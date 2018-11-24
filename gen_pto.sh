#!/bin/bash

i=0
num_cams=3
rm -f img/*.pto
for img in img/IMG-*.jpg; do
  project=$(basename $img | sed 's/-[0-9].jpg//g')
  if ! ((i % num_cams)); then
    echo "creating project img/$project.pto"
    cp project.pto "img/$project.pto"
  fi
  sed -i "img/$project.pto" -e "s#img/IMG.*-$(($i % $num_cams)).jpg#$(basename $img)#g"
  ((i = i + 1))
done
