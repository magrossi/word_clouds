# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import re
import os
import codecs
from urlparse import urlparse
from scrapy import log
from scrapy.exceptions import DropItem

class NYTimesScraperItemValidatorPipeline(object):
	def __init__(self):
		self.total = 0
		self.invalid = 0

	def process_item(self, item, spider):
		self.total += 1
		if not item['text'] or not item['url'] or not item['date'] or not item['title'] or not item['description'] or not item['category']:
			self.invalid += 1
			raise DropItem("Not an article %s" % item['url'])
		else:
			return item

	def close_spider(self, spider):
		print 'Validated ' + str(self.total - self.invalid) + ' of ' + str(self.total) + ' items.'

class NYTimesScraperItemDuplicatesPipeline(object):
	def process_item(self, item, spider):
		return item

class NYTimesScraperItemToFilePipeline(object):
	def __init__(self):
		self.fileCount = 0

	def cleanUrlTitle(self, url):
		# http://www.nytimes.com/2014/10/18/business/obama-orders-stronger-security-on-us-payment-systems.html?action=click&contentCollection=Business%20Day&region=Footer&module=MoreInSection&pgtype=article
		# will return
		# obama-orders-stronger-security-on-us-payment-systems
		parse = os.path.splitext(urlparse(url).path)[0]
		parse = next(s for s in reversed(parse.split('/')) if s).lower()		
		return  re.sub(r'[^\w]', '', parse)

	def process_item(self, item, spider):
		# data\category\YYYY-MM-DD\cleanurltitle
		title = self.cleanUrlTitle(item['url'])
		date = item['date']
		filename = "c:/data/raw_data/{0}/{1}/{2}.json".format(item['category'], date, title)
		filename = os.path.normpath(filename)
		# make any non-existing directories
		if not os.path.exists(os.path.dirname(filename)):
			os.makedirs(os.path.dirname(filename))
		# open and write to file
		#jsonItem = jsonpickle.encode(item)
		jsonItem = json.dumps(dict(item), ensure_ascii=False, indent=4, sort_keys=True, separators=(',',':'))
		with codecs.open(filename, 'w', 'utf-8') as f:
			log.msg('Saving JSON to file: ' + filename, level=log.INFO)
			f.write(jsonItem)
			f.close()
			self.fileCount += 1
		# return item
		return item

	def close_spider(self, spider):
		print 'Saved ' + str(self.fileCount) + ' files to disk.'