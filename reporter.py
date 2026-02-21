
import json
import os
from datetime import datetime
from collections import defaultdict


def build_report(files: list[dict], results: list[dict], output_dir: str) -> dict:

    category_stats = defaultdict(lambda: {"count": 0, "total_bytes": 0, "extensions": set()})
    extension_counts = defaultdict(int)
    largest_file = None
    largest_size = 0

    for f in files:
        cat = f.get("category", "Miscellaneous")
        size = f.get("size_bytes", 0)
        ext = f.get("extension", "unknown")

        category_stats[cat]["count"] += 1
        category_stats[cat]["total_bytes"] += size
        category_stats[cat]["extensions"].add(ext)
        extension_counts[ext] += 1

        if size > largest_size:
            largest_size = size
            largest_file = f["name"]

    # Convert sets to lists for JSON serialization
    for cat in category_stats:
        category_stats[cat]["extensions"] = sorted(
            list(category_stats[cat]["extensions"])
        )

    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = sum(1 for r in results if str(r.get("status", "")).startswith("error"))

    most_common_ext = max(extension_counts, key=extension_counts.get) if extension_counts else "N/A"

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "output_directory": output_dir,
        "summary": {
            "total_files": len(files),
            "files_organized": success_count,
            "files_failed": error_count,
            "total_categories": len(category_stats),
            "largest_file": largest_file or "N/A",
            "largest_file_bytes": largest_size,
            "most_common_extension": most_common_ext,
        },
        "categories": dict(category_stats),
        "extension_breakdown": dict(extension_counts),
    }

    return report


def save_json_report(report: dict, output_dir: str) -> str:
    path = os.path.join(output_dir, "organizer_report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return path


def save_html_report(report: dict, output_dir: str) -> str:
    """Generates a slick HTML dashboard."""

    cats = report["categories"]
    ext_breakdown = report["extension_breakdown"]
    summary = report["summary"]

    # Build category rows
    cat_rows = ""
    cat_chart_labels = []
    cat_chart_data = []

    ICONS = {
        "Documents": "📄", "Images": "🖼️", "Videos": "🎬",
        "Audio": "🎵", "Code": "💻", "Archives": "🗜️",
        "Spreadsheets": "📊", "Presentations": "📽️", "Finance": "💰",
        "Academic": "🎓", "Career": "💼", "Screenshots": "📸",
        "Backups": "💾", "Installers": "⚙️", "Executables": "🔧",
        "Miscellaneous": "📦",
    }

    for cat, data in sorted(cats.items(), key=lambda x: -x[1]["count"]):
        icon = ICONS.get(cat, "📁")
        mb = data["total_bytes"] / (1024 * 1024)
        exts = ", ".join(data["extensions"][:6]) or "—"
        cat_rows += f"""
        <tr>
          <td><span class="cat-icon">{icon}</span> {cat}</td>
          <td><span class="badge">{data['count']}</span></td>
          <td>{mb:.2f} MB</td>
          <td class="ext-cell">{exts}</td>
        </tr>"""
        cat_chart_labels.append(cat)
        cat_chart_data.append(data["count"])

    # Extension breakdown (top 10)
    top_exts = sorted(ext_breakdown.items(), key=lambda x: -x[1])[:10]
    ext_labels = [e[0] or "no-ext" for e in top_exts]
    ext_data = [e[1] for e in top_exts]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Smart File Organizer — Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0a0a0f;
      --surface: #111118;
      --card: #16161f;
      --border: #2a2a3d;
      --accent: #00e5ff;
      --accent2: #7c4dff;
      --text: #e0e0f0;
      --muted: #6b6b8a;
      --success: #00e676;
      --danger: #ff5252;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: "sans-serif", Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }}
    .noise {{
      position: fixed; inset: 0; pointer-events: none; z-index: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    }}
    .container {{ max-width: 1100px; margin: 0 auto; position: relative; z-index: 1; }}
    header {{ margin-bottom: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 2rem; }}
    .header-top {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }}
    .logo {{ font-family: 'Space Mono', monospace; font-size: 0.75rem; color: var(--muted);
             letter-spacing: 0.05em; }}
    h1 {{ font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em; }}
    h1 span {{ color: var(--accent); }}
    .meta {{ font-family: 'Space Mono', monospace; font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                   gap: 1rem; margin-bottom: 2.5rem; }}
    .stat-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 1.4rem; position: relative; overflow: hidden;
      transition: border-color 0.2s;
    }}
    .stat-card::before {{
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
    }}
    .stat-card:hover {{ border-color: var(--accent); }}
    .stat-label {{ font-size: 0.7rem; font-family: 'Space Mono', monospace;
                   text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 0.5rem; }}
    .stat-value {{ font-size: 2rem; font-weight: 800; color: var(--accent); }}
    .stat-sub {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.3rem;
                 font-family: 'Space Mono', monospace; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
    @media (max-width: 700px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
    .card h2 {{ font-size: 0.8rem; font-family: 'Space Mono', monospace; text-transform: uppercase;
                letter-spacing: 0.1em; color: var(--muted); margin-bottom: 1.2rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
    th {{ text-align: left; padding: 0.5rem 0.75rem; font-family: 'Space Mono', monospace;
          font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em;
          color: var(--muted); border-bottom: 1px solid var(--border); }}
    td {{ padding: 0.75rem; border-bottom: 1px solid rgba(42,42,61,0.5); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(0,229,255,0.03); }}
    .cat-icon {{ font-size: 1.1rem; margin-right: 0.4rem; }}
    .badge {{ background: rgba(0,229,255,0.1); color: var(--accent); font-family: 'Space Mono', monospace;
              font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700; }}
    .ext-cell {{ font-family: 'Space Mono', monospace; font-size: 0.72rem; color: var(--muted); }}
    .chart-wrap {{ position: relative; height: 220px; }}
    footer {{ text-align: center; margin-top: 3rem; padding-top: 2rem;
              border-top: 1px solid var(--border);
              font-family: 'Space Mono', monospace; font-size: 0.7rem; color: var(--muted); }}
  </style>
</head>
<body>
  <div class="noise"></div>
  <div class="container">
    <header>
      <div class="header-top">
        <span class="logo">FILE ORGANIZER</span>
      </div>
      <h1>Organization Report</h1>
      <div class="meta">Generated: {report['generated_at']} &nbsp;|&nbsp; Output: {report['output_directory']}</div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Files</div>
        <div class="stat-value">{summary['total_files']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Organized</div>
        <div class="stat-value" style="color:var(--success)">{summary['files_organized']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Failed</div>
        <div class="stat-value" style="color:var(--danger)">{summary['files_failed']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Categories</div>
        <div class="stat-value" style="color:var(--accent2)">{summary['total_categories']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Largest File</div>
        <div class="stat-value" style="font-size:1.1rem">📦</div>
        <div class="stat-sub">{summary['largest_file']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Top Extension</div>
        <div class="stat-value" style="font-size:1.4rem; font-family:'Space Mono',monospace">{summary['most_common_extension']}</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h2>Files by Category</h2>
        <div class="chart-wrap">
          <canvas id="catChart"></canvas>
        </div>
      </div>
      <div class="card">
        <h2>Top Extensions</h2>
        <div class="chart-wrap">
          <canvas id="extChart"></canvas>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>Category Breakdown</h2>
      <table>
        <thead>
          <tr><th>Category</th><th>Files</th><th>Size</th><th>Extensions</th></tr>
        </thead>
        <tbody>{cat_rows}</tbody>
      </table>
    </div>

    <footer>File Organizer —  Project</footer>
  </div>

  <script>
    const COLORS = ['#00e5ff','#7c4dff','#00e676','#ff5252','#ff9100','#e040fb',
                    '#69f0ae','#40c4ff','#ffd740','#ff6e40','#b9f6ca','#ea80fc'];

    new Chart(document.getElementById('catChart'), {{
      type: 'doughnut',
      data: {{
        labels: {json.dumps(cat_chart_labels)},
        datasets: [{{ data: {json.dumps(cat_chart_data)}, backgroundColor: COLORS,
                      borderColor: '#16161f', borderWidth: 3 }}]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'right', labels: {{ color: '#e0e0f0', font: {{ size: 11 }}, boxWidth: 12 }} }} }}
      }}
    }});

    new Chart(document.getElementById('extChart'), {{
      type: 'bar',
      data: {{
        labels: {json.dumps(ext_labels)},
        datasets: [{{ data: {json.dumps(ext_data)}, backgroundColor: COLORS,
                      borderRadius: 6 }}]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ ticks: {{ color: '#6b6b8a', font: {{ family: 'Space Mono', size: 10 }} }},
               grid: {{ color: '#1a1a2e' }} }},
          y: {{ ticks: {{ color: '#6b6b8a' }}, grid: {{ color: '#1a1a2e' }} }}
        }}
      }}
    }});
  </script>
</body>
</html>"""

    path = os.path.join(output_dir, "organizer_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path