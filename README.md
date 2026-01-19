# reflexivity_trends - Reflexivity Analysis for Cybersecurity News

An advanced trend analysis system that applies George Soros' **Theory of Reflexivity** to cybersecurity news. It detects market anomalies, hype bubbles, and solid investment opportunities by contrasting **Sentiment** (how people feel) against **Subjectivity** (how factual the information is).

## 📂 Project Structure

```text
reflexivity_trends/
├── data/                  # CSVs, JSONs, and intermediate data
├── outputs/               # Generated visualizations and reports
├── src/                   # Source code
│   ├── acquisition_data_manager/       # Data gathering modules
│   │   └── main_news_fetcher.py
│   ├── attribution_analysis/ # LLM & Logic modules
│   │   └── find_metadata_IA_llama_LLM.py
│   ├── database/          # Knowledge graph modules
│   │   └── atribution_mapping_neo4j.py
│   └── visualization/     # Dashboard generation
│       └── dashboard_generator.py (Coming Soon)
├── .env                   # Configuration (API Keys)
└── .gitignore
```

## 🚀 Features

*   **Acquisition**: Fetches news from Google News based on trending cybersecurity topics (AI Threat Detection, CTEM, etc.).
*   **Analysis (Llama 3)**: Analyzes each article for:
    *   **Sentiment**: (-1.0 to 1.0)
    *   **Subjectivity**: (0.0 to 1.0) - The "Hype" factor.
    *   **Hype Phase**: Innovation Trigger, Peak of Inflated Expectations, etc.
*   **Knowledge Graph (Neo4j)**: Maps relationships between News, Companies, and Concepts to detect narrative contagion.
*   **Visualization**: Interactive web dashboard to spot bubbles and opportunities (Coming Soon).

## 🛠️ Setup

1.  **Install Dependencies**:
    ```bash
    pip install pandas pytrends matplotlib plotly python-dotenv gnews groq neo4j sentence-transformers
    ```

2.  **Configuration**:
    Create a `.env` file in the root directory:
    ```ini
    GROQ_API_KEY=your_groq_api_key
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_password
    ```

## 🏃 Usage

### 1. Fetch News
```bash
python src/acquisition_data_manager/main_news_fetcher.py
```
*Outputs to `data/gnews_cybersecurity_YYYYMMDD.csv`*

### 2. Analyze with Llama 3
```bash
python src/attribution_analysis/find_metadata_IA_llama_LLM.py
```
*Outputs to `data/cybersecurity_reflexivity_YYYYMMDD.json`*

### 3. Ingest into Neo4j
```bash
python src/database/atribution_mapping_neo4j.py
```
*Populates your local Neo4j database.*

## 🧠 Theory of Reflexivity in Tech

*   **Bubble Candidate**: High Sentiment (>0.7) + High Subjectivity (>0.6). The narrative is outpacing the facts.
*   **Solid Opportunity**: High Sentiment (>0.5) + Low Subjectivity (<0.4). Optimism is backed by data.
*   **FUD (Fear, Uncertainty, Doubt)**: Low Sentiment + High Subjectivity. Negative rumors without basis.

## 📄 License
MIT
