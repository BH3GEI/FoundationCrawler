# Scrapy settings for foundation_app_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "foundation_app_scraper"

SPIDER_MODULES = ["foundation_app_scraper.spiders"]
NEWSPIDER_MODULE = "foundation_app_scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
LOG_LEVEL = 'INFO'

# Configure logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "foundation_app_scraper.pipelines.FoundationAppScraperPipeline": 300,
#}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Add a delay between requests
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = False
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 60 * 60 * 24  # 1 day

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
LOG_LEVEL = 'INFO'

DOWNLOAD_TIMEOUT = 180
RETRY_ENABLED = True
RETRY_TIMES = 3
HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day

