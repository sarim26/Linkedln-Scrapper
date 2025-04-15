from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import random
from datetime import datetime
import logging
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class LinkedInProfileFinder:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Initialize Edge WebDriver with optimal settings"""
        try:
            options = Options()
            # Basic preferences
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-infobars')
            options.add_argument('--inprivate')
            
            # Advanced anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--start-maximized')  # Start with maximized window
            
            # Make the browser look more realistic
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--enable-javascript')
            options.add_argument('--disable-blink-features')
            
            # Add common browser features
            options.add_argument('--lang=en-US,en;q=0.9')
            options.add_argument('--disable-web-security')
            options.add_argument('--ignore-certificate-errors')
            
            # Add a realistic user agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0')
            
            # Add common browser plugins
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
                "platform": "Windows"
            })
            
            # Additional anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            print(f"{Fore.GREEN}✅ Browser initialized successfully{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to initialize browser: {str(e)}{Style.RESET_ALL}")
            raise

    def random_delay(self, min_seconds=2, max_seconds=5):
        """Add a random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        # Add some micro-delays to simulate human behavior
        micro_delays = random.randint(1, 3)
        for _ in range(micro_delays):
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(delay)

    def simulate_human_behavior(self):
        """Simulate human-like scrolling and mouse movements"""
        try:
            # Random scroll
            scroll_amount = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Sometimes scroll back up a bit
            if random.random() > 0.7:
                self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)})")
                time.sleep(random.uniform(0.3, 0.7))
        except:
            pass  # Ignore if scrolling fails

    def search_profiles(self, keywords: str, num_profiles: int) -> list:
        """Search for LinkedIn profile URLs"""
        profile_urls = []
        page = 0
        search_query = f'site:linkedin.com/in/ {keywords}'
        
        print(f"\n{Fore.CYAN}🔍 Searching for LinkedIn profiles...{Style.RESET_ALL}")
        print(f"Keywords: {keywords}")
        print("=" * 50)

        try:
            while len(profile_urls) < num_profiles:
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&start={page * 10}"
                
                self.driver.get(search_url)
                time.sleep(2)  # Initial load wait
                
                # Simulate human behavior
                self.simulate_human_behavior()
                
                # Get all links on the page
                links = self.driver.find_elements(By.TAG_NAME, "a")
                found_on_page = False
                
                for link in links:
                    try:
                        # Add small random delays between link checks
                        if random.random() > 0.8:
                            time.sleep(random.uniform(0.1, 0.3))
                            
                        url = link.get_attribute("href")
                        # Only get actual LinkedIn profile URLs
                        if url and ("/in/" in url and ("linkedin.com" in url) and 
                                  not "google.com" in url and 
                                  not "accounts.google.com" in url and
                                  url not in profile_urls):
                            profile_urls.append(url)
                            found_on_page = True
                            print(f"{Fore.GREEN}✅ Found URL ({len(profile_urls)}/{num_profiles}): {Style.RESET_ALL}{url}")
                            
                            # Simulate human pause after finding a result
                            time.sleep(random.uniform(0.5, 1.0))
                            
                            if len(profile_urls) >= num_profiles:
                                break
                    except:
                        continue

                if not found_on_page:
                    print(f"{Fore.YELLOW}No new profiles found on page {page + 1}{Style.RESET_ALL}")
                    if page > 0:
                        break

                page += 1
                # Random delay between pages with more human-like variation
                self.random_delay(3, 7)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Search interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        finally:
            if profile_urls:
                print(f"\n{Fore.GREEN}Found {len(profile_urls)} LinkedIn profiles!{Style.RESET_ALL}")
            self.driver.quit()

        return profile_urls

    def save_results(self, urls: list, keywords: str):
        """Save URLs to CSV file"""
        if not urls:
            print(f"\n{Fore.RED}❌ No URLs found to save.{Style.RESET_ALL}")
            return

        try:
            # Create DataFrame with just URLs
            df = pd.DataFrame(urls, columns=['LinkedIn_URL'])
            
            # Save to CSV with simple name
            filename = f"linkedin_urls_{keywords.replace(' ', '_')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n{Fore.GREEN}✅ Saved {len(urls)} URLs to {filename}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error saving results: {str(e)}{Style.RESET_ALL}")

def main():
    try:
        print(f"{Fore.CYAN}🔎 LinkedIn URL Finder{Style.RESET_ALL}")
        print("=" * 50)
        
        # Get user input
        keywords = input("\nEnter search keywords: ").strip()
        num_profiles = int(input("How many URLs to find: "))

        if not keywords or num_profiles <= 0:
            print(f"{Fore.RED}⚠️ Please provide valid inputs!{Style.RESET_ALL}")
            return

        # Create finder and search for URLs
        finder = LinkedInProfileFinder()
        urls = finder.search_profiles(keywords, num_profiles)

        # Save results if any found
        if urls:
            finder.save_results(urls, keywords)

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️ Program cancelled by user{Style.RESET_ALL}")
    except ValueError:
        print(f"\n{Fore.RED}⚠️ Please enter a valid number{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ An error occurred: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
