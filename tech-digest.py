import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")  # Your custom ntfy topic

client = genai.Client(api_key=GEMINI_API_KEY)

# High-signal feeds covering AI, Distributed Systems, and Architecture
FEEDS = {
    "AI / ML": [
        "https://simonwillison.net/atom/everything/",
        "https://huggingface.co/blog/feed.xml",
        "https://openai.com/news/rss.xml",
    ],
    "Systems & Engineering": [
        "https://hnrss.org/frontpage?points=150",
        "https://lobste.rs/rss",
        "https://netflixtechblog.com/feed",
        "https://blog.cloudflare.com/rss/",
    ]
}

def fetch_curated_articles():
    articles = []
    for category, feed_urls in FEEDS.items():
        for url in feed_urls:
            try:
                parsed = feedparser.parse(url)
                if parsed.entries:
                    top_entry = parsed.entries[0]
                    articles.append({
                        "category": category,
                        "title": top_entry.title,
                        "link": top_entry.link
                    })
            except Exception:
                continue

    # Pick 2 AI/ML items and 2 Systems/Architecture items
    ai_picks = [a for a in articles if a["category"] == "AI / ML"][:2]
    sys_picks = [a for a in articles if a["category"] == "Systems & Engineering"][:2]
    return ai_picks + sys_picks

def extract_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return "\n".join([p.get_text() for p in soup.find_all("p")])[:4000]
    except Exception:
        return ""

def generate_summary(item, text):
    prompt = f"""
Summarize this technical article for a Senior Software Engineer's 60-minute morning study block.

Category: {item['category']}
Title: {item['title']}
URL: {item['link']}
Content:
{text}

Output strictly in this format:
### [{item['title']}]({item['link']})
* **Category**: {item['category']}
* **Core Concept**: (What problem is solved? 1-2 lines)
* **Architecture / Mechanisms**: (Specific algorithms, layers, or structures)
* **Key Takeaway**: (Practical mental model or production lesson)
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"### [{item['title']}]({item['link']})\n*Summary unavailable ({e})*"

def push_to_ntfy(topic, markdown_content):
    url = f"https://ntfy.sh/{topic}"
    today_str = datetime.date.today().strftime("%d %b %Y")
    
    headers = {
        "Title": f"Tech Upskill Brief — {today_str}",
        "Priority": "high",
        "Tags": "brain,computer",
        "Markdown": "yes"
    }
    
    # Send the combined markdown digest
    resp = requests.post(
        url,
        data=markdown_content.encode("utf-8"),
        headers=headers,
        timeout=15
    )
    print(f"ntfy response status: {resp.status_code}")

def main():
    items = fetch_curated_articles()
    summaries = []
    
    for item in items:
        raw_text = extract_text(item["link"])
        if len(raw_text) > 200:
            summaries.append(generate_summary(item, raw_text))
            
    if not summaries:
        print("No articles processed.")
        return

    full_digest = "\n\n---\n\n".join(summaries)
    push_to_ntfy(NTFY_TOPIC, full_digest)

if __name__ == "__main__":
    main()
