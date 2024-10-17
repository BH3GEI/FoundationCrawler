import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv
import sys
import logging

class NFTScanSpider(scrapy.Spider):
    name = 'nftscan_spider'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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

        self.valid_url_count = 0
        self.error_url_count = 0

        self.urls_to_process = self.read_urls_from_csv()
        
        self.logger.info(f"Spider initialized with {len(self.urls_to_process)} URLs to process.")

        self.valid_urls_file = 'valid_urls.txt'
        self.error_urls_file = 'error_urls.txt'
        open(self.valid_urls_file, 'w').close()
        open(self.error_urls_file, 'w').close()

        self.url_json_dict = {}

        # 初始化CSV文件
        self.output_csv = 'nftscan_data.csv'
        with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ['url', 'description', 'medium_original', 'medium_simplified']
            for i in range(1, 51):  # 为50次交易添加列
                headers.extend([f'transaction_{i}_date', f'transaction_{i}_action', f'transaction_{i}_price', 
                                f'transaction_{i}_gas', f'transaction_{i}_from', f'transaction_{i}_to'])
            writer.writerow(headers)

    def read_urls_from_csv(self):
        csv_path = 'nftscan_links.csv'
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行
            return [row[0] for row in reader]

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
                self.driver = webdriver.Chrome(options=chrome_options)

            self.driver.get(response.url)
            self.before_action()

            # 提取Description
            description_selector = "#scroll-detail-content > div.scrollContent___Rwat- > div > div.cardRow___2pZG5 > div:nth-child(2) > div.qkCard___xu6o-.card___1qnmA.official___3aNrA.common-card > div:nth-child(2) > div.officialContent___3hHGb.active___2DPTX > div.listItem___3eSbn.block___1VdlR > div.value___1X20z"
            description_element = self.wait_for_element((By.CSS_SELECTOR, description_selector))
            description = description_element.text if description_element else "N/A"

            # 提取Format (用于medium_simplified)
            format_selector = "#scroll-detail-content > div.scrollContent___Rwat- > div > div.cardRow___2pZG5 > div:nth-child(2) > div.basicCard___1d8gC.common-card > div.cardContent___3gJcz > div:nth-child(12) > div.value___1X20z"
            format_element = self.wait_for_element((By.CSS_SELECTOR, format_selector))
            medium_simplified = format_element.text if format_element else "N/A"

            # 提取交易记录
            transactions = []
            transaction_table_selector = "#scroll-detail-content > div.scrollContent___Rwat- > div > div.contentContainer___LCaV6.common-card > div.searchContent___2XlXL > div > div > div"
            transaction_table = self.wait_for_element((By.CSS_SELECTOR, transaction_table_selector))
            if transaction_table:
                rows = transaction_table.find_elements(By.TAG_NAME, "tr")[1:]  # 跳过表头
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 6:
                        action_date = cells[0].text.split('\n')
                        action = action_date[0] if action_date else ''
                        date = action_date[1] if len(action_date) > 1 else ''
                        price = cells[2].text if len(cells) > 2 else ''
                        gas = cells[4].text if len(cells) > 4 else ''
                        transfer_info = cells[5].find_elements(By.TAG_NAME, "a")
                        from_address = self.format_address(transfer_info[0]) if len(transfer_info) > 0 else ''
                        to_address = self.format_address(transfer_info[1]) if len(transfer_info) > 1 else ''
                        transactions.append((date, action, price, gas, from_address, to_address))

            # 对交易记录进行排序，按照日期从早到晚
            transactions.sort(key=lambda x: x[0] if x[0] else '', reverse=True)

            # 构建数据字典
            data = {
                'url': original_url,
                'description': description,
                'medium_original': '',  # 留空
                'medium_simplified': medium_simplified,
            }

            # 添加交易记录
            for i, (date, action, price, gas, from_address, to_address) in enumerate(transactions[:50], 1):
                data[f'transaction_{i}_date'] = date
                data[f'transaction_{i}_action'] = action
                data[f'transaction_{i}_price'] = price
                data[f'transaction_{i}_gas'] = gas
                data[f'transaction_{i}_from'] = from_address
                data[f'transaction_{i}_to'] = to_address

            # 写入CSV文件
            with open(self.output_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                row = [data.get(key, '') for key in self.get_csv_headers()]
                writer.writerow(row)

            self.record_url(original_url, is_valid=True)
            self.valid_url_count += 1

        except Exception as e:
            self.log_and_print(f"Error processing {original_url}: {str(e)}", level=logging.ERROR)
            if retry_count < self.max_retries:
                retry_count += 1
                self.log_and_print(f"Retrying {original_url} (attempt {retry_count}/{self.max_retries})")
                yield scrapy.Request(url=original_url, callback=self.parse, errback=self.errback_httpbin,
                                     dont_filter=True, meta={'url': original_url, 'retry_count': retry_count})
            else:
                self.log_and_print(f"Max retries reached for {original_url}. Skipping.")
                self.error_url_count += 1

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def get_csv_headers(self):
        headers = ['url', 'description', 'medium_original', 'medium_simplified']
        for i in range(1, 51):
            headers.extend([f'transaction_{i}_date', f'transaction_{i}_action', f'transaction_{i}_price', 
                            f'transaction_{i}_gas', f'transaction_{i}_from', f'transaction_{i}_to'])
        return headers

    def record_url(self, url, is_valid):
        file_path = self.valid_urls_file if is_valid else self.error_urls_file
        with open(file_path, 'a') as f:
            f.write(url + '\n')

    def errback_httpbin(self, failure):
        url = failure.request.meta['url']
        self.log_and_print(f"Error on {url}: {str(failure.value)}", level=logging.ERROR)
        self.error_url_count += 1

    def closed(self, reason):
        self.log_and_print(f"Spider closed: {reason}")
        self.log_and_print(f"Total URLs processed: {self.valid_url_count + self.error_url_count}")
        self.log_and_print(f"Valid URLs: {self.valid_url_count}")
        self.log_and_print(f"Error URLs: {self.error_url_count}")

    def format_address(self, element):
        if element:
            full_address = element.get_attribute('href').split('/')[-1]
            short_address = element.text
            return f"{short_address}[https://eth.nftscan.com/{full_address}]"
        return ''
