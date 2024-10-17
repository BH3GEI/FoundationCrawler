import scrapy
from scrapy.exceptions import CloseSpider
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import logging
import json
import csv
import os
import argparse
import sys
import traceback
import pandas as pd
import requests
from urllib.parse import urlparse
import re

class FoundationSpider(scrapy.Spider):
    name = 'foundation'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置 Chrome 选项
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 硬件加速
        chrome_options.add_argument("--no-sandbox")  # 禁用沙箱
        chrome_options.add_argument("--disable-dev-shm-usage")  # 禁用 /dev/shm 
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = None  # 初始化为None，我后面在parse中创建
        
        self.max_retries = 5
        self.retry_delays = [2, 5, 10, 20, 30]  

        # 初始化有效URL计数器和错误URL计数器
        self.valid_url_count = 0
        self.error_url_count = 0

        # 从 CSV 文件中读取 URL
        self.urls_to_process = self.read_urls_from_csv()
        
        self.logger.info(f"Spider initialized with {len(self.urls_to_process)} URLs to process.")

        self.valid_urls_file = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/valid_urls.txt'
        self.error_urls_file = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/error_urls.txt'
        open(self.valid_urls_file, 'w').close()
        open(self.error_urls_file, 'w').close()

        self.url_json_dict = {}

        self.output_csv = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/url_json_data.csv'
        with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ['url', 'description', 'medium_original', 'medium_simplified']
            for i in range(1, 51):  # 为50次交易添加列
                headers.extend([f'transaction_{i}_date', f'transaction_{i}_action', f'transaction_{i}_price'])
            writer.writerow(headers)

    def read_urls_from_csv(self):
        csv_path = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/nft_information_data_example.csv'
        df = pd.read_csv(csv_path)
        return df.iloc[:, 0].tolist()

    def start_requests(self):
        for url in self.urls_to_process:
            self.record_url(url, is_valid=False)
            yield scrapy.Request(url=url, callback=self.parse, errback=self.errback_httpbin, 
                                 dont_filter=True, meta={'url': url, 'retry_count': 0})

    def log_and_print(self, message, level=logging.INFO):
        print(message, file=sys.stderr)
        self.logger.log(level, message)

    def wait_for_element(self, locator, timeout=30):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            self.log_and_print(f"Element not found: {locator}", level=logging.WARNING)
            return None

    def simulate_human_behavior(self):
        self.log_and_print(f"[URL: {self.driver.current_url}] Simulating human behavior...", level=logging.DEBUG)
        body = self.wait_for_element((By.TAG_NAME, "body"))
        if body:
            self.driver.execute_script(f"window.scrollTo(0, {random.randint(100, 1000)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        time.sleep(random.uniform(0.5, 1.5))

    def before_action(self):
        self.log_and_print(f"[URL: {self.driver.current_url}] Performing pre-action routine...", level=logging.DEBUG)
        self.wait_for_element((By.TAG_NAME, "body"), timeout=30)
        time.sleep(random.uniform(3, 5))  
        self.simulate_human_behavior()

    def parse(self, response):
        self.log_and_print(f"Parsing URL: {response.url}")
        retry_count = response.meta.get('retry_count', 0)
        original_url = response.meta.get('url', response.url)
        data = {}

        try:
            if self.driver is None:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")
                self.driver = webdriver.Chrome(options=chrome_options)

            self.log_and_print(f"[URL: {original_url}] [Attempt: {retry_count + 1}] Navigating to URL")
            self.driver.get(response.url)
            self.before_action()

            if "Page Not Found" in self.driver.title:
                raise Exception("Page Not Found")

            self.log_and_print(f"[URL: {original_url}] [Attempt: {retry_count + 1}] Extracting Description")
            try:
                self.log_and_print("Waiting for 'Read more' button...")
                read_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#__next > div:nth-child(4) > div > div.st--c-kRMSMx > div:nth-child(2) > div > div.st--c-dhzjXW > a"))
                )
                self.log_and_print("'Read more' button found. Clicking...")
                self.driver.execute_script("arguments[0].click();", read_more_button)
                self.log_and_print("'Read more' button clicked. Waiting for description...")
                
                description_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:r0\\: > div.st--c-htPtb > div.st--c-jCxxLK.st--c-jCxxLK-igHAool-css"))
                )
                
                full_description = self.driver.execute_script("""
                    var element = document.querySelector("#radix-\\\\:r0\\\\: > div.st--c-htPtb > div.st--c-jCxxLK.st--c-jCxxLK-igHAool-css");
                    return element ? element.innerText : '';
                """)
                
                self.log_and_print(f"Full description extracted: {full_description[:100]}...")  # 只打印前100个字符
                
                data['Description'] = full_description.strip()
            except Exception as e:
                self.log_and_print(f"Error extracting full description: {str(e)}", level=logging.ERROR)
                description_meta = response.xpath('//meta[@name="description"]/@content').get()
                data['Description'] = description_meta.strip() if description_meta else None

            self.log_and_print(f"[URL: {original_url}] [Attempt: {retry_count + 1}] Extracting Details")
            details = {}

            self.before_action()
            self.driver.get(response.url)

            try:
                print("Extracting Collection information...")
                # 提取 Collection 信息
                collection_link_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(1) > div:nth-child(2) > div > div > a"))
                )
                collection_url = collection_link_element.get_attribute('href')

                collection_name_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(1) > div:nth-child(2) > div > div > a > div > span"))
                )
                collection_name = collection_name_element.text.strip()

                details['Collection'] = f"{collection_name}[{collection_url}]"
            except:
                details['Collection'] = "N/A"

            try:
                # 提取 Owned by 信息
                username_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(2) > div:nth-child(2) > div > div > a > div > span"))
                )
                username = username_element.text.strip()

                link_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(2) > div:nth-child(2) > div > div > a"))
                )
                link = link_element.get_attribute('href')

                details['Owned by'] = f"{username}[{link}]"
            except:
                details['Owned by'] = "N/A"

            try:
                # 后面的代码结构类似，就不一一注释了
                blockchain_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(3) > div:nth-child(2) > div > span"))
                )
                details['Blockchain'] = blockchain_element.text.strip()
            except:
                details['Blockchain'] = "N/A"

            try:
                token_id_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(4) > div:nth-child(2)"))
                )
                details['Token ID'] = token_id_element.text.strip()
            except:
                details['Token ID'] = "N/A"

            try:
                contract_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'content-details')]//div[contains(text(), 'Contract')]/following-sibling::div//a"))
                )
                contract_text = contract_element.text.strip()
                contract_link = contract_element.get_attribute('href')

                contract_address = contract_link.split('/')[-1]

                details['Contract'] = f"{contract_text}[{contract_link}]"
            except Exception as e:
                self.logger.error(f"Error extracting Contract information: {str(e)}")
                details['Contract'] = "N/A"
                contract_address = "unknown"

            try:
                created_with_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(6) > div:nth-child(2) > div > span"))
                )
                details['Created with'] = created_with_element.text.strip()
            except:
                details['Created with'] = "N/A"


            try:
                token_standard_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(7) > div:nth-child(2)"))
                )
                details['Token standard'] = token_standard_element.text.strip()
            except:
                details['Token standard'] = "N/A"

            try:
                metadata_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(8) > div:nth-child(2) > a"))
                )
                metadata_text = metadata_element.text.strip()
                metadata_link = metadata_element.get_attribute('href')

                details['Metadata'] = f"{metadata_text}[{metadata_link}]"
            except:
                details['Metadata'] = "N/A"

            try:
                medium_text_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(9) > a > div"))
                )
                medium_text = medium_text_element.text.strip()

                medium_link_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-details > div > div:nth-child(9) > a"))
                )
                medium_link = medium_link_element.get_attribute('href')

                details['Medium'] = f"{medium_text}[{medium_link}]"
            except:
                details['Medium'] = "N/A"

            
            data['Details'] = details

            self.log_and_print(f"[URL: {original_url}] [Attempt: {retry_count + 1}] Extracting Activities")
            # 提取 Activities
            activities = []
            try:
                self.before_action()
                activity_tab = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-trigger-activity"))
                )

                activity_panel = self.driver.find_element(By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-activity")
                if activity_panel.get_attribute('data-state') != 'active':
                    activity_tab.click()
                    # 等待 Activity 面板变为激活状态
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "#radix-\\:Rejq8m\\:-content-activity[data-state='active']"))
                    )

                # 等一下，让页面加载完            
                time.sleep(5)

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.st--c-bqNLyO"))
                )
                
                activity_items = self.driver.find_elements(By.CSS_SELECTOR, "div.st--c-bqNLyO")
                
                for item in activity_items:
                    activity = {}
                    
                    # 提取行为名称
                    try:
                        action_element = item.find_element(By.CSS_SELECTOR, "div.st--c-jCxxLK.st--c-jCxxLK-hiuxaX-ellipsis-true > div")
                        activity['Action'] = action_element.text.strip()
                    except:
                        activity['Action'] = "N/A"
                    
                    # 提取用户信
                    try:
                        user_element = item.find_element(By.CSS_SELECTOR, "div.st--c-jCxxLK.st--c-jCxxLK-hiuxaX-ellipsis-true a.st--c-kBvNHc")
                        user_display_name = user_element.text.strip()
                        user_link = user_element.get_attribute('href')
                        user_name = user_link.split('/')[-1]
                        activity['User'] = f"{user_display_name}[@{user_name}]({user_link})"
                    except:
                        activity['User'] = "N/A"
                    
                    # 提取时间和链接
                    try:
                        time_element = item.find_element(By.CSS_SELECTOR, "a.st--c-jCxxLK.st--c-kBvNHc.st--c-jCxxLK-kGICcE-size-0.st--c-kBvNHc-cJzClO-variant-primary.st--c-jCxxLK-iUazGY-css")
                        date_text = time_element.text.strip()
                        date_link = time_element.get_attribute('href')
                        activity['Date'] = f"{date_text}[{date_link}]"
                    except:
                        activity['Date'] = "N/A"
                    
                    # 提取交易金额（如果有）
                    try:
                        amount_element = item.find_element(By.CSS_SELECTOR, "div.st--c-jCxxLK.st--c-jCxxLK-ieOKMTV-css")
                        activity['Amount'] = amount_element.text.strip()
                    except:
                        activity['Amount'] = "N/A"
                    
                    activities.append(activity)
                
                self.logger.info(f"Extracted {len(activities)} activities")
            except TimeoutException:
                self.logger.error("Timeout waiting for activities to load")
            except Exception as e:
                self.logger.error(f"Error extracting activities: {str(e)}")
            
            for activity in activities:
                if 'User' in activity and '@@' in activity['User']:
                    activity['User'] = activity['User'].replace('@@', '@')

            data['Activity'] = activities

            # 检查是否需要重试
            if self.should_retry(data):
                if retry_count < self.max_retries:
                    retry_count += 1
                    self.log_and_print(f"[URL: {original_url}] Incomplete data, retrying (Attempt {retry_count} of {self.max_retries})")
                    yield scrapy.Request(url=original_url, callback=self.parse, errback=self.errback_httpbin,
                                         dont_filter=True, meta={'retry_count': retry_count, 'url': original_url},
                                         priority=100)
                    return
                else:
                    self.log_and_print(f"[URL: {original_url}] Max retries reached, data still incomplete", level=logging.ERROR)

            self.log_and_print(f"[URL: {original_url}] Successfully parsed")
            self.log_and_print(f"[URL: {original_url}] Extracted data: {json.dumps(data, indent=2)}")

            # 保存数据到文件
            json_filename = self.save_data(data, response.url)

            if json_filename:
                self.update_url_status(original_url, is_valid=True)
                self.log_and_print(f"[URL: {original_url}] Successfully parsed and saved")
            else:
                raise Exception("Failed to save JSON data")

            yield data

        except Exception as e:
            self.log_and_print(f"[URL: {original_url}] [Attempt: {retry_count + 1}] Error: {str(e)}", level=logging.ERROR)
            if retry_count < self.max_retries and "Page Not Found" not in str(e):
                retry_count += 1
                self.log_and_print(f"[URL: {original_url}] Retrying (Attempt {retry_count} of {self.max_retries})")
                yield scrapy.Request(url=original_url, callback=self.parse, errback=self.errback_httpbin,
                                     dont_filter=True, meta={'retry_count': retry_count, 'url': original_url},
                                     priority=100)
            else:
                self.record_url(original_url, is_valid=False)
                self.log_and_print(f"[URL: {original_url}] Max retries reached or Page Not Found. Recorded as error URL.", level=logging.ERROR)
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def record_url(self, url, is_valid):
        file_path = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/error_urls.txt'
        
        try:
            with open(file_path, 'a') as f:
                f.write(f"{url}\n")
            
            self.log_and_print(f"URL recorded in error_urls.txt: {url}")
        except Exception as e:
            self.log_and_print(f"Error writing to {file_path}: {str(e)}", level=logging.ERROR)

    def update_url_status(self, url, is_valid):
        error_file = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/error_urls.txt'
        valid_file = '/mnt/r/users/yao/desktop/scrapy/foundation_app_scraper/valid_urls.txt'

        try:
            with open(error_file, 'r') as f:
                lines = f.readlines()
            with open(error_file, 'w') as f:
                for line in lines:
                    if line.strip() != url:
                        f.write(line)

            with open(valid_file, 'a') as f:
                f.write(f"{url}\n")

            self.valid_url_count += 1
            self.error_url_count -= 1
            
            self.log_and_print(f"URL status updated. Valid count: {self.valid_url_count}, Error count: {self.error_url_count}")
        except Exception as e:
            self.log_and_print(f"Error updating URL status: {str(e)}", level=logging.ERROR)

    def get_priced_transactions(self, activities):
        transactions = []
        for activity in activities:
            transaction = {
                'date': activity.get('Date', '').split('[')[0].strip(),
                'action': activity.get('Action', ''),
                'price': activity.get('Amount', 'N/A'),
                'user': ''
            }
            if 'User' in activity:
                user = activity['User'].split('[')[0].strip()
                transaction['user'] = f"{transaction['action']} by {user}"
            else:
                transaction['user'] = transaction['action']
            
            transactions.append(transaction)
        
        # 按日期排序，最早的在前
        transactions.sort(key=lambda x: x['date'])
        return transactions

    def save_data(self, data, url):
        url_parts = url.split('/')
        file_name_parts = url_parts[3:]  
        file_name = '_'.join(file_name_parts)
        
        json_filename = f'foundation_data_{file_name}.json'
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Data saved to {json_filename}")

            description = data.get('Description', '')
            
            medium_original = data.get('Details', {}).get('Medium', '')
            
            medium_simplified = medium_original.split('[')[0].strip()  # 移除 URL 部分
            medium_simplified = re.sub(r'\s*\([^)]*\)', '', medium_simplified)  # 移除括号及其内容

            all_transactions = self.get_priced_transactions(data.get('Activity', []))

            csv_row = [url, description, medium_original, medium_simplified]
            for transaction in all_transactions:
                csv_row.extend([
                    transaction['date'],
                    transaction['user'],
                    transaction['price']
                ])

            with open(self.output_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(csv_row)
            
            self.logger.info(f"Data appended to {self.output_csv}")
            return json_filename
        except Exception as e:
            self.logger.error(f"Error saving data for URL {url}: {str(e)}")
            return None

    def flatten_dict(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self.flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{sep}{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)

    def errback_httpbin(self, failure):
        self.logger.error(f"Error on {failure.request.url}: {str(failure.value)}")
        retry_count = failure.request.meta.get('retry_count', 0)
        original_url = failure.request.meta.get('url')
        if retry_count < self.max_retries:
            retry_count += 1
            self.logger.info(f"Retrying {original_url} (Attempt {retry_count} of {self.max_retries})")
            yield scrapy.Request(url=original_url, callback=self.parse, errback=self.errback_httpbin,
                                 dont_filter=True, meta={'retry_count': retry_count, 'url': original_url},
                                 priority=100)  
        else:
            self.record_url(original_url, is_valid=False)
            self.log_and_print(f"Max retries reached for {original_url}. Recorded as error URL.", level=logging.ERROR)

    def should_retry(self, data):
        if not data.get('Activity'):
            self.log_and_print(f"[URL: {self.driver.current_url}] Activity is empty, should retry")
            return True
        
        details = data.get('Details', {})
        for key, value in details.items():
            if not value or (isinstance(value, str) and value.strip() == ''):
                self.log_and_print(f"[URL: {self.driver.current_url}] Details field '{key}' is empty, should retry")
                return True
        
        return False

    def remove_duplicates(self, filename):
        if not os.path.exists(filename):
            self.logger.warning(f"File {filename} does not exist.")
            return

        with open(filename, 'r') as file:
            urls = set(file.read().splitlines())
        
        with open(filename, 'w') as file:
            for url in sorted(urls):
                file.write(f"{url}\n")

        self.logger.info(f"Removed duplicates from {filename}. Unique URLs: {len(urls)}")

    def close(self, reason):
        self.remove_duplicates(self.valid_urls_file)
        self.remove_duplicates(self.error_urls_file)
        super().close(reason)

if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    parser = argparse.ArgumentParser(description='Run the Foundation spider.')
    parser.add_argument('file', nargs='?', default='urls.txt', help='File containing URLs to scrape')
    args = parser.parse_args()

    file_path = os.path.abspath(args.file)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        exit(1)

    process = CrawlerProcess(get_project_settings())
    process.crawl(FoundationSpider, file=file_path)
    process.start()