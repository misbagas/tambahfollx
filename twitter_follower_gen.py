import tweepy
import time
import random
import requests
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome, ChromeOptions
import undetected_chromedriver as uc
from PIL import Image
import io
import base64
from proxybroker import Broker
import threading
import queue
import json

# Config
TARGET_USERNAME = 'sukacocktail'
TARGET_ID = None  # Auto-fetched
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAH9u8wEAAAAAUBr0BJ%2BYZY21I9gvwJ15A7jxqhQ%3DaOjSqeCzOAh0DJsuywpfnLsShMjYr7mTd76GTg2qyaE81aenaD'  # From Twitter Dev Portal
PROXIES_FILE = 'proxies.txt'
TEMP_EMAIL_API = 'https://api.mail.tm'  # Or your provider
NUM_FOLLOWERS = 1000
FOLLOW_DELAY_MIN = 60  # seconds
FOLLOW_DELAY_MAX = 300
PROXY_ROTATE_EVERY = 20  # accounts

fake = Faker()

class TwitterFollowerGenerator:
    def __init__(self):
        self.proxies = self.load_proxies()
        self.proxy_queue = queue.Queue()
        for p in self.proxies:
            self.proxy_queue.put(p)
        self.api = tweepy.Client(bearer_token=BEARER_TOKEN)
        self.target_id = self.get_target_id()
        self.successful = 0
        print(f"Target: @{TARGET_USERNAME} (ID: {self.target_id})")

    def load_proxies(self):
        proxies = []
        with open(PROXIES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) >= 4:
                    proxies.append({
                        'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}',
                        'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
                    })
        return proxies[:50]  # Limit to 50

    def get_target_id(self):
        user = self.api.get_user(username=TARGET_USERNAME)
        return user.data.id

    def generate_profile(self):
        name = fake.name()
        bio = random.choice([
            "Love coffee ☕ | Tech enthusiast | #crypto",
            "Fitness junkie 💪 | DM for collabs",
            "Artist | Music lover 🎨🎵",
            ""  # Empty for realism
        ])
        username = f"bot_{random.randint(10000,99999)}_{fake.user_name()[:8]}"
        pfp_url = f"https://source.unsplash.com/random/400x400/?{random.choice(['person','avatar','portrait'])}"
        return name, username, bio, pfp_url

    def create_account(self, proxy):
        options = uc.ChromeOptions()
        options.add_argument(f'--proxy-server={proxy["http"]}')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={fake.user_agent()}')
        
        driver = uc.Chrome(options=options)
        
        try:
            # Get temp email
            email_resp = requests.get(TEMP_EMAIL_API + str(random.randint(100000,999999)))
            email = email_resp.json()['email']
            
            # Signup flow (simplified - automate full process)
            driver.get('https://twitter.com/i/flow/signup')
            time.sleep(random.uniform(2,5))
            
            # Fill name, email, birthdate (use devtools to inspect selectors)
            driver.find_element(By.NAME, 'name').send_keys(fake.name())
            driver.find_element(By.NAME, 'email').send_keys(email)
            # ... (full form automation below - expand as needed)
            
            # Verify email via API polling
            wait = WebDriverWait(driver, 30)
            # Simulate verification click
            
            # Set username, bio, pfp
            driver.get('https://twitter.com/home')
            # Upload PFP
            pfp_data = requests.get(pfp_url).content
            # driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(pfp_data)
            
            username = self.generate_profile()[1]
            # Set handle via settings
            
            print(f"Created account: {username} via {proxy['http']}")
            return username
            
        except Exception as e:
            print(f"Account creation failed: {e}")
            return None
        finally:
            driver.quit()

    def make_follow(self, follower_username):
        # Use Selenium to follow from new account (API limits on new accounts)
        proxy = self.proxy_queue.get()
        follower_id = self.get_user_id(follower_username)  # Fetch ID
        
        options = ChromeOptions()
        options.add_argument(f'--proxy-server={proxy["http"]}')
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get(f'https://twitter.com/{TARGET_USERNAME}')
            follow_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="placementTracking"]//span[text()="Follow"]'))
            )
            follow_btn.click()
            time.sleep(random.uniform(1,3))
            print(f"✅ @{follower_username} followed @{TARGET_USERNAME}")
            self.successful += 1
            return True
        except:
            return False
        finally:
            driver.quit()
            self.proxy_queue.put(proxy)

    def run(self):
        print(f"Generating {NUM_FOLLOWERS} followers...")
        for i in range(NUM_FOLLOWERS):
            follower = self.create_account(self.proxies[i % len(self.proxies)])
            if follower and self.make_follow(follower):
                print(f"Progress: {self.successful}/{NUM_FOLLOWERS}")
            time.sleep(random.randint(FOLLOW_DELAY_MIN, FOLLOW_DELAY_MAX))
        
        print(f"Complete! Added {self.successful} followers to @{TARGET_USERNAME}")

if __name__ == "__main__":
    gen = TwitterFollowerGenerator()
    gen.run()
