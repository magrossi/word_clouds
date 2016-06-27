# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class NYTimesScraperItem(scrapy.Item):
	url = scrapy.Field()
	date = scrapy.Field()
	title = scrapy.Field()
	description = scrapy.Field()
	author = scrapy.Field()
	category = scrapy.Field()
	textType = scrapy.Field()
	text = scrapy.Field()