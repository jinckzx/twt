import os
import random
import time
import smtplib
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText

# Updated imports for enhanced context scraper
from tweet_generator import generate_tweet_with_validation
from context_scraper import ContextScraper  # Updated import
from tweet_poster import login_to_twitter, post_tweet

# Load .env
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

HASHTAGS_FILE = "hashtags.txt"
CONTEXT_FILE = "context.txt"
TWEET_FILE = "tweet_to_post.txt"
POSTED_FILE = "posted_tweets.txt"

def random_sleep(min_secs=7200, max_secs=14400):
    """Sleep for random duration between posts"""
    wait = random.randint(min_secs, max_secs)
    print(f"⏳ Sleeping for {wait // 60} minutes...")
    time.sleep(wait)

def send_email_notification(tweet):
    """Send email notification when tweet is posted"""
    if not all([EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
        print("⚠️ Email not configured in .env")
        return
    try:
        # Include context info in email
        context_info = ""
        if os.path.exists("context_summary.txt"):
            with open("context_summary.txt", "r", encoding="utf-8") as f:
                context_info = f.read()
        
        email_body = f"""✅ Tweet posted successfully!

Tweet: {tweet}

Context Summary:
{context_info}

Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        msg = MIMEText(email_body)
        msg["Subject"] = "GenAI Bot: New Tweet Posted"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("📧 Email notification sent.")
    except Exception as e:
        print(f"❌ Email notification failed: {e}")

def already_posted(tweet):
    """Check if tweet was already posted to avoid duplicates"""
    if not os.path.exists(POSTED_FILE):
        return False
    
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            posted_tweets = f.read()
            # Check for exact match or very similar tweets (first 50 chars)
            return tweet in posted_tweets or tweet[:50] in posted_tweets
    except Exception as e:
        print(f"⚠️ Error checking posted tweets: {e}")
        return False

def save_posted(tweet):
    """Save posted tweet to history with timestamp"""
    try:
        with open(POSTED_FILE, "a", encoding="utf-8") as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {tweet}\n")
    except Exception as e:
        print(f"⚠️ Error saving posted tweet: {e}")

def write_tweet(tweet):
    """Write tweet to file for posting"""
    with open(TWEET_FILE, "w", encoding="utf-8") as f:
        f.write(tweet)

def gather_enhanced_context():
    """Use the enhanced context scraper to gather comprehensive context"""
    print("🔍 Gathering enhanced context from multiple sources...")
    
    try:
        scraper = ContextScraper()
        context = scraper.get_comprehensive_context()
        
        if context:
            # This creates both context.txt (limited) and context_full.txt
            limited_context = scraper.save_context(context, max_tokens=100)  # Adjust token limit as needed
            print(f"✅ Enhanced context gathered successfully")
            return True
        else:
            print("⚠️ No context gathered, will generate tweet without context")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced context scraping failed: {e}")
        print("📝 Falling back to basic context scraping...")
        
        # Fallback to basic scraping if enhanced fails
        try:
            from context_scraper import scrape_tweets  # Old function as fallback
            
            with open(HASHTAGS_FILE, "r", encoding="utf-8") as f:
                hashtags = [line.strip() for line in f if line.strip()]
            selected = random.sample(hashtags, k=min(2, len(hashtags)))
            
            context = scrape_tweets(selected)
            with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
                for line in context:
                    f.write(line + "\n")
            return True
            
        except Exception as fallback_error:
            print(f"❌ Fallback context scraping also failed: {fallback_error}")
            return False

def run_once():
    """Run one complete cycle: context -> generate -> post"""
    print(f"\n🚀 Starting new tweet cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Gather enhanced context
    context_success = gather_enhanced_context()
    
    # 2. Generate tweet with enhanced validation
    print("🤖 Generating tweet...")
    tweet = generate_tweet_with_validation(CONTEXT_FILE)
    
    if not tweet:
        print("❌ Tweet generation failed completely.")
        return

    # 3. Check for duplicates
    if already_posted(tweet):
        print("⚠️ Duplicate or very similar tweet detected. Skipping.")
        return

    print(f"📝 Generated tweet: {tweet}")
    
    # 4. Save for posting
    write_tweet(tweet)
    save_posted(tweet)

    # 5. Post with Selenium
    print("📤 Posting tweet...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        login_to_twitter(driver)
        post_tweet(driver, tweet)
        print("✅ Tweet posted successfully!")
        send_email_notification(tweet)
        
    except Exception as e:
        print(f"❌ Failed to post tweet: {e}")
        # Remove from posted tweets since it wasn't actually posted
        try:
            if os.path.exists(POSTED_FILE):
                with open(POSTED_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(POSTED_FILE, "w", encoding="utf-8") as f:
                    f.writelines(lines[:-1])  # Remove last line
        except:
            pass
            
    finally:
        driver.quit()
        # Clean up tweet file
        if os.path.exists(TWEET_FILE):
            os.remove(TWEET_FILE)

def cleanup_old_files():
    """Clean up old temporary files"""
    temp_files = ["tweet_post_fail.png", "page_source_debug.html", "tweet_button_not_found.png"]
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    print("🤖 GenAI Twitter Bot Started!")
    print("📊 Enhanced multi-source context scraping enabled")
    
    # Clean up any old debug files
    cleanup_old_files()
    
    while True:
        try:
            run_once()
            print(f"✅ Cycle completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            random_sleep()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            print("⏳ Waiting 30 minutes before retry...")
            time.sleep(1800)  # Wait 30 minutes before retrying