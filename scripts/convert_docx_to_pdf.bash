mkdir -p pdf/input
for f in word/input/*.docx; do
  libreoffice --headless --convert-to pdf --outdir pdf/input "$f"
done