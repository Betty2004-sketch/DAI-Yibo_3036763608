"""
Build report.pdf from report/report.md.

Uses the Python `markdown` package (tables extension) for Markdown -> HTML and
headless Google Chrome for HTML -> PDF. The wage-distribution figure is embedded
as a base64 data URI so the PDF is self-contained.
"""
import base64
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "report", "report.md")
HTML = os.path.join(ROOT, "report", "report.html")
PDF = os.path.join(ROOT, "report.pdf")
FIG = os.path.join(ROOT, "outputs", "figures", "figure1_wage_distribution.png")

import markdown  # noqa: E402

with open(MD, encoding="utf-8") as f:
    body = markdown.markdown(f.read(), extensions=["tables", "fenced_code", "sane_lists"])

# Embed the figure so the PDF is self-contained.
with open(FIG, "rb") as f:
    data_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode()
body = body.replace('src="../outputs/figures/figure1_wage_distribution.png"',
                    f'src="{data_uri}"')

css = """
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
       max-width: 48rem; margin: 2.5rem auto; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.2rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: .2rem; }
table { border-collapse: collapse; margin: 1rem 0; font-size: .9rem; }
th, td { border: 1px solid #ccc; padding: .3rem .6rem; text-align: center; }
th { background: #f4f4f4; }
img { max-width: 100%; margin: 1rem 0; }
code, pre { font-family: Menlo, monospace; font-size: .85em; }
pre { background: #f6f6f6; padding: .8rem; overflow-x: auto; }
"""

html = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>")

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([
    chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
    f"--print-to-pdf={PDF}", f"file://{HTML}",
], check=True, capture_output=True)

print(f"wrote {PDF}")
