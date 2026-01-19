
import os
import pandas as pd
from datetime import datetime
from gnews import GNews
from llama_LLM import analizar_noticia_reflexividad
import json

# Setup GNews
def fetch_test_news(topic="DeepSeek AI", count=2):
    print(f"Fetching {count} news items for {topic}...")
    google_news = GNews(language='en', country='US', period='7d', max_results=count)
    results = google_news.get_news(topic)
    
    news_items = []
    for news in results[:count]:
        # Minimal extraction simulation
        try:
            full_content = news.get('description', '')  # Simplification for test
            # In a real scenario we would use requests + BS4 here like in the main script
            # But for this test, we might rely on the snippet or title if extraction fails
            # Let's just use title + description for the test to avoid network issues with scraping
            
            news_item = {
                "title": news.get("title", ""),
                "link": news.get("url", ""),
                "source": news.get("publisher", {}).get("title", ""),
                "date": news.get("published date", ""),
                "full_text": f"{news.get('title', '')}\n\n{news.get('description', '')}"
            }
            news_items.append(news_item)
        except Exception as e:
            print(f"Error processing item: {e}")
            
    return news_items

def run_test():
    print("--- 1. TEST ACQUISITION (GNews) ---")
    news_data = fetch_test_news("DeepSeek AI", 2)
    
    if not news_data:
        print("No news found. Using dummy data for valid testing.")
        news_data = [{
            "title": "DeepSeek-V3 Soars: Evaluation Shows It Rivals GPT-4o",
            "link": "https://example.com/deepseek",
            "source": "TechCrunch",
            "date": datetime.now().isoformat(),
            "full_text": "DeepSeek-V3 has been released and benchmarks suggest it performs on par with OpenAI's GPT-4o. The stock market is reacting wildly, with investors pouring money into Chinese AI stocks. Some experts warn this might be a temporary hype bubble driven by marketing claims rather than real enterprise adoption."
        }]

    print(f"Got {len(news_data)} items.")

    print("\n--- 2. TEST ANALYSIS (Llama 3 via Groq) ---")
    results = []
    for item in news_data:
        print(f"Analyzing: {item['title'][:50]}...")
        analysis = analizar_noticia_reflexividad(item['full_text'])
        
        if analysis:
            result = {
                "news": item,
                "analysis": analysis
            }
            results.append(result)
            print("Analysis success!")
            print(json.dumps(analysis, indent=2))
        else:
            print("Analysis failed.")

    print("\n--- 3. NEO4J OUTPUT INTERPRETATION ---")
    # Here we simulate what the Neo4j analysis script does
    for res in results:
        analysis = res['analysis']
        sentimiento = analysis.get('sentimiento', 0)
        subjetividad = analysis.get('subjetividad', 0)
        fase = analysis.get('fase_hype', 'Unknown')
        
        print(f"\nItem: {res['news']['title']}")
        print(f"  Sentiment: {sentimiento:.2f}")
        print(f"  Subjectivity: {subjetividad:.2f}")
        print(f"  Hype Phase: {fase}")
        
        # Logic from analysis_neo4j.py: find_bubble_candidates
        if subjetividad >= 0.6 and sentimiento >= 0.5:
            print("  [!!!] NEO4J INTERPRETATION: BUBBLE CANDIDATE")
            print("  Reason: High sentiment driven by high subjectivity (speculation/hype).")
            print("  Reflexivity Theory: The narrative is outpacing the reality.")
            
        # Logic from analysis_neo4j.py: find_opportunities
        elif subjetividad <= 0.4 and sentimiento >= 0.3:
            print("  [***] NEO4J INTERPRETATION: SOLID OPPORTUNITY")
            print("  Reason: Positive sentiment backed by low subjectivity (facts/fundamentals).")
            print("  Reflexivity Theory: The reality supports the positive trend.")
            
        else:
            print("  [---] NEO4J INTERPRETATION: NEUTRAL / OBSERVING")
            print("  Reason: Balanced or inconclusive metrics.")

if __name__ == "__main__":
    run_test()
