#!/usr/bin/env bash
#
#  merge_pdf.sh – Concatenate multiple PDFs into one.
#
#  Usage:
#     ./merge_pdf.sh output.pdf input1.pdf input2.pdf … [inputN.pdf]
#
#  Dependencies (at least one of the following must be present):
#    - poppler-utils : pdfunite
#    - qpdf          : qpdf
#    - pdftk         : pdftk
#    - ghostscript   : gs
#
#  The script preserves the order of files as they appear on the command line.
#  It also checks for a few common problems (missing input, unreadable files,
#  output file already exists, etc.).
#

set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") OUTPUT.pdf INPUT1.pdf [INPUT2.pdf ...]
Merges all INPUT*.pdf files into the single OUTPUT.pdf.
Requires at least one PDF utility:
  * pdfunite (poppler‑utils)
  * qpdf
  * pdftk
  * gs (ghostscript)
EOF
  exit 1
}

# ---- Sanity checks --------------------------------------------------------

if [[ $# -lt 2 ]]; then
  echo "Error: Need at least one input PDF and an output file." >&2
  usage
fi

OUT="${1}"
shift

# Check that all inputs exist & are readable PDFs
for f in "$@"; do
  if [[ ! -r "$f" ]]; then
    echo "Error: Cannot read input file '$f'." >&2
    exit 1
  fi
done

# Prevent accidental overwrite (you can delete/rename the target if you really want it)
if [[ -e "$OUT" ]]; then
  echo "Error: Output file '$OUT' already exists. Please choose a different name or remove it first." >&2
  exit 1
fi

# ---- Find a suitable tool -------------------------------------------------

# Helper to run command and capture its error message if it fails
run() {
  "$@" || { echo "Command failed:" "$*" >&2; return 1; }
}

if command -v pdfunite &>/dev/null; then
  TOOL="pdfunite"
elif command -v qpdf &>/dev/null; then
  TOOL="qpdf"
elif command -v pdftk &>/dev/null; then
  TOOL="pdftk"
elif command -v gs &>/dev/null; then
  TOOL="gs"
else
  echo "Error: No supported PDF tool found. Install poppler‑utils, qpdf, pdftk or ghostscript." >&2
  exit 1
fi

# ---- Perform the merge ----------------------------------------------------

case "$TOOL" in
  pdfunite)
    run pdfunite "$@" "$OUT"
    ;;

  qpdf)
    # qpdf needs all inputs listed first and then the output file as the last argument
    run qpdf --empty --pages "$@" -- "$OUT"
    ;;

  pdftk)
    # pdftk syntax: pdftk input1.pdf input2.pdf cat output output.pdf
    run pdftk "$@" cat output "$OUT"
    ;;

  gs)
    # Ghostscript (PostScript) command – fairly universal but a bit slower
    # The '-sDEVICE=pdfwrite' creates a PDF, '-dBATCH -dNOPAUSE' prevents interactive mode,
    # and '-q' suppresses the status bar.
    run gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite \
         "-sOutputFile=$OUT" "$@"
    ;;

  *)
    echo "Internal error: Unhandled tool $TOOL" >&2
    exit 1
    ;;
esac

echo "Successfully merged $(printf '%q ' "$@") into '$OUT'."

exit 0
