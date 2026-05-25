#!/usr/bin/env python3
"""Generate a searchable static HTML site from dumped ObjC headers."""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>iOS {version} ({build}) — Header Browser</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0d1117; color: #c9d1d9; height: 100vh; display: flex; flex-direction: column; }}
  #header {{ background: #161b22; border-bottom: 1px solid #30363d; padding: 12px 16px; display: flex; align-items: center; gap: 16px; flex-shrink: 0; }}
  #header h1 {{ font-size: 15px; font-weight: 600; color: #58a6ff; white-space: nowrap; }}
  #header .meta {{ font-size: 12px; color: #8b949e; }}
  #search {{ flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 6px 10px; color: #c9d1d9; font-size: 13px; outline: none; }}
  #search:focus {{ border-color: #58a6ff; }}
  #layout {{ display: flex; flex: 1; overflow: hidden; }}
  #sidebar {{ width: 280px; flex-shrink: 0; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; overflow: hidden; }}
  #framework-list {{ flex: 1; overflow-y: auto; }}
  .framework-item {{ cursor: pointer; }}
  .framework-name {{ padding: 6px 12px; font-size: 13px; font-weight: 500; color: #c9d1d9; display: flex; align-items: center; justify-content: space-between; border-left: 3px solid transparent; }}
  .framework-name:hover {{ background: #1f2937; }}
  .framework-name.active {{ border-left-color: #58a6ff; background: #1f2937; color: #58a6ff; }}
  .framework-name .count {{ font-size: 11px; color: #8b949e; background: #21262d; padding: 1px 6px; border-radius: 10px; }}
  .file-list {{ display: none; background: #0d1117; }}
  .file-list.open {{ display: block; }}
  .file-item {{ padding: 4px 12px 4px 24px; font-size: 12px; color: #8b949e; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid transparent; }}
  .file-item:hover {{ color: #c9d1d9; background: #161b22; }}
  .file-item.active {{ color: #58a6ff; border-left-color: #58a6ff; background: #161b22; }}
  #content {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}
  #breadcrumb {{ padding: 8px 16px; font-size: 12px; color: #8b949e; background: #161b22; border-bottom: 1px solid #30363d; flex-shrink: 0; }}
  #breadcrumb span {{ color: #58a6ff; }}
  #file-content {{ flex: 1; overflow: auto; padding: 0; }}
  #file-content pre {{ padding: 16px; font-family: "SF Mono", "Fira Code", "Consolas", monospace; font-size: 12px; line-height: 1.6; tab-size: 4; white-space: pre; color: #c9d1d9; }}
  #empty-state {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #8b949e; gap: 8px; }}
  #empty-state .icon {{ font-size: 48px; }}
  #empty-state p {{ font-size: 14px; }}
  .hl-comment {{ color: #8b949e; }}
  .hl-keyword {{ color: #ff7b72; }}
  .hl-type {{ color: #79c0ff; }}
  .hl-string {{ color: #a5d6ff; }}
  .hl-number {{ color: #f2cc60; }}
  .hl-preprocessor {{ color: #d2a8ff; }}
  .hl-property {{ color: #7ee787; }}
  #stats {{ font-size: 11px; color: #8b949e; padding: 8px 12px; border-top: 1px solid #30363d; flex-shrink: 0; }}
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #484f58; }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
<div id="header">
  <h1>iOS {version} ({build}) Headers</h1>
  <input id="search" type="search" placeholder="Search frameworks and classes..." autocomplete="off">
  <div class="meta">{framework_count} frameworks &nbsp;·&nbsp; {header_count} headers &nbsp;·&nbsp; {generated}</div>
</div>
<div id="layout">
  <div id="sidebar">
    <div id="framework-list"></div>
    <div id="stats"></div>
  </div>
  <div id="content">
    <div id="breadcrumb">Select a header file from the sidebar</div>
    <div id="file-content">
      <div id="empty-state">
        <div class="icon">&#128196;</div>
        <p>Select a header file to view its contents</p>
      </div>
    </div>
  </div>
</div>

<script>
const INDEX = {index_json};

let currentFramework = null;
let currentFile = null;
let searchQuery = '';

function escapeHtml(s) {{
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function highlight(code) {{
  code = escapeHtml(code);
  // Single-line comments
  code = code.replace(/(\\/\\/[^\\n]*)/g, '<span class="hl-comment">$1</span>');
  // Multi-line comments
  code = code.replace(/(\\/\\*[\\s\\S]*?\\*\\/)/g, '<span class="hl-comment">$1</span>');
  // Preprocessor
  code = code.replace(/^(#[^\\n]*)/gm, '<span class="hl-preprocessor">$1</span>');
  // ObjC keywords
  const kw = ['@interface','@implementation','@end','@protocol','@property','@class',
               '@optional','@required','@synthesize','@dynamic','@selector','@encode',
               'self','super','nil','Nil','YES','NO','BOOL','id','void','return',
               'if','else','for','while','do','switch','case','break','continue',
               'typedef','struct','enum','union','static','const','extern','inline'];
  kw.forEach(k => {{
    const re = new RegExp('\\\\b(' + k.replace('@','\\\\@') + ')\\\\b', 'g');
    code = code.replace(re, '<span class="hl-keyword">$1</span>');
  }});
  // Types
  code = code.replace(/\\b(NS[A-Z][A-Za-z]*|UI[A-Z][A-Za-z]*|AV[A-Z][A-Za-z]*|CL[A-Z][A-Za-z]*|MK[A-Z][A-Za-z]*|CF[A-Z][A-Za-z]*|CG[A-Z][A-Za-z]*)\\b/g,
    '<span class="hl-type">$1</span>');
  // String literals
  code = code.replace(/@?"([^"\\\\]|\\\\.)*"/g, '<span class="hl-string">$&</span>');
  // Property attributes
  code = code.replace(/\\((\\s*(nonatomic|atomic|strong|weak|copy|assign|readonly|readwrite|nullable|nonnull|getter|setter|class)[,\\s]*)+\\)/g,
    '<span class="hl-property">$&</span>');
  return code;
}}

function renderSidebar() {{
  const list = document.getElementById('framework-list');
  const q = searchQuery.toLowerCase();
  let visibleFrameworks = 0;
  let visibleFiles = 0;

  list.innerHTML = INDEX.frameworks.map(fw => {{
    const files = INDEX.files[fw] || [];
    const matchedFiles = q ? files.filter(f => f.toLowerCase().includes(q) || fw.toLowerCase().includes(q)) : files;
    if (q && matchedFiles.length === 0) return '';
    visibleFrameworks++;
    visibleFiles += matchedFiles.length;

    const isActive = fw === currentFramework;
    const isOpen = isActive || (q && matchedFiles.length > 0);

    return `<div class="framework-item" data-fw="${{escapeHtml(fw)}}">
      <div class="framework-name${{isActive ? ' active' : ''}}" onclick="toggleFramework('${{escapeHtml(fw)}}')">
        <span>${{escapeHtml(fw)}}</span>
        <span class="count">${{matchedFiles.length}}</span>
      </div>
      <div class="file-list${{isOpen ? ' open' : ''}}">
        ${{matchedFiles.map(f => `<div class="file-item${{f === currentFile && fw === currentFramework ? ' active' : ''}}" onclick="loadFile('${{escapeHtml(fw)}}','${{escapeHtml(f)}}')">${{escapeHtml(f)}}</div>`).join('')}}
      </div>
    </div>`;
  }}).join('');

  document.getElementById('stats').textContent =
    q ? `${{visibleFrameworks}} frameworks · ${{visibleFiles}} files matching "${{q}}"` : '';
}}

function toggleFramework(fw) {{
  if (currentFramework === fw) {{
    currentFramework = null;
  }} else {{
    currentFramework = fw;
  }}
  renderSidebar();
}}

async function loadFile(fw, filename) {{
  currentFramework = fw;
  currentFile = filename;
  renderSidebar();

  document.getElementById('breadcrumb').innerHTML =
    `<span>${{escapeHtml(fw)}}</span> / ${{escapeHtml(filename)}}`;

  const path = `${{fw}}/${{filename}}`;
  let text;
  try {{
    const resp = await fetch(path);
    if (!resp.ok) throw new Error(resp.statusText);
    text = await resp.text();
  }} catch(e) {{
    text = `// Error loading ${{path}}\\n// ${{e.message}}`;
  }}

  document.getElementById('file-content').innerHTML =
    `<pre>${{highlight(text)}}</pre>`;
}}

document.getElementById('search').addEventListener('input', e => {{
  searchQuery = e.target.value;
  renderSidebar();
}});

// Hash-based navigation
function parseHash() {{
  const h = location.hash.slice(1);
  if (!h) return;
  const [fw, file] = h.split('/');
  if (fw && file) loadFile(decodeURIComponent(fw), decodeURIComponent(file));
  else if (fw) {{ currentFramework = decodeURIComponent(fw); renderSidebar(); }}
}}

renderSidebar();
parseHash();
window.addEventListener('hashchange', parseHash);
</script>
</body>
</html>
"""


def build_index(headers_dir: Path) -> dict:
    frameworks = {}
    for framework_dir in sorted(headers_dir.iterdir()):
        if not framework_dir.is_dir():
            continue
        files = sorted(f.name for f in framework_dir.glob("*.h"))
        if files:
            frameworks[framework_dir.name] = files
    return frameworks


def main():
    parser = argparse.ArgumentParser(description="Generate a static HTML header browser")
    parser.add_argument("headers_dir", nargs="?", default="headers",
                        help="Path to headers directory (default: headers/)")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file (default: <headers_dir>/index.html)")
    args = parser.parse_args()

    headers_dir = Path(args.headers_dir).resolve()
    if not headers_dir.exists():
        print(f"Error: headers directory not found: {headers_dir}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else headers_dir / "index.html"

    # Read version from version.txt if present, otherwise parse from directory name
    version_file = headers_dir / "version.txt"
    if version_file.exists():
        ver_text = version_file.read_text().strip()
        # "26.5 (23F77)" format
        import re
        m = re.match(r"^(.+?)\s+\((.+?)\)$", ver_text)
        version, build = (m.group(1), m.group(2)) if m else (ver_text, "")
    else:
        dir_name = headers_dir.name
        parts = dir_name.split("_", 1)
        version = parts[0] if len(parts) >= 1 else dir_name
        build = parts[1] if len(parts) >= 2 else ""

    print(f"Scanning headers in: {headers_dir}")
    frameworks = build_index(headers_dir)
    framework_count = len(frameworks)
    header_count = sum(len(v) for v in frameworks.values())
    print(f"Found {framework_count} frameworks, {header_count} header files")

    index_data = {
        "version": version,
        "build": build,
        "frameworks": list(frameworks.keys()),
        "files": frameworks,
    }

    html = HTML_TEMPLATE.format(
        version=version,
        build=build,
        framework_count=f"{framework_count:,}",
        header_count=f"{header_count:,}",
        generated=datetime.now().strftime("%Y-%m-%d"),
        index_json=json.dumps(index_data, ensure_ascii=False),
    )

    output_path.write_text(html, encoding="utf-8")
    print(f"Generated: {output_path}")
    print()
    print("To browse, run from the headers directory:")
    print(f"  cd {headers_dir}")
    print(f"  python3 -m http.server 8080")
    print(f"  open http://localhost:8080/index.html")


if __name__ == "__main__":
    main()
