# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FoundationAppScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

    
from scrapy import Item, Field

class NFTScanItem(Item):
    url = Field()
    description = Field()
    medium_simplified = Field()
    transactions = Field()