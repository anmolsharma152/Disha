#!/usr/bin/env python3
"""
Fetch top 3 post titles from a public RSS feed.
"""
import feedparser

# BBC News RSS feed - reliable and publicly accessible
RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"

def main():
    feed = feedparser.parse(RSS_URL)
    
    if feed.bozo:
        print(f"Warning: Feed parsing had issues: {feed.bozo_exception}")
    
    if not feed.entries:
        print("No entries found in the feed")
        return
    
    print("Top 3 post titles from BBC News:")
    print("-" * 40)
    
    for i, entry in enumerate(feed.entries[:3], 1):
        title = entry.get('title', 'No title available')
        print(f"{i}. {title}")

if __name__ == "__main__":
    main()