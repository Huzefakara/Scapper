import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playwright.sync_api import sync_playwright
import time
import threading
from urllib.parse import urlparse
import re
from datetime import datetime
import traceback
import sys
import os
import json
import random
import logging

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Comparison")
        self.root.geometry("1200x800")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        ttk.Label(main_frame, text="Enter URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(main_frame, width=100)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Scrape button
        self.scrape_button = ttk.Button(main_frame, text="Scrape", command=self.start_scraping)
        self.scrape_button.grid(row=0, column=2, padx=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create text view tab
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="Text View")
        
        # Create table view tab
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="Table View")
        
        # Results text area in text view tab
        self.results_text = scrolledtext.ScrolledText(self.text_frame, width=120, height=40)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Table view components
        self.tree = ttk.Treeview(self.table_frame, columns=("Method", "Product Name", "Original Price", "Current Price", "Discount"), show="headings")
        self.tree.heading("Method", text="Method")
        self.tree.heading("Product Name", text="Product Name")
        self.tree.heading("Original Price", text="Original Price")
        self.tree.heading("Current Price", text="Current Price")
        self.tree.heading("Discount", text="Discount")
        
        # Set column widths
        self.tree.column("Method", width=100)
        self.tree.column("Product Name", width=300)
        self.tree.column("Original Price", width=150)
        self.tree.column("Current Price", width=150)
        self.tree.column("Discount", width=100)
        
        # Add scrollbar to table
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid table and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=600, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Performance metrics
        self.performance_metrics = {}
        
        # Check dependencies
        self.check_dependencies()
        
        # Initialize user agents list
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
        # Initialize request headers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)
        
    def check_dependencies(self):
        """Check if all required dependencies are properly installed"""
        try:
            # Check BeautifulSoup
            soup = BeautifulSoup("<html></html>", 'html.parser')
            self.log_message("BeautifulSoup: OK")
        except Exception as e:
            self.log_message(f"BeautifulSoup Error: {str(e)}")
            
        try:
            # Check Selenium
            options = Options()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            driver.quit()
            self.log_message("Selenium: OK")
        except Exception as e:
            self.log_message(f"Selenium Error: {str(e)}")
            
        try:
            # Check Playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            self.log_message("Playwright: OK")
        except Exception as e:
            self.log_message(f"Playwright Error: {str(e)}")
            if "Executable doesn't exist" in str(e):
                if messagebox.askyesno("Install Playwright Browsers", 
                    "Playwright browsers are not installed. Would you like to install them now?"):
                    try:
                        import subprocess
                        subprocess.run([sys.executable, "-m", "playwright", "install"], 
                            check=True, capture_output=True)
                        self.log_message("Playwright browsers installed successfully!")
                    except Exception as install_error:
                        self.log_message(f"Failed to install Playwright browsers: {str(install_error)}")
                        
    def log_message(self, message):
        """Add a message to the results text area"""
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)
        
    def start_scraping(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log_message("Please enter a valid URL")
            return
            
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            self.log_message(f"Invalid URL: {str(e)}")
            return
            
        self.scrape_button.config(state='disabled')
        self.results_text.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.performance_metrics = {}
        
        # Start scraping in a separate thread
        threading.Thread(target=self.scrape_all_methods, args=(url,), daemon=True).start()
        
    def update_table(self, method, result):
        """Update the table with new results"""
        name = result.get('name', 'Not found')
        current_price = result.get('current_price', 'Not found')
        original_price = result.get('original_price', 'Not found')
        discount = f"{result.get('discount_percent', '')}%" if result.get('discount_percent') else 'N/A'
        
        # Insert new row
        self.tree.insert("", "end", values=(method, name, original_price, current_price, discount))

    def clear_table(self):
        """Clear all items from the table"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def scrape_all_methods(self, url):
        try:
            start_time = datetime.now()
            self.clear_table()  # Clear table before new scrape
            
            # BeautifulSoup
            self.log_message("\n=== BeautifulSoup Results ===")
            bs_start = datetime.now()
            try:
                bs_result = self.scrape_with_bs(url)
                bs_time = (datetime.now() - bs_start).total_seconds()
                self.performance_metrics['BeautifulSoup'] = bs_time
                self.log_message(self.format_price_output(bs_result))
                self.log_message(f"Time taken: {bs_time:.2f} seconds")
                self.update_table("BeautifulSoup", bs_result)
            except Exception as e:
                self.log_message(f"BeautifulSoup Error: {str(e)}")
            self.progress['value'] = 25
            
            # Selenium
            self.log_message("\n=== Selenium Results ===")
            selenium_start = datetime.now()
            try:
                selenium_result = self.scrape_with_selenium(url)
                selenium_time = (datetime.now() - selenium_start).total_seconds()
                self.performance_metrics['Selenium'] = selenium_time
                self.log_message(self.format_price_output(selenium_result))
                self.log_message(f"Time taken: {selenium_time:.2f} seconds")
                self.update_table("Selenium", selenium_result)
            except Exception as e:
                self.log_message(f"Selenium Error: {str(e)}")
            self.progress['value'] = 50
            
            # Playwright
            self.log_message("\n=== Playwright Results ===")
            playwright_start = datetime.now()
            try:
                playwright_result = self.scrape_with_playwright(url)
                playwright_time = (datetime.now() - playwright_start).total_seconds()
                self.performance_metrics['Playwright'] = playwright_time
                self.log_message(self.format_price_output(playwright_result))
                self.log_message(f"Time taken: {playwright_time:.2f} seconds")
                self.update_table("Playwright", playwright_result)
            except Exception as e:
                self.log_message(f"Playwright Error: {str(e)}")
            self.progress['value'] = 75
            
            # Performance Summary
            self.log_message("\n=== Performance Summary ===")
            for method, time_taken in self.performance_metrics.items():
                self.log_message(f"{method}: {time_taken:.2f} seconds")
            
            total_time = (datetime.now() - start_time).total_seconds()
            self.log_message(f"\nTotal time taken: {total_time:.2f} seconds")
            self.progress['value'] = 100
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.log_message("Please check if the URL is valid and accessible.")
        finally:
            self.scrape_button.config(state='normal')
            
    def clean_price(self, price_text):
        """Clean and validate price text"""
        if not price_text:
            return None
            
        try:
            # Remove common currency symbols and text
            price_text = price_text.replace('$', '').replace('USD', '').replace('£', '')
            price_text = price_text.replace('€', '').replace('CAD', '').replace('AUD', '')
            
            # Remove any non-numeric characters except . and ,
            price_text = re.sub(r'[^\d.,]', '', price_text)
            
            # Handle different decimal separators
            if ',' in price_text and '.' in price_text:
                # If both exist, assume comma is thousand separator
                price_text = price_text.replace(',', '')
            elif ',' in price_text:
                # If only comma exists, assume it's decimal separator
                price_text = price_text.replace(',', '.')
                
            # Extract the first valid price if multiple exist
            price_matches = re.findall(r'\d+\.?\d*', price_text)
            if price_matches:
                price = float(price_matches[0])
                if 0 < price < 1000000:  # Basic sanity check
                    return price
            return None
            
        except ValueError:
            return None
            
    def extract_price(self, soup, selectors):
        """Extract price using multiple methods"""
        # Method 1: Try direct price selectors
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Skip if element contains words indicating non-current price
                text = element.get_text().lower()
                if any(word in text for word in ['was', 'old', 'msrp', 'regular', 'retail', 'list']):
                    continue
                    
                price = self.clean_price(text)
                if price:
                    return price
                    
        # Method 2: Try JSON-LD data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for price in various JSON-LD structures
                    if 'offers' in data:
                        if isinstance(data['offers'], dict):
                            price = self.clean_price(str(data['offers'].get('price')))
                            if price:
                                return price
                        elif isinstance(data['offers'], list):
                            for offer in data['offers']:
                                price = self.clean_price(str(offer.get('price')))
                                if price:
                                    return price
            except:
                continue
                
        # Method 3: Try meta tags
        meta_selectors = [
            'meta[property="product:price:amount"]',
            'meta[property="og:price:amount"]',
            'meta[name="price"]',
            'meta[itemprop="price"]'
        ]
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                price = self.clean_price(element['content'])
                if price:
                    return price
                    
        return None
        
    def get_random_user_agent(self):
        """Get a random user agent from the list"""
        return random.choice(self.user_agents)
        
    def get_headers(self, url):
        """Get headers with random user agent and proper referer"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = self.get_random_user_agent()
        # Add referer from major search engines
        referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://www.yahoo.com/',
            'https://duckduckgo.com/'
        ]
        headers['Referer'] = random.choice(referers)
        return headers
        
    def add_stealth_selenium_options(self, options):
        """Add stealth options to Selenium"""
        # Existing options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Additional stealth options
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        
        # Random window size
        window_sizes = ['1920,1080', '1366,768', '1536,864', '1440,900', '1280,720']
        options.add_argument(f'--window-size={random.choice(window_sizes)}')
        
        # Add random user agent
        options.add_argument(f'--user-agent={self.get_random_user_agent()}')
        
        # Disable automation flags
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        return options
        
    def configure_playwright_stealth(self, page):
        """Configure Playwright for stealth"""
        # Set random viewport size
        viewport_sizes = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)]
        viewport = random.choice(viewport_sizes)
        page.set_viewport_size({'width': viewport[0], 'height': viewport[1]})
        
        # Set headers including random user agent
        headers = self.get_headers(page.url)
        page.set_extra_http_headers(headers)
        
        # Add JavaScript code to mask automation
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)
        
        return page
        
    def format_price_output(self, result):
        """Format the price output string based on available price information"""
        name = result.get('name', 'Not found')
        current_price = result.get('current_price', 'Not found')
        original_price = result.get('original_price', None)
        discount_percent = result.get('discount_percent', None)
        
        output = [f"Product Name: {name}"]
        
        if original_price and current_price != 'Not found':
            output.append(f"Original Price: {original_price}")
            output.append(f"Current Price: {current_price}")
            if discount_percent:
                output.append(f"Discount: {discount_percent}%")
        else:
            output.append(f"Price: {current_price}")
            
        return "\n".join(output)

    def calculate_discount_percent(self, original, current):
        """Calculate discount percentage"""
        try:
            original = float(str(original).replace('$', '').replace(',', ''))
            current = float(str(current).replace('$', '').replace(',', ''))
            if original > current:
                discount = ((original - current) / original) * 100
                return round(discount, 2)
        except:
            pass
        return None

    def extract_prices(self, soup, price_selectors, was_price_selectors):
        """Extract both current and original prices"""
        current_price = None
        original_price = None
        
        # Try to find current price
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                if not any(word in text for word in ['was', 'old', 'msrp', 'regular', 'retail', 'list']):
                    price = self.clean_price(text)
                    if price:
                        current_price = price
                        break
            if current_price:
                break
                
        # Try to find original price
        for selector in was_price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                if any(word in text for word in ['was', 'old', 'msrp', 'regular', 'retail', 'list']):
                    price = self.clean_price(text)
                    if price and (not current_price or price > current_price):
                        original_price = price
                        break
            if original_price:
                break
                
        return current_price, original_price

    def scrape_with_bs(self, url):
        try:
            headers = self.get_headers(url)
            time.sleep(random.uniform(1, 3))
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Current price selectors
            price_selectors = [
                "[class*='price']:not([class*='was']):not([class*='old']):not([class*='regular'])",
                "[class*='Price']:not([class*='Was']):not([class*='Old']):not([class*='Regular'])",
                "[class*='current-price']",
                "[class*='sale-price']",
                "[class*='special-price']",
                "[class*='offer-price']",
                "[class*='price-value']",
                "[class*='price__current']",
                "[class*='price--sale']",
                "[data-price]",
                "[data-product-price]",
                "[itemprop='price']"
            ]
            
            # Original price selectors
            was_price_selectors = [
                "[class*='was-price']",
                "[class*='old-price']",
                "[class*='regular-price']",
                "[class*='list-price']",
                "[class*='compare-price']",
                "[class*='original-price']",
                "[class*='price--compare']",
                "[class*='price__regular']",
                "[class*='price__was']",
                "[data-regular-price]",
                "[data-compare-price]"
            ]
            
            # Extract prices
            current_price, original_price = self.extract_prices(soup, price_selectors, was_price_selectors)
            
            # Extract name (existing code)
            name_selectors = [
                "[class*='product-title']",
                "[class*='product-name']",
                "h1",
                "[class*='title']",
                "[class*='name']",
                "[itemprop='name']"
            ]
            
            name = None
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text().strip()
                    break
                    
            # Calculate discount if both prices are available
            discount_percent = None
            if original_price and current_price:
                discount_percent = self.calculate_discount_percent(original_price, current_price)
                
            return {
                'name': name or 'Not found',
                'current_price': f"${current_price:.2f}" if current_price else 'Not found',
                'original_price': f"${original_price:.2f}" if original_price else None,
                'discount_percent': discount_percent
            }
            
        except Exception as e:
            self.log_message(f"BeautifulSoup Error: {str(e)}")
            return {'name': 'Error', 'current_price': f'Scraping failed: {str(e)}'}
            
    def extract_prices_selenium(self, driver):
        """Extract original and discounted prices using Selenium"""
        # Original price selectors
        original_price_selectors = [
            "//*[contains(@class, 'price--old')]",
            "//*[contains(@class, 'price--regular')]",
            "//*[contains(@class, 'price--compare')]",
            "//*[contains(@class, 'price--was')]",
            # Specific website selectors
            "//*[@class='price text-dark-gray text-xl font-sans font-light line-through']"
        ]

        # Discounted price selectors
        discounted_price_selectors = [
            "//*[contains(@class, 'price--current')]",
            "//*[contains(@class, 'price--sale')]",
            "//*[contains(@class, 'price--special')]",
            "//*[contains(@class, 'price--discounted')]",
            # Specific website selectors
            "//*[@class='price text-darkpink-900 text-22 font-semibold font-sans leading-9 lg:text-4xl']"
        ]

        original_price = None
        discounted_price = None

        # Extract original price
        for selector in original_price_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                original_price = self.clean_price(element.text)
                break
            except:
                continue

        # Extract discounted price
        for selector in discounted_price_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                discounted_price = self.clean_price(element.text)
                break
            except:
                continue

        return original_price, discounted_price

    def scrape_with_selenium(self, url):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options = self.add_stealth_selenium_options(chrome_options)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            time.sleep(random.uniform(2, 5))
            driver.get(url)
            
            # Add random scrolling
            for _ in range(random.randint(3, 7)):
                driver.execute_script(f"window.scrollTo(0, {random.randint(100, 1000)});")
                time.sleep(random.uniform(0.5, 1.5))
                
            # Try the new price extraction method first
            original_price, current_price = self.extract_prices_selenium(driver)
            
            # If prices not found, fall back to the original selectors
            if not current_price:
                # Current price selectors
                price_selectors = [
                    "//*[contains(@class, 'price') and not(contains(@class, 'was')) and not(contains(@class, 'old'))]",
                    "//*[contains(@class, 'current-price')]",
                    "//*[contains(@class, 'sale-price')]",
                    "//*[contains(@class, 'special-price')]",
                    "//*[@data-price]",
                    "//*[@itemprop='price']"
                ]
                
                # Original price selectors
                was_price_selectors = [
                    "//*[contains(@class, 'was-price')]",
                    "//*[contains(@class, 'old-price')]",
                    "//*[contains(@class, 'regular-price')]",
                    "//*[contains(@class, 'compare-price')]",
                    "//*[@data-regular-price]",
                    "//*[@data-compare-price]"
                ]
                
                # Find current price
                for selector in price_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and not any(word in text.lower() for word in ['was', 'old', 'msrp', 'regular']):
                                price = self.clean_price(text)
                                if price:
                                    current_price = price
                                    break
                        if current_price:
                            break
                    except:
                        continue
                        
                # Find original price if not found yet
                if not original_price:
                    for selector in was_price_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                text = element.text.strip()
                                if text and any(word in text.lower() for word in ['was', 'old', 'msrp', 'regular']):
                                    price = self.clean_price(text)
                                    if price and (not current_price or price > current_price):
                                        original_price = price
                                        break
                            if original_price:
                                break
                        except:
                            continue
                    
            # Extract name
            name_selectors = [
                "//*[contains(@class, 'product-title')]",
                "//*[contains(@class, 'product-name')]",
                "//h1",
                "//*[contains(@class, 'title')]",
                "//*[contains(@class, 'name')]",
                "//*[@itemprop='name']"
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    name = element.text.strip()
                    break
                except:
                    continue
                    
            # Calculate discount if both prices are available
            discount_percent = None
            if original_price and current_price:
                discount_percent = self.calculate_discount_percent(original_price, current_price)
                
            return {
                'name': name or 'Not found',
                'current_price': f"${current_price:.2f}" if current_price else 'Not found',
                'original_price': f"${original_price:.2f}" if original_price else None,
                'discount_percent': discount_percent
            }
            
        except Exception as e:
            self.log_message(f"Selenium Error: {str(e)}")
            return {'name': 'Error', 'current_price': f'Scraping failed: {str(e)}'}
        finally:
            if 'driver' in locals():
                driver.quit()
                
    def extract_prices_playwright(self, page):
        """Extract original and discounted prices using Playwright"""
        # Original price selectors
        original_price_selectors = [
            ".price--old", ".price--regular", ".price--compare", ".price--was",
            # Specific website selectors
            ".price.text-dark-gray.text-xl.font-sans.font-light.line-through"
        ]

        # Discounted price selectors
        discounted_price_selectors = [
            ".price--current", ".price--sale", ".price--special", ".price--discounted",
            # Specific website selectors
            ".price.text-darkpink-900.text-22.font-semibold.font-sans.leading-9.lg\\:text-4xl"
        ]

        original_price = None
        discounted_price = None

        # Extract original price
        for selector in original_price_selectors:
            element = page.query_selector(selector)
            if element:
                original_price = self.clean_price(element.text_content())
                break

        # Extract discounted price
        for selector in discounted_price_selectors:
            element = page.query_selector(selector)
            if element:
                discounted_price = self.clean_price(element.text_content())
                break

        return original_price, discounted_price

    def scrape_with_playwright(self, url):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.get_random_user_agent(),
                    java_script_enabled=True,
                    ignore_https_errors=True
                )
                
                page = context.new_page()
                page = self.configure_playwright_stealth(page)
                
                time.sleep(random.uniform(1, 3))
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Add random scrolling
                for _ in range(random.randint(3, 7)):
                    page.evaluate(f"window.scrollTo(0, {random.randint(100, 1000)})")
                    time.sleep(random.uniform(0.5, 1.5))
                    
                # Try the new price extraction method first
                original_price, current_price = self.extract_prices_playwright(page)
                
                # If prices not found, fall back to the original selectors
                if not current_price:
                    # Current price selectors
                    price_selectors = [
                        "[class*='price']:not([class*='was']):not([class*='old']):not([class*='regular'])",
                        "[class*='current-price']",
                        "[class*='sale-price']",
                        "[class*='special-price']",
                        "[data-price]",
                        "[itemprop='price']"
                    ]
                    
                    # Original price selectors
                    was_price_selectors = [
                        "[class*='was-price']",
                        "[class*='old-price']",
                        "[class*='regular-price']",
                        "[class*='compare-price']",
                        "[data-regular-price]",
                        "[data-compare-price]"
                    ]
                    
                    # Find current price
                    for selector in price_selectors:
                        elements = page.query_selector_all(selector)
                        for element in elements:
                            text = element.text_content().strip()
                            if text and not any(word in text.lower() for word in ['was', 'old', 'msrp', 'regular']):
                                price = self.clean_price(text)
                                if price:
                                    current_price = price
                                    break
                        if current_price:
                            break
                            
                    # Find original price if not found yet
                    if not original_price:
                        for selector in was_price_selectors:
                            elements = page.query_selector_all(selector)
                            for element in elements:
                                text = element.text_content().strip()
                                if text and any(word in text.lower() for word in ['was', 'old', 'msrp', 'regular']):
                                    price = self.clean_price(text)
                                    if price and (not current_price or price > current_price):
                                        original_price = price
                                        break
                            if original_price:
                                break
                        
                # Try JSON-LD data for prices if still not found
                if not current_price or not original_price:
                    scripts = page.query_selector_all('script[type="application/ld+json"]')
                    for script in scripts:
                        try:
                            data = json.loads(script.text_content())
                            if isinstance(data, dict):
                                if 'offers' in data:
                                    if isinstance(data['offers'], dict):
                                        if not current_price:
                                            current_price = self.clean_price(str(data['offers'].get('price')))
                                        if not original_price and 'priceSpecification' in data['offers']:
                                            original_price = self.clean_price(
                                                str(data['offers']['priceSpecification'].get('price')))
                        except:
                            continue
                            
                # Extract name
                name_selectors = [
                    "[class*='product-title']",
                    "[class*='product-name']",
                    "h1",
                    "[class*='title']",
                    "[class*='name']",
                    "[itemprop='name']"
                ]
                
                name = None
                for selector in name_selectors:
                    element = page.query_selector(selector)
                    if element:
                        name = element.text_content().strip()
                        break
                        
                # Calculate discount if both prices are available
                discount_percent = None
                if original_price and current_price:
                    discount_percent = self.calculate_discount_percent(original_price, current_price)
                    
                browser.close()
                return {
                    'name': name or 'Not found',
                    'current_price': f"${current_price:.2f}" if current_price else 'Not found',
                    'original_price': f"${original_price:.2f}" if original_price else None,
                    'discount_percent': discount_percent
                }
                
        except Exception as e:
            self.log_message(f"Playwright Error: {str(e)}")
            return {'name': 'Error', 'current_price': f'Scraping failed: {str(e)}'}

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop() 