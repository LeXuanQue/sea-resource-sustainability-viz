#!/usr/bin/env python3
"""Build docs/proposal/proposal.pdf (and .docx) from proposal.md + docs/sketch/*.png.

Text pages: A4, 2.54 cm margins, Liberation Serif (Times New Roman metrics), 12pt/1.15.
Appendix:   one prototype sketch per page, caption below in 11pt italic.
Each page is rendered separately and merged with pdfunite, because Chromium inserts a
blank page when the page orientation changes mid-document.
"""
import sys, os, re, base64, subprocess, shutil, tempfile
from markdown_it import MarkdownIt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MD   = os.path.join(HERE, "proposal.md")
PDF  = os.path.join(HERE, "proposal.pdf")
DOCX = os.path.join(HERE, "proposal.docx")
SK   = os.path.join(REPO, "docs", "sketch")
TEXT_ONLY = "--text-only" in sys.argv
CHROME = shutil.which("chromium") or shutil.which("google-chrome-stable")

SERIF = '"Liberation Serif", "Times New Roman", "Tinos", serif'

FIGURES = [
 "Design A: story first. The main finding is readable without any interaction.",
 "Design A: clicking a country re-ranks and highlights it; years with no data are labelled, never drawn as zero.",
 "Design B: coordinated dashboard, every view on one screen.",
 "Design B: one click updates the KPI strip, small multiples and trend together.",
 "Design C, level 1: controls and a ranking of all eight countries, with average and median cards.",
 "Design C: clicking an indicator card opens its full trend; gaps are named, never drawn as zero.",
]
PORTRAIT = {1, 2, 5}

TEXT_CSS = f"""
@page {{ size: A4; margin: 2.54cm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: {SERIF}; font-size: 12pt; line-height: 1.15; color: #000;
        background: #fff; margin: 0; text-align: justify; }}
p {{ margin: 0 0 6pt; }}
.titleblock {{ text-align: center; margin: 0 0 10pt; }}
.titleblock p {{ text-align: center; margin: 0 0 4pt; }}
.t1 {{ font-weight: bold; font-size: 14pt; }}
.t2, .t3 {{ font-size: 12pt; }}
h2 {{ font-size: 12pt; font-weight: bold; margin: 9pt 0 3pt; text-align: left;
      break-after: avoid; page-break-after: avoid; }}
h3 {{ font-size: 12pt; font-weight: bold; margin: 7pt 0 2pt; text-align: left;
      break-after: avoid; page-break-after: avoid; }}
table {{ width: 100%; border-collapse: collapse; font-size: 11pt; margin: 5pt 0 6pt; }}
th, td {{ border: 0.75pt solid #000; padding: 1.4pt 4pt; text-align: left; vertical-align: top; }}
th {{ font-weight: bold; }}
tr {{ break-inside: avoid; page-break-inside: avoid; }}
table {{ break-inside: avoid; page-break-inside: avoid; }}
ul {{ margin: 0 0 6pt; padding-left: 18pt; }}
li {{ margin-bottom: 1.5pt; text-align: justify; }}
code {{ font-family: "Liberation Mono", monospace; font-size: 10.5pt; }}
a {{ color: #000; text-decoration: none; word-break: break-all; }}
.refs {{ font-size: 10pt; line-height: 1; }}
.refs p {{ margin: 0 0 2.5pt; }}
"""

def render(html, out):
    tmp = tempfile.mkdtemp()
    hp = os.path.join(tmp, "p.html")
    open(hp, "w", encoding="utf-8").write(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={out}",
                    "--virtual-time-budget=20000", f"file://{hp}"],
                   check=True, capture_output=True)

def npages(pdf):
    o = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return int([l for l in o.splitlines() if l.startswith("Pages")][0].split(":")[1])

md = MarkdownIt("commonmark").enable(["table", "strikethrough"])
body = md.render(open(MD, encoding="utf-8").read())

work = tempfile.mkdtemp()
text_pdf = os.path.join(work, "00-text.pdf")
render(f"<!doctype html><html><head><meta charset='utf-8'><style>{TEXT_CSS}</style></head>"
       f"<body>{body}</body></html>", text_pdf)
n_text = npages(text_pdf)

if TEXT_ONLY:
    shutil.copy(text_pdf, os.path.join(HERE, "_textonly.pdf"))
    print(f"TEXT-ONLY pages={n_text}")
    sys.exit(0)

parts = [text_pdf]
for i in range(1, 7):
    portrait = i in PORTRAIT
    size   = "A4 portrait" if portrait else "A4 landscape"
    margin = "1.2cm"
    cap_mm = 16 if i == 1 else 12          # first page also carries the appendix heading
    maxh   = (297 - 24 - cap_mm) if portrait else (210 - 24 - cap_mm)
    b64 = base64.b64encode(open(os.path.join(SK, f"sketch-{i}.png"), "rb").read()).decode()
    head = ('<p class="apxh">Appendix: Prototype sketches</p>' if i == 1 else '')
    css = (f"@page {{ size: {size}; margin: {margin}; }}"
           f"html,body{{margin:0;padding:0;font-family:{SERIF};color:#000;background:#fff;}}"
           "body{text-align:center;}"
           ".apxh{font-size:12pt;font-weight:bold;text-align:left;margin:0 0 6pt;}"
           f"img{{max-width:100%;max-height:{maxh}mm;display:block;margin:0 auto;"
           "object-fit:contain;border:0.5pt solid #000;}"
           ".cap{font-size:11pt;font-style:italic;margin-top:4mm;text-align:center;}")
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"{head}<img src='data:image/png;base64,{b64}'>"
            f"<div class='cap'>Figure {i}. {FIGURES[i-1]}</div></body></html>")
    sp = os.path.join(work, f"{i:02d}.pdf")
    render(html, sp)
    assert npages(sp) == 1, f"figure {i} rendered {npages(sp)} pages"
    parts.append(sp)

subprocess.run(["pdfunite", *parts, PDF], check=True)

# ---- editable DOCX (Times New Roman reference doc) ----
def build_docx():
    import pypandoc
    pandoc = pypandoc.get_pandoc_path()
    ref = os.path.join(work, "ref.docx")
    subprocess.run([pandoc, "-o", ref, "--print-default-data-file=reference.docx"],
                   check=True, stdout=open(ref, "wb"))
    # retype the reference doc to Times New Roman 12pt
    import zipfile
    tmpd = os.path.join(work, "refx"); os.makedirs(tmpd, exist_ok=True)
    with zipfile.ZipFile(ref) as z: z.extractall(tmpd)
    sp = os.path.join(tmpd, "word", "styles.xml")
    x = open(sp, encoding="utf-8").read()
    TNR = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
           'w:cs="Times New Roman" w:eastAsia="Times New Roman"/>')
    x = re.sub(r'<w:rFonts[^/]*?Theme[^/]*?/>', TNR, x)          # theme fonts -> explicit TNR
    x = re.sub(r'<w:rFonts w:ascii="[^"]*"[^/]*?/>', TNR, x)      # any explicit font -> TNR
    x = re.sub(r'<w:sz w:val="2[0-3]"\s*/>', '<w:sz w:val="24" />', x)
    x = re.sub(r'<w:szCs w:val="2[0-3]"\s*/>', '<w:szCs w:val="24" />', x)
    open(sp, "w", encoding="utf-8").write(x)
    ref2 = os.path.join(work, "ref-tnr.docx")
    with zipfile.ZipFile(ref2, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmpd):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, tmpd))
    # strip raw HTML wrappers so the title block survives the docx conversion
    src = open(MD, encoding="utf-8").read()
    src = src.replace('<div class="titleblock">', '').replace('<div class="refs">', '')
    src = src.replace('</div>', '')
    src = re.sub(r'<p class="t1">(.*?)</p>', r'**\1**', src)
    src = re.sub(r'<p class="t2">(.*?)</p>', r'\1', src)
    src = re.sub(r'<p class="t3">(.*?)</p>', r'\1', src)
    src += "\n\n## Appendix: Prototype sketches\n\n"
    for i in range(1, 7):
        src += f"![Figure {i}. {FIGURES[i-1]}](../sketch/sketch-{i}.png)\n\n"
    mdx = os.path.join(work, "docx.md")
    open(mdx, "w", encoding="utf-8").write(src)
    subprocess.run([pandoc, mdx, "-o", DOCX, f"--reference-doc={ref2}",
                    "--resource-path", HERE], check=True)

build_docx()
print(f"PDF {PDF}  text={n_text} figures=6 total={npages(PDF)}")
print(f"DOCX {DOCX}  {os.path.getsize(DOCX)//1024} KB")
