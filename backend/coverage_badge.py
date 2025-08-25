from __future__ import annotations

import os
import xml.etree.ElementTree as ET


def color_for(pct: float) -> str:
    if pct >= 90:
        return "#4c1"  # bright green
    if pct >= 80:
        return "#97CA00"  # green
    if pct >= 70:
        return "#dfb317"  # yellow
    if pct >= 60:
        return "#fe7d37"  # orange
    return "#e05d44"  # red


def make_badge(pct: float) -> str:
    # Simple SVG badge similar to shields.io style
    label = "coverage"
    pct_text = f"{int(round(pct))}%"
    color = color_for(pct)
    # widths are rough; text length affects ideal width
    left_w = 70
    right_w = 60
    total_w = left_w + right_w
    return f"""
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{total_w}\" height=\"20\">
  <linearGradient id=\"s\" x2=\"0\" y2=\"100%\">
    <stop offset=\"0\" stop-color=\"#fff\" stop-opacity=\".7\"/>
    <stop offset=\".1\" stop-opacity=\".1\"/>
    <stop offset=\".9\" stop-opacity=\".3\"/>
    <stop offset=\"1\" stop-opacity=\".5\"/>
  </linearGradient>
  <mask id=\"m\">
    <rect width=\"{total_w}\" height=\"20\" rx=\"3\" fill=\"#fff\"/>
  </mask>
  <g mask=\"url(#m)\">
    <rect width=\"{left_w}\" height=\"20\" fill=\"#555\"/>
    <rect x=\"{left_w}\" width=\"{right_w}\" height=\"20\" fill=\"{color}\"/>
    <rect width=\"{total_w}\" height=\"20\" fill=\"url(#s)\"/>
  </g>
  <g fill=\"#fff\" text-anchor=\"middle\" font-family=\"DejaVu Sans,Verdana,Geneva,sans-serif\" font-size=\"11\">
    <text x=\"{left_w/2}\" y=\"14\">{label}</text>
    <text x=\"{left_w + right_w/2}\" y=\"14\">{pct_text}</text>
  </g>
</svg>
""".strip()


def main():
    xml_path = os.path.join(os.path.dirname(__file__), "coverage.xml")
    if not os.path.exists(xml_path):
        raise SystemExit("coverage.xml not found. Run pytest with --cov-report=xml first.")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # coverage.py xml has attributes: lines-valid, lines-covered
    lines_valid = float(root.attrib.get("lines-valid", 0) or 0)
    lines_covered = float(root.attrib.get("lines-covered", 0) or 0)
    pct = 0.0 if lines_valid == 0 else (lines_covered / lines_valid) * 100.0
    svg = make_badge(pct)
    out_path = os.path.join(os.path.dirname(__file__), "coverage.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out_path} at {pct:.1f}%")


if __name__ == "__main__":
    main()
