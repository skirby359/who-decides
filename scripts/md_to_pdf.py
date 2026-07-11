"""Convert a Markdown file to a clean, preview-style PDF (and optionally HTML).

Why this exists: VS Code has no built-in print/PDF export, and the third-party
"Print" extension (pdconsec.vscode-print) throws on some setups. This is a
dependency-light, repeatable alternative that renders bold / headings / `---`
section rules / tables the way the VS Code preview does.

Requirements (already present on this machine):
  - Python package `markdown`  ->  pip install markdown
  - wkhtmltopdf                 ->  https://wkhtmltopdf.org (found on PATH or in Program Files)

Usage (run from the project root):
  python scripts/md_to_pdf.py local-wedge-brief.md
  python scripts/md_to_pdf.py local-wedge-brief.md docs/local-wedge-brief.pdf
  python scripts/md_to_pdf.py local-wedge-brief.md --html   # also keep the .html

The default output path is the same name with a .pdf extension, next to the input.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import markdown  # type: ignore

# Print-friendly stylesheet approximating the GitHub / VS Code markdown preview.
CSS = """
@page { margin: 18mm 16mm; }
body {
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 11pt; line-height: 1.5; color: #1f2328; max-width: 100%;
}
h1, h2, h3, h4 { line-height: 1.25; margin: 1.2em 0 0.5em; font-weight: 600; }
h1 { font-size: 20pt; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
h2 { font-size: 15pt; border-bottom: 1px solid #d0d7de; padding-bottom: 0.25em; }
h3 { font-size: 12.5pt; }
h4 { font-size: 11pt; }
p, li { margin: 0.4em 0; }
strong { font-weight: 700; }
hr { border: none; border-top: 2px solid #d0d7de; margin: 1.4em 0; }
blockquote {
  margin: 0.6em 0; padding: 0.1em 1em; color: #57606a;
  border-left: 0.25em solid #d0d7de;
}
code {
  font-family: "Cascadia Code", Consolas, "Courier New", monospace;
  background: #f6f8fa; padding: 0.1em 0.35em; border-radius: 4px; font-size: 90%;
}
pre { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 0.8em 0; width: 100%; }
th, td { border: 1px solid #d0d7de; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; font-weight: 600; }
tr:nth-child(even) td { background: #fafbfc; }
a { color: #0969da; text-decoration: none; }
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>{body}</body></html>
"""


def find_wkhtmltopdf() -> str:
    found = shutil.which("wkhtmltopdf")
    if found:
        return found
    candidate = Path(r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    if candidate.exists():
        return str(candidate)
    sys.exit("ERROR: wkhtmltopdf not found on PATH or in Program Files. Install from https://wkhtmltopdf.org")


def main(argv: list[str]) -> None:
    args = [a for a in argv if a != "--html"]
    keep_html = "--html" in argv
    if not args:
        sys.exit(__doc__)

    src = Path(args[0]).resolve()
    if not src.exists():
        sys.exit(f"ERROR: input not found: {src}")

    out_pdf = Path(args[1]).resolve() if len(args) > 1 else src.with_suffix(".pdf")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out_html = out_pdf.with_suffix(".html")

    text = src.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "toc", "admonition"],
        output_format="html5",
    )
    out_html.write_text(HTML_TEMPLATE.format(css=CSS, body=body), encoding="utf-8")

    wk = find_wkhtmltopdf()
    subprocess.run(
        [wk, "--enable-local-file-access", "--encoding", "utf-8",
         str(out_html), str(out_pdf)],
        check=True,
    )

    if not keep_html:
        out_html.unlink(missing_ok=True)
    print(f"PDF written: {out_pdf}")
    if keep_html:
        print(f"HTML kept:  {out_html}")


if __name__ == "__main__":
    main(sys.argv[1:])
