#!/bin/bash

DIR="/Users/allets/Desktop/XJTUThesisLMQ/Figures"

for f in "$DIR"/*.pdf; do
  gs \
    -sDEVICE=pdfwrite \
    -dCompatibilityLevel=1.5 \
    -dNOPAUSE \
    -dQUIET \
    -dBATCH \
    -sOutputFile="${f%.pdf}_tmp.pdf" \
    "$f"

  mv "${f%.pdf}_tmp.pdf" "$f"

  echo "Fixed $f"
done