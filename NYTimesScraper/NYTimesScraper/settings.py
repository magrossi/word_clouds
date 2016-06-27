# -*- coding: utf-8 -*-

# Scrapy settings for NYTimesScraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'NYTimesScraper'

SPIDER_MODULES = ['NYTimesScraper.spiders']
NEWSPIDER_MODULE = 'NYTimesScraper.spiders'
RANDOMIZE_DOWNLOAD_DELAY = True
ITEM_PIPELINES = {
	'NYTimesScraper.pipelines.NYTimesScraperItemValidatorPipeline': 100,
#	'NYTimesScraper.pipelines.NYTimesScraperItemDuplicatesPipeline': 200,
	'NYTimesScraper.pipelines.NYTimesScraperItemToFilePipeline': 300
}
LOG_ENABLED = True
LOG_LEVEL = 'CRITICAL'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'NYTimesScraper (+http://www.yourdomain.com)'
