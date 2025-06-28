import requests
from bs4 import BeautifulSoup
import random
import time
import feedparser
from datetime import datetime, timedelta
import re
import json

class ContextScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.all_context = []

    def scrape_arxiv_papers(self, keywords, max_papers=5):
        """Scrape recent arXiv papers based on keywords"""
        print("🔬 Scraping arXiv papers...")
        arxiv_context = []
        
        try:
            # Build search query
            search_terms = " OR ".join([f'cat:{kw}' if kw in ['cs.AI', 'cs.LG', 'cs.CL'] else f'all:{kw}' for kw in keywords])
            url = f"http://export.arxiv.org/api/query?search_query={search_terms}&start=0&max_results={max_papers}&sortBy=submittedDate&sortOrder=descending"
            
            response = requests.get(url, timeout=15)
            
            # Parse the XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                published = entry.find('{http://www.w3.org/2005/Atom}published').text
                
                # Clean up the summary (first 200 chars)
                clean_summary = re.sub(r'\s+', ' ', summary)[:200] + "..."
                
                paper_context = f"📄 Recent arXiv: '{title}' - {clean_summary}"
                arxiv_context.append(paper_context)
                
            print(f"✅ Found {len(arxiv_context)} arXiv papers")
            
        except Exception as e:
            print(f"❌ Failed to scrape arXiv: {e}")
            
        return arxiv_context

    def scrape_hackernews(self, keywords, max_items=3):
        """Scrape Hacker News for tech discussions"""
        print("📰 Scraping Hacker News...")
        hn_context = []
        
        try:
            # Search HN using their API
            for keyword in keywords[:2]:  # Limit to avoid too many requests
                url = f"https://hn.algolia.com/api/v1/search?query={keyword}&tags=story&hitsPerPage={max_items}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                for hit in data.get('hits', [])[:max_items]:
                    title = hit.get('title', '')
                    url = hit.get('url', '')
                    points = hit.get('points', 0)
                    
                    if title and points > 10:  # Only high-engagement posts
                        hn_context.append(f"📰 HN ({points} pts): {title}")
                        
            print(f"✅ Found {len(hn_context)} HN stories")
            
        except Exception as e:
            print(f"❌ Failed to scrape HN: {e}")
            
        return hn_context

    def scrape_reddit_tech(self, keywords, max_posts=3):
        """Scrape Reddit tech discussions"""
        print("🔴 Scraping Reddit...")
        reddit_context = []
        
        subreddits = ['MachineLearning', 'artificial', 'singularity', 'OpenAI', 'ChatGPT']
        
        try:
            for subreddit in subreddits[:2]:  # Limit subreddits
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={max_posts}"
                response = requests.get(url, headers=self.headers, timeout=10)
                data = response.json()
                
                for post in data.get('data', {}).get('children', [])[:max_posts]:
                    post_data = post.get('data', {})
                    title = post_data.get('title', '')
                    score = post_data.get('score', 0)
                    
                    if score > 50 and len(title) > 10:  # Filter for engagement
                        reddit_context.append(f"🔴 r/{subreddit} ({score}↑): {title}")
                        
                time.sleep(1)  # Rate limiting
                
            print(f"✅ Found {len(reddit_context)} Reddit posts")
            
        except Exception as e:
            print(f"❌ Failed to scrape Reddit: {e}")
            
        return reddit_context

    def scrape_github_trending(self):
        """Scrape GitHub trending repositories"""
        print("⭐ Scraping GitHub Trending...")
        github_context = []
        
        try:
            url = "https://github.com/trending?l=python&since=daily"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            repos = soup.find_all("article", class_="Box-row")[:3]
            
            for repo in repos:
                name_elem = repo.find("h2", class_="h3")
                if name_elem:
                    name = name_elem.get_text(strip=True).replace("\n", "").replace(" ", "")
                    desc_elem = repo.find("p", class_="col-9")
                    desc = desc_elem.get_text(strip=True) if desc_elem else "No description"
                    
                    github_context.append(f"⭐ Trending: {name} - {desc[:100]}...")
                    
            print(f"✅ Found {len(github_context)} trending repos")
            
        except Exception as e:
            print(f"❌ Failed to scrape GitHub: {e}")
            
        return github_context

    def get_comprehensive_context(self, hashtags_file="hashtags.txt"):
        """Main method to gather context from all sources"""
        print("🚀 Starting comprehensive context scraping...")
        
        # Load hashtags
        try:
            with open(hashtags_file, 'r') as f:
                hashtags = [tag.strip() for tag in f.readlines() if tag.strip()]
        except FileNotFoundError:
            hashtags = ["#AI", "#MachineLearning", "#OpenAI", "#TechNews"]
            
        # Extract keywords for arXiv search
        keywords = [tag.replace("#", "").lower() for tag in hashtags]
        
        # Scrape from all sources
        all_context = []
        
        # 1. ArXiv papers
        arxiv_context = self.scrape_arxiv_papers(keywords, max_papers=3)
        all_context.extend(arxiv_context)
        
        
        # 3. Hacker News
        hn_context = self.scrape_hackernews(keywords, max_items=2)
        all_context.extend(hn_context)
        
        # 4. Reddit
        reddit_context = self.scrape_reddit_tech(keywords, max_posts=2)
        all_context.extend(reddit_context)
        
        # 5. GitHub Trending
        github_context = self.scrape_github_trending()
        all_context.extend(github_context)
        
        # Shuffle and limit context
        random.shuffle(all_context)
        final_context = all_context[:15]  # Limit to prevent context overload
        
        return final_context

    def estimate_tokens(self, text):
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4

    def create_limited_context(self, context, max_tokens=100):
        """Create a context string limited to max_tokens"""
        if not context:
            return ""
        
        # Shuffle for randomness
        random.shuffle(context)
        
        limited_context = []
        current_tokens = 0
        
        for item in context:
            # Clean and shorten each item
            clean_item = item.replace("📄", "").replace("🐦", "").replace("📰", "").replace("🔴", "").replace("⭐", "").strip()
            
            # Take first part of longer items
            if len(clean_item) > 80:
                clean_item = clean_item[:80] + "..."
            
            item_tokens = self.estimate_tokens(clean_item)
            
            if current_tokens + item_tokens <= max_tokens:
                limited_context.append(clean_item)
                current_tokens += item_tokens
            else:
                break
        
        return " | ".join(limited_context)

    def save_context(self, context, filename="context.txt", max_tokens=100):
        """Save both full and limited context"""
        # Save full context for reference
        with open("context_full.txt", "w", encoding="utf-8") as f:
            f.write("=== FULL TECH CONTEXT ===\n\n")
            for i, item in enumerate(context, 1):
                f.write(f"{i}. {item}\n\n")
        
        # Create and save limited context for LLM
        limited_context = self.create_limited_context(context, max_tokens)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(limited_context)
            
        print(f"✅ Saved full context ({len(context)} items) to context_full.txt")
        print(f"✅ Saved limited context (~{self.estimate_tokens(limited_context)} tokens) to {filename}")
        
        return limited_context

def main():
    scraper = ContextScraper()
    
    print("🔍 Gathering comprehensive context from multiple sources...")
    context = scraper.get_comprehensive_context()
    
    if context:
        # Save with token limit (adjust as needed)
        limited_context = scraper.save_context(context, max_tokens=100)
        
        # Also create a summary file for quick reference
        with open("context_summary.txt", "w", encoding="utf-8") as f:
            f.write(f"Context gathered at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total items: {len(context)}\n")
            f.write(f"Limited context tokens: ~{scraper.estimate_tokens(limited_context)}\n\n")
            
            # Group by source
            sources = {}
            for item in context:
                source = item.split()[0]
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
                
            f.write("Sources breakdown:\n")
            for source, count in sources.items():
                f.write(f"  {source}: {count} items\n")
                
            f.write(f"\nLimited context preview:\n{limited_context}")
                
        print(f"\n📊 Context Summary:")
        print(f"   Total items: {len(context)}")
        print(f"   Limited context: ~{scraper.estimate_tokens(limited_context)} tokens")
        for source, count in sources.items():
            print(f"   {source}: {count} items")
            
    else:
        print("❌ No context gathered")

if __name__ == "__main__":
    main()