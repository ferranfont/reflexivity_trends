"""
Reflexivity Time-Series Dashboard
=================================
Reads the point-in-time metrics store (SQLite) and renders one interactive
HTML page per theme, with the five signal layers stacked over time:

  Capa A - Retail crowd     (StockTwits)
  Capa B - Attention        (Wikipedia)
  Capa C - The informed     (EDGAR insiders)
  Capa D - Informed consensus (Polymarket)
  Capa E - Media contagion  (GDELT)

Each layer is a small-multiple line panel (one line per entity). No dual axes:
metrics of different scale live in different panels. Colors follow the entity,
assigned in fixed order (never cycled), matching the project's dark theme.

Usage:
    python -m src.visualization.timeseries_dashboard --theme cybersecurity_ai
"""

import os
import sys
import json
import webbrowser
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.timeseries_store import metrics_store

# Categorical hues in FIXED order — validated set for the dark surface #0f172a
# (passes lightness band, chroma floor, CVD separation, normal-vision floor and
# 3:1 contrast; see dataviz validate_palette). Max 8 series per panel: beyond
# that we show the top 8 and fold the rest — hues are never cycled.
PALETTE = [
    "#3987e5", "#008300", "#d55181", "#c98500",
    "#199e70", "#d95926", "#9085e9", "#e66767",
]
MAX_SERIES_PER_PANEL = 8

# Which metric belongs to which layer, and how to present it.
LAYERS = [
    ("Capa A · Multitud retail", "StockTwits", [
        ("st_msgs_per_hour", "Mensajes / hora"),
        ("st_bull_ratio", "Ratio alcista (0–1)"),
    ]),
    ("Capa B · Atención agregada", "Wikipedia", [
        ("wiki_pageviews", "Visitas diarias"),
    ]),
    ("Capa C · Los informados", "SEC EDGAR", [
        ("edgar_form4_count_30d", "Form 4 (insiders) · 30d"),
        ("edgar_8k_count_30d", "8-K (eventos) · 30d"),
    ]),
    ("Capa D · Consenso informado", "Polymarket", [
        ("pm_prob_yes", "Probabilidad implícita YES"),
    ]),
    ("Capa E · Contagio mediático", "GDELT", [
        ("gdelt_article_count", "Artículos / día (mundo)"),
    ]),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reflexivity Time-Series | {theme_name}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{
            --bg:#0f172a; --card:rgba(30,41,59,0.7); --border:rgba(148,163,184,0.12);
            --text:#f8fafc; --muted:#94a3b8; --accent:#38bdf8;
        }}
        * {{ box-sizing:border-box; }}
        body {{
            font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg);
            background-image:
                radial-gradient(at 0% 0%, rgba(56,189,248,0.12) 0, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139,92,246,0.12) 0, transparent 50%);
            color:var(--text); margin:0; padding:2rem; min-height:100vh;
        }}
        header {{ margin-bottom:2rem; }}
        h1 {{
            font-size:2rem; margin:0;
            background:linear-gradient(90deg,#38bdf8,#818cf8);
            -webkit-background-clip:text; background-clip:text; color:transparent;
        }}
        .sub {{ color:var(--muted); margin-top:.4rem; }}
        .meta {{ display:flex; gap:1rem; margin-top:1rem; flex-wrap:wrap; }}
        .chip {{
            background:var(--card); border:1px solid var(--border); border-radius:.6rem;
            padding:.5rem .9rem; font-size:.85rem;
        }}
        .chip b {{ color:var(--accent); }}
        .panel {{
            background:var(--card); border:1px solid var(--border); border-radius:1rem;
            padding:1.2rem 1.4rem; margin-bottom:1.5rem;
            backdrop-filter:blur(10px);
        }}
        .panel h2 {{ font-size:1.1rem; margin:0 0 .2rem; }}
        .panel .src {{ color:var(--muted); font-size:.8rem; margin-bottom:1rem;
            text-transform:uppercase; letter-spacing:.05em; }}
        .plot {{ width:100%; height:280px; }}
        .empty {{ color:var(--muted); font-style:italic; padding:2rem 0; text-align:center; }}
        .note {{
            background:rgba(56,189,248,0.08); border-left:3px solid var(--accent);
            border-radius:.5rem; padding:1rem 1.2rem; color:#cbd5e1; font-size:.9rem;
            margin-bottom:2rem; line-height:1.5;
        }}
        footer {{ margin-top:3rem; padding-top:1.5rem; border-top:1px solid #1e293b;
            color:#64748b; font-size:.8rem; text-align:center; }}
    </style>
</head>
<body>
    <header>
        <h1>Reflexivity Time-Series Radar</h1>
        <p class="sub">{theme_name} — señales precursoras por capa (dataset point-in-time)</p>
        <div class="meta">
            <div class="chip">Generado <b>{date}</b></div>
            <div class="chip">Puntos almacenados <b>{total_points}</b></div>
            <div class="chip">Rango <b>{date_range}</b></div>
        </div>
    </header>
    <div class="note">
        Cada panel es una capa del marco reflexivo (ver <b>plan_I+D.md</b>). La señal
        operable no está en una serie aislada sino en la <b>divergencia entre capas</b>
        (retail vs. informados) y en la <b>sincronización</b> entre ellas. Con pocos días
        de histórico las tendencias aún no son fiables: el valor aparece al acumular
        semanas de snapshots diarios.
    </div>
    {panels}
    <footer>Reflexivity Trends · Time-Series Module v1.0 · fuentes 100% gratuitas y sin API key</footer>
</body>
</html>
"""


def _panel_html(title, source_name, series_specs, df, color_map, panel_idx):
    """Build one layer panel with one Plotly plot per metric that has data."""
    plots_html = []
    for m_i, (metric, label) in enumerate(series_specs):
        sub = df[df["metric"] == metric]
        div_id = f"plot_{panel_idx}_{m_i}"
        if sub.empty:
            continue
        # Cap series count: keep the top entities by mean value, fold the rest.
        entities_by_weight = (
            sub.groupby("entity")["value"].mean().sort_values(ascending=False)
        )
        kept = set(entities_by_weight.head(MAX_SERIES_PER_PANEL).index)
        folded = len(entities_by_weight) - len(kept)
        sub = sub[sub["entity"].isin(kept)]
        if folded > 0:
            label = f"{label} · top {MAX_SERIES_PER_PANEL} ({folded} más plegadas)"
        traces = []
        for entity, g in sub.groupby("entity"):
            g = g.sort_values("event_date")
            traces.append({
                "x": g["event_date"].tolist(),
                "y": g["value"].tolist(),
                "name": str(entity),
                "mode": "lines+markers",
                "line": {"color": color_map.get(entity, "#8a8a8a"), "width": 2},
                "marker": {"size": 6},
            })
        layout = {
            "title": {"text": label, "font": {"size": 13, "color": "#cbd5e1"}, "x": 0.01},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#94a3b8", "size": 11},
            "xaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
            "yaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
            "margin": {"t": 34, "r": 16, "b": 34, "l": 48},
            "hovermode": "x unified",
            "legend": {"orientation": "h", "y": -0.25, "font": {"size": 10}},
            "showlegend": True,
        }
        plots_html.append(
            f'<div id="{div_id}" class="plot"></div>'
            f'<script>Plotly.newPlot("{div_id}",{json.dumps(traces)},'
            f'{json.dumps(layout)},{{responsive:true,displayModeBar:false}});</script>'
        )

    body = "".join(plots_html) if plots_html else \
        '<div class="empty">Sin datos todavía para esta capa. Ejecuta snapshot_daily.py.</div>'
    return (
        f'<div class="panel"><h2>{title}</h2>'
        f'<div class="src">{source_name}</div>{body}</div>'
    )


def generate_timeseries_dashboard(theme_id="cybersecurity_ai", open_browser=True):
    print(f"\n--- Generating Time-Series Dashboard for: {theme_id} ---")
    theme_conf = config.INVESTING_THEMES.get(theme_id, {})
    theme_name = theme_conf.get("name", theme_id)

    df = metrics_store.load_latest(theme_id)
    total_points = len(df)
    if total_points == 0:
        print("  [!] Store is empty for this theme. Run: python snapshot_daily.py --theme " + theme_id)

    # Fixed-order color assignment per entity, scoped per source (panels never mix
    # sources, so slots can be reused across layers without ambiguity). Within a
    # source, entities are ranked by overall weight so the same entity keeps the
    # same hue in every panel of its layer. No cycling: beyond 8, no color is
    # assigned (those series are folded out by the per-panel cap).
    color_map = {}
    if total_points:
        for _, src_df in df.groupby("source_id"):
            ranked = (
                src_df.groupby("entity")["value"].mean()
                .sort_values(ascending=False).index.tolist()
            )
            for i, e in enumerate(ranked[: len(PALETTE)]):
                color_map[e] = PALETTE[i]

    date_range = (
        f"{df['event_date'].min()} … {df['event_date'].max()}" if total_points else "—"
    )

    panels = "".join(
        _panel_html(title, src, specs, df, color_map, i)
        for i, (title, src, specs) in enumerate(LAYERS)
    )

    html = HTML_TEMPLATE.format(
        theme_name=theme_name,
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_points=total_points,
        date_range=date_range,
        panels=panels,
    )

    theme_dirs = config.get_theme_dirs(theme_id)
    out_path = os.path.join(
        theme_dirs["CHARTS_HTML"],
        f"timeseries_{theme_id}_{datetime.now().strftime('%Y%m%d')}.html",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved: {out_path}")

    if open_browser:
        try:
            webbrowser.get("chrome").open("file://" + out_path)
        except Exception:
            webbrowser.open("file://" + out_path)
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", default="cybersecurity_ai")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    generate_timeseries_dashboard(args.theme, open_browser=not args.no_open)
