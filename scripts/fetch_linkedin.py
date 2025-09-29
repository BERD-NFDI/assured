import feedparser
import toml
from datetime import datetime
import re
import os

# RSS feed URL from RSS.app
RSS_FEED_URL = "https://cdn.mysitemapgenerator.com/shareapi/rss/29091480315"
NEWS_TOML_PATH = "content/news/news.toml"

def clean_html(text):
    """Remove HTML tags and clean up text"""
    # Remove HTML tags
    text = re.sub('<.*?>', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Limit length
    if len(text) > 300:
        text = text[:297] + "..."
    return text

def parse_date(date_string):
    """Parse various date formats from RSS"""
    try:
        # Try parsing RSS date format
        dt = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d")
    except:
        try:
            # Try alternative format
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except:
            # Default to today if parsing fails
            return datetime.now().strftime("%Y-%m-%d")

def fetch_linkedin_posts():
    """Fetch and parse LinkedIn posts from RSS feed"""
    print(f"Fetching RSS feed from: {RSS_FEED_URL}")
    
    feed = feedparser.parse(RSS_FEED_URL)
    
    if feed.bozo:
        print(f"Warning: Feed parsing had issues: {feed.bozo_exception}")
    
    posts = []
    
    for entry in feed.entries[:10]:  # Get last 10 posts
        # Extract title
        title = entry.get('title', 'LinkedIn Update')
        if title.startswith('Assured Training posted'):
            title = title.replace('Assured Training posted on LinkedIn', '').strip()
            if not title:
                title = "New LinkedIn Update"
        
        # Extract and clean content
        content = entry.get('summary', entry.get('description', ''))
        clean_content = clean_html(content)
        
        # Extract date
        date = parse_date(entry.get('published', entry.get('pubDate', '')))
        
        # Extract link
        link = entry.get('link', '')
        
        # Create news item
        news_item = {
            'title': title[:100],  # Limit title length
            'anews': clean_content,
            'date': date,
            'by': 'Assured Training',
            'pin': 'false',  # Set to true if you want these in carousel
            'originalurl': link,
            'source': 'linkedin'  # Tag for identification
        }
        
        posts.append(news_item)
        print(f"  - Found post: {title[:50]}... ({date})")
    
    return posts

def update_news_toml(new_posts):
    """Update news.toml file with new posts"""
    
    # Create news.toml if it doesn't exist
    if not os.path.exists(NEWS_TOML_PATH):
        os.makedirs(os.path.dirname(NEWS_TOML_PATH), exist_ok=True)
        with open(NEWS_TOML_PATH, 'w') as f:
            toml.dump({'news': []}, f)
    
    # Load existing news
    with open(NEWS_TOML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        if content.strip():
            existing_data = toml.loads(content)
        else:
            existing_data = {'news': []}
    
    if 'news' not in existing_data:
        existing_data['news'] = []
    
    # Get existing LinkedIn URLs to avoid duplicates
    existing_urls = set()
    for item in existing_data['news']:
        if item.get('originalurl'):
            existing_urls.add(item['originalurl'])
    
    # Add new posts that aren't already in the file
    added_count = 0
    for post in new_posts:
        if post['originalurl'] not in existing_urls:
            # Insert at beginning to keep newest first
            existing_data['news'].insert(0, post)
            added_count += 1
            print(f"  + Added: {post['title'][:50]}...")
    
    # Sort by date (newest first)
    existing_data['news'].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Limit total number of news items if desired (optional)
    # existing_data['news'] = existing_data['news'][:50]  # Keep only last 50 items
    
    # Save updated file
    with open(NEWS_TOML_PATH, 'w', encoding='utf-8') as f:
        toml.dump(existing_data, f)
    
    print(f"\nUpdated {NEWS_TOML_PATH}")
    print(f"  - Added {added_count} new posts")
    print(f"  - Total posts: {len(existing_data['news'])}")

def main():
    """Main function to fetch and update LinkedIn posts"""
    print("LinkedIn RSS Feed Updater")
    print("=" * 50)
    
    try:
        # Fetch posts from RSS
        posts = fetch_linkedin_posts()
        
        if posts:
            print(f"\nFound {len(posts)} posts in RSS feed")
            
            # Update news.toml
            update_news_toml(posts)
            
            # Set some posts as pinned for carousel (optional)
            print("\nTip: Edit news.toml and set 'pin = \"true\"' for posts you want in the carousel")
        else:
            print("No posts found in RSS feed")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
