
import os
import json
import glob
import webbrowser
import pandas as pd
from datetime import datetime

# Configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

DATA_DIR = config.DIRS["DATA"]
# Saving dashboard to CHARTS_HTML to keep outputs organized
OUTPUT_DIR = config.DIRS["CHARTS_HTML"]

# Modern HTML Template with Glassmorphism and Dark Mode
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reflexivity Analysis | Cybersecurity Trends</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(148, 163, 184, 0.1);
            --accent: #38bdf8;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #eab308;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
        }

        .glass-panel {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .metric-card {
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.3);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-dark); 
        }
        ::-webkit-scrollbar-thumb {
            background: #334155; 
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569; 
        }

        .phase-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .sentiment-bar {
            height: 4px;
            background: #334155;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        
        .sentiment-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.5s ease-out;
        }

        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }

        .chart-container {
            width: 100%; 
            height: 500px;
        }
    </style>
</head>
<body class="p-6 md:p-10">

    <!-- Header -->
    <header class="mb-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-indigo-400">
                Reflexivity Radar
            </h1>
            <p class="text-slate-400 mt-2 text-lg">
                Cybersecurity Market Hype vs. Reality Analysis
            </p>
        </div>
        <div class="flex gap-3">
            <div class="glass-panel px-4 py-2 flex flex-col items-center">
                <span class="text-xs text-slate-400 uppercase tracking-wider">Analysis Date</span>
                <span class="font-mono text-sky-400 font-semibold"><!-- DATE_PLACEHOLDER --></span>
            </div>
            <div class="glass-panel px-4 py-2 flex flex-col items-center">
                <span class="text-xs text-slate-400 uppercase tracking-wider">Articles</span>
                <span class="font-mono text-sky-400 font-semibold"><!-- COUNT_PLACEHOLDER --></span>
            </div>
        </div>
    </header>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
        
        <!-- Interactive Scatter Plot -->
        <div class="glass-panel p-6 lg:col-span-2">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-semibold flex items-center gap-2">
                    <svg class="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
                    Reflexivity Matrix
                </h2>
                <div class="flex gap-4 text-xs text-slate-400">
                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span> Bubble Risk</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500"></span> Opportunity</span>
                </div>
            </div>
            <div id="reflexivityChart" class="chart-container"></div>
        </div>

        <!-- Key Insights / Metrics -->
        <div class="space-y-6">
            <!-- Top Metric -->
            <div class="glass-panel p-6 metric-card">
                <h3 class="text-sm font-semibold text-slate-400 uppercase mb-4">Market Sentiment</h3>
                <div class="flex items-end gap-3 mb-2">
                    <span class="text-4xl font-bold text-white"><!-- AVG_SENTIMENT_PLACEHOLDER --></span>
                    <span class="text-sm text-slate-400 mb-1">/ 1.0</span>
                </div>
                <div class="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-sky-500 to-indigo-500" style="width: <!-- SENTIMENT_PCT_PLACEHOLDER -->%"></div>
                </div>
                <p class="text-xs text-slate-500 mt-3">Average sentiment across all analyzed articles.</p>
            </div>

            <!-- Bubble Watch -->
            <div class="glass-panel p-6 metric-card border-l-4 border-l-red-500">
                <h3 class="text-sm font-semibold text-red-400 uppercase mb-4">Bubble Watch</h3>
                <ul class="space-y-3">
                    <!-- BUBBLE_LIST_PLACEHOLDER -->
                </ul>
            </div>

            <!-- Opportunity Watch -->
            <div class="glass-panel p-6 metric-card border-l-4 border-l-green-500">
                <h3 class="text-sm font-semibold text-green-400 uppercase mb-4">Solid Opportunities</h3>
                <ul class="space-y-3">
                    <!-- OPPORTUNITY_LIST_PLACEHOLDER -->
                </ul>
            </div>
        </div>
    </div>

    <!-- News Feed -->
    <h2 class="text-2xl font-bold mb-6 flex items-center gap-2">
        <svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
        Latest Analysis Stream
    </h2>
    <div class="news-grid">
        <!-- NEWS_CARDS_PLACEHOLDER -->
    </div>

    <footer class="mt-20 pt-10 border-t border-slate-800 text-center text-slate-500 text-sm">
        <p>Generated by Reflexivity Trends Agent | <span class="text-slate-600">Reflexivity Model v1.0</span></p>
    </footer>

    <script>
        // Data passed from Python
        const chartData = <!-- CHART_DATA_JSON_PLACEHOLDER -->;

        // Prepare Plotly Data
        const trace = {
            x: chartData.map(d => d.subjetividad),
            y: chartData.map(d => d.sentimiento),
            text: chartData.map(d => `<b>${d.titulo}</b><br>Phase: ${d.fase}<br>Cat: ${d.categoria}`),
            mode: 'markers',
            marker: {
                size: 14,
                color: chartData.map(d => {
                    // Color logic based on zones
                    if (d.subjetividad > 0.6 && d.sentimiento > 0.5) return '#ef4444'; // Red (Bubble)
                    if (d.subjetividad < 0.4 && d.sentimiento > 0.3) return '#22c55e'; // Green (Opportunity)
                    return '#38bdf8'; // Blue (Neutral)
                }),
                opacity: 0.8,
                line: {
                    color: 'white',
                    width: 1
                }
            },
            hoverinfo: 'text'
        };

        const layout = {
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: '#94a3b8',
                family: 'Outfit, sans-serif'
            },
            xaxis: {
                title: 'Subjectivity (Hype/Speculation)',
                range: [0, 1],
                gridcolor: '#334155',
                zerolinecolor: '#475569'
            },
            yaxis: {
                title: 'Sentiment (Market Mood)',
                range: [-1, 1],
                gridcolor: '#334155',
                zerolinecolor: '#475569'
            },
            shapes: [
                // Highlight Zones (optional, keep clean for now)
            ],
            margin: { t: 20, r: 20, b: 50, l: 50 },
            hovermode: 'closest'
        };

        Plotly.newPlot('reflexivityChart', [trace], layout, {responsive: true, displayModeBar: false});
    </script>
</body>
</html>
"""

# ... (imports remain) ...

def generate_dashboard(theme_id="cybersecurity_ai"):
    print(f"\n--- Generating Dashboard for Theme: {theme_id} ---")
    
    # 1. Resolve Theme Paths
    theme_dirs = config.get_theme_dirs(theme_id)
    data_dir = theme_dirs["DATA"]
    output_dir = theme_dirs["CHARTS_HTML"]
    
    # 2. Find latest data in THEME folder
    # Priority: Analyzed > Unified (Raw)
    analyzed_pattern = os.path.join(data_dir, "analyzed_reflexivity_*.json")
    unified_pattern = os.path.join(data_dir, "unified_data_*.json")
    
    analyzed_files = glob.glob(analyzed_pattern)
    unified_files = glob.glob(unified_pattern)
    
    data_is_analyzed = False
    
    if analyzed_files:
        files = analyzed_files
        print("Found ANALYZED data. Using it for dashboard.")
        data_is_analyzed = True
    elif unified_files:
        files = unified_files
        print("Found only RAW data. Dashboard will show neutral stats.")
    else:
        files = []
    
    if not files:
        print(f"No data found in {data_dir}")
        return
        
    latest_file = max(files, key=os.path.getmtime)
    print(f"Loading data from: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # ... (Rest of processing remains mostly the same, ensuring 'data' is valid list) ...
    if not isinstance(data, list):
         print("Error: JSON data is not a list of articles.")
         return

    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate Metrics
    avg_sentiment = df['metadata'].apply(lambda x: x.get('average_interest', 0) if isinstance(x, dict) else 0).mean() # Simplified for now, or use 'sentiment' if available
    # Wait, the data structure depends on GNews vs SerpApi.
    # GNews has 'metadata' but maybe not 'sentiment'.
    # If using verify_integration.py dummy data, it had 'subjetividad' and 'sentimiento'.
    # But main_news_fetcher fetches REAL data (ArticleModel).
    # ArticleModel has: source_id, source_name, title, url, published_date, abstract, full_text, metadata.
    # It does NOT have 'sentimiento' or 'subjetividad' computed yet! That happens in the ANALYSIS step (LLM).
    # The current dashboard expects analyzed data.
    # The 'unified_data_*.json' contains RAW articles.
    # To test the dashboard properly, we need data with 'sentimiento' and 'subjetividad'.
    # The current 'main_news_fetcher' only acquires raw data. It does not run analysis.
    # However, to avoid 'NameError: html', I must generate the HTML string.
    # I will adapt the dashboard to handle raw data gracefully or mock the missing fields for visualization.
    
    # Let's check keys in df
    has_analysis = 'sentimiento' in df.columns
    
    avg_sentiment = df['sentimiento'].mean() if has_analysis and not df['sentimiento'].isnull().all() else 0
    article_count = len(df)
    date_str = datetime.now().strftime("%B %d, %Y")
    
    # Identify Bubble Candidates & Opportunities (Mock or Real)
    if has_analysis:
        bubbles = df[(df['subjetividad'] > 0.6) & (df['sentimiento'] > 0.5)].head(3)
        opps = df[(df['subjetividad'] < 0.4) & (df['sentimiento'] > 0.3)].head(3)
    else:
        bubbles = pd.DataFrame()
        opps = pd.DataFrame()
    
    # generate lists HTML
    bubble_html = ""
    for _, row in bubbles.iterrows():
        bubble_html += f"""
        <li class="p-3 rounded bg-red-500/10 border border-red-500/20">
            <div class="font-bold text-red-200 truncate">{row.get('title', 'No Title')[:40]}...</div>
            <div class="text-xs text-red-400 mt-1">Subj: {row.get('subjetividad',0):.2f} | Sent: {row.get('sentimiento',0):.2f}</div>
        </li>
        """
        
    opp_html = ""
    for _, row in opps.iterrows():
        opp_html += f"""
        <li class="p-3 rounded bg-green-500/10 border border-green-500/20">
            <div class="font-bold text-green-200 truncate">{row.get('title', 'No Title')[:40]}...</div>
            <div class="text-xs text-green-400 mt-1">Subj: {row.get('subjetividad',0):.2f} | Sent: {row.get('sentimiento',0):.2f}</div>
        </li>
        """

    # Generate News Cards HTML
    news_cards_html = ""
    for _, row in df.iterrows():
        # Clean entities
        try:
            ents = row.get('metadata', {}).get('entities', []) 
            # Fallback if ents is not a list
            if isinstance(ents, str): ents = [ents]
            ents_badges = "".join([f'<span class="px-2 py-1 bg-slate-700 rounded text-xs text-slate-300">{str(e)}</span>' for e in ents[:3]])
        except:
            ents_badges = ""
            
        # Sentiment fallback
        sent = row.get('sentimiento', 0)
        sent_color = "bg-green-500" if sent > 0.2 else ("bg-red-500" if sent < -0.2 else "bg-slate-400")
        sent_width = (sent + 1) * 50 # Map -1..1 to 0..100
        
        url = row.get('url') or '#'
        title = row.get('title', 'No Title')
        
        # Use abstract as 'razonamiento' fallback
        desc = row.get('razonamiento', row.get('abstract', ''))
        
        card = f"""
        <div class="glass-panel p-5 metric-card flex flex-col h-full relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-1 h-full {sent_color}"></div>
            
            <div class="flex justify-between items-start mb-3 pl-3">
                <span class="phase-badge bg-indigo-500/20 text-indigo-300">{row.get('fase_hype', 'Raw Data')[:15]}</span>
                <span class="text-xs text-slate-500">{row.get('source_name', 'Source')[:15]}</span>
            </div>
            
            <h3 class="font-bold text-lg leading-tight mb-2 pl-3 flex-grow">
                <a href="{url}" target="_blank" class="hover:text-sky-400 transition-colors">
                    {title[:80]}...
                </a>
            </h3>
            
            <p class="text-sm text-slate-400 mb-4 pl-3 line-clamp-3">
                {desc}
            </p>
            
            <div class="mt-auto pl-3">
                <div class="flex flex-wrap gap-2 mb-3">
                    {ents_badges}
                </div>
                
                <div class="flex justify-between items-center text-xs text-slate-500 mb-1">
                    <span>Sentiment</span>
                    <span>{sent:.2f}</span>
                </div>
                <div class="w-full bg-slate-700 h-1 rounded-full overflow-hidden">
                    <div class="h-full {sent_color}" style="width: {sent_width}%"></div>
                </div>
            </div>
        </div>
        """
        news_cards_html += card

    # Prepare Chart JSON
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            'titulo': row.get('title', '')[:50],
            'sentimiento': row.get('sentimiento', 0),
            'subjetividad': row.get('subjetividad', 0), # Default to 0 if not analyzed
            'fase': row.get('fase_hype', 'Raw'),
            'categoria': row.get('source_name', '')
        })
    chart_json = json.dumps(chart_data)

    # Determine Correct Messages
    if data_is_analyzed:
        no_bubble_msg = '<li class="text-slate-400 text-sm">No bubble risks detected in current timeframe.</li>'
        no_opp_msg = '<li class="text-slate-400 text-sm">No clear opportunities detected in current timeframe.</li>'
    else:
        no_bubble_msg = '<li class="text-slate-400 text-sm">Waiting for Analysis... (Raw Data)</li>'
        no_opp_msg = '<li class="text-slate-400 text-sm">Waiting for Analysis... (Raw Data)</li>'

    # Initialize HTML
    html = HTML_TEMPLATE

    # Specific Replacements
    html = html.replace('<!-- DATE_PLACEHOLDER -->', date_str)
    html = html.replace('<!-- COUNT_PLACEHOLDER -->', str(article_count))
    html = html.replace('<!-- AVG_SENTIMENT_PLACEHOLDER -->', f"{avg_sentiment:.2f}")
    html = html.replace('<!-- SENTIMENT_PCT_PLACEHOLDER -->', f"{(avg_sentiment+1)*50:.0f}")
    html = html.replace('<!-- BUBBLE_LIST_PLACEHOLDER -->', bubble_html or no_bubble_msg)
    html = html.replace('<!-- OPPORTUNITY_LIST_PLACEHOLDER -->', opp_html or no_opp_msg)
    html = html.replace('<!-- NEWS_CARDS_PLACEHOLDER -->', news_cards_html)
    html = html.replace('<!-- CHART_DATA_JSON_PLACEHOLDER -->', chart_json)

    # 4. Save to Theme Output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_filename = f"dashboard_{theme_id}_{datetime.now().strftime('%Y%m%d')}.html"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Dashboard generated: {output_path}")
    
    # 5. Open in Chrome (Automatic)
    print("Opening in browser...")
    try:
        webbrowser.get('chrome').open('file://' + output_path)
    except:
        webbrowser.open('file://' + output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Dashboard for a specific theme")
    parser.add_argument("--theme", type=str, default="cybersecurity_ai", help="Theme ID from config.py")
    args = parser.parse_args()
    
    generate_dashboard(theme_id=args.theme)
