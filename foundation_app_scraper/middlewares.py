from scrapy import signals
from itemadapter import is_item, ItemAdapter

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

class FoundationAppScraperSpiderMiddleware:
    # Scrapy用来创建爬虫的方法
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # 这里处理进入爬虫的每个响应
        return None

    def process_spider_output(self, response, result, spider):
        # 处理爬虫返回的结果
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # 处理异常情况，先放着
        pass

    def process_start_requests(self, start_requests, spider):
        # 处理爬虫的起始请求
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("爬虫开工啦: %s" % spider.name)


class FoundationAppScraperDownloaderMiddleware:
    # 和上面一样，Scrapy用来创建爬虫的方法
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # 处理每个下载请求，先不动它
        return None

    def process_response(self, request, response, spider):
        # 处理下载器返回的响应，直接返回
        return response

    def process_exception(self, request, exception, spider):
        # 处理下载异常，先放着
        pass

    def spider_opened(self, spider):
        spider.logger.info("爬虫准备就绪: %s" % spider.name)
