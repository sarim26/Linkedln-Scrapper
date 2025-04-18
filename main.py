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
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                           QTextEdit, QSpinBox, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import sys
import os
import queue

# Initialize colorama for colored output
init()

# Create AllCSV directory if it doesn't exist
os.makedirs("AllCSV", exist_ok=True)

class SearchWorker(QThread):
    """Worker thread for running the search"""
    status_update = pyqtSignal(str, str)  # message, type
    search_complete = pyqtSignal()
    progress_update = pyqtSignal(int)

    def __init__(self, keywords, num_profiles):
        super().__init__()
        self.keywords = keywords
        self.num_profiles = num_profiles
        self.finder = LinkedInProfileFinder()
        self.finder.status_signal = self.status_update
        self.finder.progress_signal = self.progress_update

    def run(self):
        try:
            self.finder.setup_driver()
            urls = self.finder.search_profiles(self.keywords, self.num_profiles)
            if urls:
                self.finder.save_results(urls, self.keywords)
        except Exception as e:
            self.status_update.emit(f"Error: {str(e)}", "error")
        finally:
            self.search_complete.emit()

class LinkedInProfileFinder:
    def __init__(self):
        self.driver = None
        self.status_signal = None
        self.progress_signal = None

    def emit_status(self, message, msg_type="info"):
        if self.status_signal:
            self.status_signal.emit(message, msg_type)

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
            options.add_argument('--start-maximized')
            
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
            
            self.emit_status("Browser initialized successfully", "success")
            
        except Exception as e:
            self.emit_status(f"Failed to initialize browser: {str(e)}", "error")
            raise

    def random_delay(self, min_seconds=2, max_seconds=5):
        """Add a random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        micro_delays = random.randint(1, 3)
        for _ in range(micro_delays):
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(delay)

    def simulate_human_behavior(self):
        """Simulate human-like scrolling and mouse movements"""
        try:
            # Random scroll down
            scroll_amount = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Sometimes scroll back up a bit
            if random.random() > 0.7:
                self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
                time.sleep(random.uniform(0.3, 0.7))
                
            # Occasionally scroll to bottom and back
            if random.random() > 0.9:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.5, 1))
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)});")
                time.sleep(random.uniform(0.3, 0.7))
        except:
            pass

    def extract_name_from_url(self, url: str) -> str:
        """Extract name from LinkedIn URL"""
        try:
            # Get the part after /in/
            name_part = url.split('/in/')[1]
            
            # Remove any trailing parameters or slashes
            name_part = name_part.split('?')[0].split('/')[0]
            
            # Split by hyphens
            parts = name_part.split('-')
            
            # Filter out parts that look like random alphanumeric strings
            clean_parts = []
            for part in parts:
                # Skip if part is numeric
                if part.isdigit():
                    continue
                    
                # Skip if part looks like a random string (mix of letters and numbers)
                if (any(c.isdigit() for c in part) or 
                    len(part) > 15 or  # Skip very long parts
                    (any(not c.isalpha() for c in part) and len(part) > 5)):  # Skip parts with special chars
                    continue
                
                clean_parts.append(part)
            
            # If we have no valid parts, return default
            if not clean_parts:
                return url
            
            # Convert to title case and join
            name = ' '.join(part.title() for part in clean_parts)
            return name
        except:
            return url

    def search_profiles(self, keywords: str, num_profiles: int) -> list:
        """Search for LinkedIn profile URLs using Google"""
        profile_urls = []
        page = 0
        search_query = f'site:linkedin.com/in/ {keywords}'
        
        self.emit_status(f"Starting search with keywords: {keywords}")

        try:
            while len(profile_urls) < num_profiles:  # Main loop condition
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                if page > 0:
                    search_url += f"&start={page * 10}"
                
                self.driver.get(search_url)
                time.sleep(random.uniform(2, 4))
                
                # Add human-like behavior
                self.simulate_human_behavior()
                
                try:
                    # Wait for results to load and get all divs containing results
                    results = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.yuRUbf"))
                    )
                    
                    if not results:
                        break

                    for result in results:
                        # Break if we've found enough profiles
                        if len(profile_urls) >= num_profiles:
                            break
                            
                        try:
                            # Get all 'a' tags directly from the result div
                            links = result.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                # Break if we've found enough profiles
                                if len(profile_urls) >= num_profiles:
                                    break
                                    
                                url = link.get_attribute("href")
                                
                                if url and "/in/" in url and "linkedin.com" in url and url not in profile_urls:
                                    profile_urls.append(url)
                                    name = self.extract_name_from_url(url)
                                    self.emit_status(f"Found Profile ({len(profile_urls)}/{num_profiles}): {name}")
                                    
                                    if self.progress_signal:
                                        progress = int((len(profile_urls) / num_profiles) * 100)
                                        self.progress_signal.emit(progress)
                                    
                                    # Add small delay between profile processing
                                    time.sleep(random.uniform(0.5, 1))
                        except:
                            continue

                    # Break the outer loop if we've found enough profiles
                    if len(profile_urls) >= num_profiles:
                        break

                    # Only look for next page if we need more profiles
                    if len(profile_urls) < num_profiles:
                        try:
                            next_button = self.driver.find_element(By.ID, "pnnext")
                            if next_button:
                                # Scroll to next button with human-like behavior
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                                time.sleep(random.uniform(1, 2))
                                page += 1
                                time.sleep(random.uniform(2, 4))
                        except:
                            break

                except Exception as e:
                    self.emit_status(f"Error: {str(e)}", "error")
                    break

        except Exception as e:
            self.emit_status(f"Error: {str(e)}", "error")
        finally:
            # Ensure we don't return more profiles than requested
            profile_urls = profile_urls[:num_profiles]
            
            if profile_urls:
                self.emit_status(f"Found {len(profile_urls)} LinkedIn profiles!")
            else:
                self.emit_status("No LinkedIn profiles found.")
            self.driver.quit()

        return profile_urls

    def save_results(self, urls: list, keywords: str):
        """Save URLs and extracted names to CSV"""
        if not urls:
            self.emit_status("No URLs found to save.", "error")
            return

        try:
            # Create list of dictionaries with URL and Name
            data = []
            for url in urls:
                name = self.extract_name_from_url(url)
                data.append({
                    'Name': name,
                    'LinkedIn_URL': url
                })

            # Create DataFrame with URLs and Names
            df = pd.DataFrame(data)
            
            # Save to CSV
            filename = os.path.join("AllCSV", f"linkedin_urls_{keywords.replace(' ', '_')}.csv")
            df.to_csv(filename, index=False)
            self.emit_status(f"Saved {len(urls)} profiles with names to {filename}", "success")
            
        except Exception as e:
            self.emit_status(f"Error saving results: {str(e)}", "error")

class LinkedInFinderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Profile Finder")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #1a1a1a;
                font-size: 14px;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                font-size: 14px;
                color: black;
            }
            QPushButton {
                background-color: #0a66c2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #004182;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background: white;
                font-size: 13px;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0a66c2;
            }
        """)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("LinkedIn Profile Finder")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0a66c2; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Input section
        input_layout = QVBoxLayout()
        
        # Keywords input
        keywords_layout = QVBoxLayout()
        keywords_label = QLabel("Search Keywords:")
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("Enter search keywords (e.g., HDFC Marketing Sales)")
        keywords_layout.addWidget(keywords_label)
        keywords_layout.addWidget(self.keywords_input)
        input_layout.addLayout(keywords_layout)

        # Number of profiles input
        profiles_layout = QVBoxLayout()
        profiles_label = QLabel("Number of Profiles:")
        self.profiles_input = QSpinBox()
        self.profiles_input.setRange(1, 1000)
        self.profiles_input.setValue(10)
        profiles_layout.addWidget(profiles_label)
        profiles_layout.addWidget(self.profiles_input)
        input_layout.addLayout(profiles_layout)

        layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Search button
        self.search_button = QPushButton("Start Search")
        self.search_button.clicked.connect(self.start_search)
        layout.addWidget(self.search_button)

        # Status text area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.worker = None

    def update_status(self, message, msg_type="info"):
        color = {
            "error": "#dc3545",
            "success": "#28a745",
            "warning": "#ffc107",
            "info": "#0a66c2"
        }.get(msg_type, "black")
        
        self.status_text.append(f'<span style="color: {color};">{message}</span>')
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def search_complete(self):
        self.search_button.setEnabled(True)
        self.progress_bar.setValue(100)

    def start_search(self):
        keywords = self.keywords_input.text().strip()
        num_profiles = self.profiles_input.value()

        if not keywords:
            QMessageBox.warning(self, "Error", "Please enter search keywords")
            return

        self.search_button.setEnabled(False)
        self.status_text.clear()
        self.progress_bar.setValue(0)

        self.worker = SearchWorker(keywords, num_profiles)
        self.worker.status_update.connect(self.update_status)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.search_complete.connect(self.search_complete)
        self.worker.start()

def main():
    app = QApplication(sys.argv)
    window = LinkedInFinderGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
