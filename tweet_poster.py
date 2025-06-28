import os
import time
import random
import traceback
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Load .env
load_dotenv()
USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")

# 🧹 Remove non-BMP characters (e.g. rare emojis that ChromeDriver can't handle)
def remove_non_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

# ✅ Log in to X.com
def login_to_twitter(driver):
    print("🌐 Navigating to X.com...")
    driver.get("https://x.com/login")
    wait = WebDriverWait(driver, 20)

    try:
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        user_input.send_keys(USERNAME)
        user_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Sometimes Twitter asks for username/email again
        try:
            confirm_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            confirm_input.send_keys(USERNAME)
            confirm_input.send_keys(Keys.RETURN)
            time.sleep(2)
        except TimeoutException:
            pass

        pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        pass_input.send_keys(PASSWORD)
        pass_input.send_keys(Keys.RETURN)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        print("✅ Logged in to X.")

    except Exception as e:
        print("❌ Login failed:")
        traceback.print_exc()
        raise e

from selenium.webdriver.common.action_chains import ActionChains

def post_tweet(driver, raw_tweet):
    wait = WebDriverWait(driver, 15)
    tweet = remove_non_bmp(raw_tweet)

    if not tweet.strip():
        print("❌ Cleaned tweet is empty after removing non-BMP characters.")
        print("📝 Original tweet:", raw_tweet)
        return

    try:
        print("📝 Original tweet:", raw_tweet)
        print("🧹 Cleaned tweet:", tweet)

        # Multiple possible selectors for the tweet box
        tweet_box_selectors = [
            'div[data-testid="tweetTextarea_0"]',
            'div[data-testid="tweetTextarea_0"] div[contenteditable="true"]',
            'div[contenteditable="true"][data-testid*="tweet"]',
            'div[role="textbox"][data-testid*="tweet"]'
        ]
        
        tweet_box = None
        for selector in tweet_box_selectors:
            try:
                tweet_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                print(f"✅ Found tweet box with selector: {selector}")
                break
            except TimeoutException:
                continue
        
        if not tweet_box:
            print("❌ Could not find tweet box with any selector")
            driver.save_screenshot("tweet_box_not_found.png")
            return

        # Clear any existing text and click
        tweet_box.clear()
        tweet_box.click()
        time.sleep(1)

        # Type the tweet content
        tweet_box.send_keys(tweet)
        time.sleep(2)

        # Multiple possible selectors for the tweet button
        tweet_button_selectors = [
            'div[data-testid="tweetButtonInline"]',
            'div[data-testid="tweetButton"]',
            'button[data-testid="tweetButtonInline"]',
            'button[data-testid="tweetButton"]',
            '[role="button"][data-testid*="tweet"]',
            'div[role="button"]:has-text("Post")',
            'button:has-text("Post")'
        ]

        tweet_button = None
        for selector in tweet_button_selectors:
            try:
                # Wait longer and try to find the button
                button_wait = WebDriverWait(driver, 10)
                tweet_button = button_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                print(f"✅ Found tweet button with selector: {selector}")
                break
            except TimeoutException:
                print(f"⏳ Selector {selector} not found, trying next...")
                continue

        # If no button found with selectors, try finding by text
        if not tweet_button:
            try:
                print("🔍 Trying to find button by text content...")
                tweet_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(text(), 'Post')]")))
                print("✅ Found tweet button by text")
            except TimeoutException:
                try:
                    tweet_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Post')]")))
                    print("✅ Found tweet button by button text")
                except TimeoutException:
                    print("❌ Could not find tweet button with any method")
                    driver.save_screenshot("tweet_button_not_found.png")
                    
                    # Debug: Print all buttons on page
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    divs_with_role = driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
                    print(f"🔍 Found {len(buttons)} buttons and {len(divs_with_role)} clickable divs")
                    
                    # Try to find any element with "Post" text
                    all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Post')]")
                    print(f"🔍 Found {len(all_elements)} elements containing 'Post'")
                    
                    return

        # Scroll button into view and click
        driver.execute_script("arguments[0].scrollIntoView(true);", tweet_button)
        time.sleep(1)

        # Try multiple click methods
        click_success = False
        
        # Method 1: Regular click
        try:
            tweet_button.click()
            print("✅ Tweet posted with regular click!")
            click_success = True
        except Exception as e:
            print(f"⚠️ Regular click failed: {e}")

        # Method 2: JavaScript click
        if not click_success:
            try:
                driver.execute_script("arguments[0].click();", tweet_button)
                print("✅ Tweet posted with JavaScript click!")
                click_success = True
            except Exception as e:
                print(f"⚠️ JavaScript click failed: {e}")

        # Method 3: Action chains click
        if not click_success:
            try:
                ActionChains(driver).move_to_element(tweet_button).click().perform()
                print("✅ Tweet posted with ActionChains click!")
                click_success = True
            except Exception as e:
                print(f"⚠️ ActionChains click failed: {e}")

        # Method 4: Send ENTER key to the tweet box
        if not click_success:
            try:
                tweet_box.send_keys(Keys.CONTROL + Keys.RETURN)  # Ctrl+Enter often posts tweets
                print("✅ Tweet posted with Ctrl+Enter!")
                click_success = True
            except Exception as e:
                print(f"⚠️ Ctrl+Enter failed: {e}")

        if not click_success:
            print("❌ All click methods failed")
            driver.save_screenshot("all_clicks_failed.png")
            return

        # Wait a moment to let the tweet process
        time.sleep(3)

    except Exception as e:
        print("❌ Failed to post tweet:")
        traceback.print_exc()
        driver.save_screenshot("tweet_post_fail.png")
        print("📸 Screenshot saved as tweet_post_fail.png")
        
        # Additional debugging - save page source
        try:
            with open("page_source_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("📄 Page source saved as page_source_debug.html")
        except:
            pass
            
        raise e

# ✅ Entrypoint
def main():
    if not os.path.exists("tweet_to_post.txt"):
        print("❌ tweet_to_post.txt not found.")
        return

    with open("tweet_to_post.txt", "r", encoding="utf-8") as f:
        raw_tweet = f.read().strip()

    if not raw_tweet:
        print("❌ tweet_to_post.txt is empty.")
        return

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Comment this for visual debugging
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        login_to_twitter(driver)
        post_tweet(driver, raw_tweet)
    except Exception as e:
        print("❌ Exception during tweet post:", e)
    finally:
        driver.quit()
        if os.path.exists("tweet_to_post.txt"):
            os.remove("tweet_to_post.txt")

if __name__ == "__main__":
    main()
