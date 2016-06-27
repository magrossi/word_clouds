# -*- coding: utf-8 -*-
import scrapy
import json
import datetime
import re
from scrapy.contrib.spiders import CrawlSpider
from scrapy.http import Request
from scrapy import log
from NYTimesScraper.items import NYTimesScraperItem

class NYTimesSpider(CrawlSpider):
    name = "nytimes"
    allowed_domains = ("nytimes.com", )
    #start_urls = (
        #'http://www.nytimes.com/',
        #'http://www.nytimes.com/pages/politics/index.html',
        #'http://www.nytimes.com/pages/business/index.html',
        #'http://www.nytimes.com/pages/technology/index.html',
        #'http://www.nytimes.com/2014/10/17/technology/new-apple-ipads-mac-computers.html',
        #'http://www.nytimes.com/2014/10/12/technology/riot-games-league-of-legends-main-attraction-esports.html', 
    #)
    #rules = ( Rule (LinkExtractor(allow=("", ),),
    #            callback="parse",  follow= True),
    #)
    #rules = ( Rule (LinkExtractor(allow=("http://www.nytimes.com/2014", ),),
    #            callback="parse_item",  follow= True),
    #)
    #rules = (Rule(LinkExtractor()), ) #allow=(r'http://www.nytimes.com/2014', )), follow=True),)
    #rules = [
    # Extract links matching 'category.php' (but not matching 'subsection.php')
    # and follow links from them (since no callback means follow=True by default).
    #    Rule(LxmlLinkExtractor(allow=[r'2010/\d+']), follow=True)
    #]
    #url='http://www.nytimes.com/2014/10
    #rules = [Rule(SgmlLinkExtractor(allow=[r'page/\d+']), follow=True), 
        # r'page/\d+' : regular expression for http://isbullsh.it/page/X URLs
    #   Rule(SgmlLinkExtractor(allow=[r'\d{4}/\d{2}/\w+']), callback='parse_blogpost')]
    # r'\d{4}/\d{2}/\w+' : regular expression for http://isbullsh.it/YYYY/MM/title URLs

    def __init__(self, start=None, end=None, *args, **kwargs):
        super(NYTimesSpider, self).__init__(*args, **kwargs)
        self.qryUrl = r'http://query.nytimes.com/svc/cse/v2pp/sitesearch.json?sort_order=a&date_range_upper={0}&date_range_lower={1}&page={2}'
        self.rangeUpper = end
        self.rangeLower = start
        self.pageNumber = 0
        self.currDate = start
        self.start_urls = (self.qryUrl.format(self.currDate, self.currDate, self.pageNumber), )
        self.total_items = 0
        self.invalid_items = 0
        self.total_articles = 0

    def parse_article(self, response):
        self.total_items += 1
        try:
            # Create the content item
            item = NYTimesScraperItem()
            item['date'] = response.xpath('//meta[@property="article:published" or @itemprop="datePublished"]/@content').extract()[0]
            item['url'] = response.xpath('//meta[@property="twitter:url" or @name="twitter:url" or @property="og:url"]/@content').extract()[0]
            item['title'] = response.xpath('//meta[@property="twitter:title" or @name="twitter:title" or @property="og:title"]/@content').extract()[0]
            item['description'] = response.xpath('//meta[@property="twitter:description" or @name="twitter:description" or @property="og:description" or @name="description"]/@content').extract()[0]
            item['author'] = response.xpath('//meta[@name="author"]/@content').extract()[0] if len(response.xpath('//meta[@name="author"]/@content').extract()) > 0 else u'Unknown'
            item['category'] = re.sub('[^a-zA-Z0-9]', '', response.xpath('//meta[@name="CG"]/@content').extract()[0])            
            item['textType'] = response.xpath('//meta[@name="PT"]/@content').extract()[0]
            item['text'] = ''
            for sel in response.xpath('//p[contains(concat(" ",@class," ")," story-body-text ") or @itemprop="articleBody"]/text()'):
                item['text'] = item['text'] + sel.extract()
            yield item
        except Exception, e:
            # log the exception and returns nothing
            self.invalid_items += 1
            log.msg("Parsing [" + response.url + "]. Reason: " + str(e), level=log.ERROR)
            return # returns nothing if this page is not a news article

    # Parse the JSON objects for the search results from NYTimes 
    # http://query.nytimes.com/svc/cse/v2pp/sitesearch.json?date_range_upper=20150101&date_range_lower=20140101&page=1
    def parse(self, response):
        res = json.loads(response.body)['results']
        # ['results']['meta']['payload'] is the number of articles returned
        # print 'Payload: ' + str(res['meta']['payload'])
        # ['results']['meta']['results_estimated_total'] is the estimated total number of articles for the search criteria
        # print 'Estimated Total: ' + str(res['meta']['results_estimated_total'])
        # ['results']['meta']['results_end'] is the last article in this search (when it is equal to estimated then its the end
        # print 'Results End: ' + str(res['meta']['results_end'])
        # ['results']['results'][0]['twitter:url']
        # for i in o['results']['results']:
        #   print i['twitter:url']
        if int(res['meta']['payload']) > 0:
            print 'Processing date {0} items {1} of {2}.'.format(self.currDate, res['meta']['results_end'], res['meta']['results_estimated_total'])
            # Pass the articles to be parsed by the proper callback function
            for art in res['results']:
                try:
                    yield Request(art['url'], callback=self.parse_article)
                except:
                    log.msg('Item without url element: [' + str(response.url) + ']', level=log.ERROR)
            # If not a the end of the search pass it again recursively to continue
            if int(res['meta']['results_end']) < int(res['meta']['results_estimated_total']):
                # find which result page we are and increment one
                self.pageNumber += 1
                # dates remain the same
                # print 'Next search: ' + self.qryUrl.format(self.currDate, self.currDate, self.pageNumber)
                yield Request(self.qryUrl.format(self.currDate, self.currDate, self.pageNumber), callback=self.parse)
            else:
                # Try to increase the range by one day and see if its still in the allowed interval
                if self.currDate < self.rangeUpper:
                    self.currDate = (datetime.datetime.strptime(self.currDate, '%Y%m%d') + datetime.timedelta(days=1)).strftime('%Y%m%d')
                    self.pageNumber = 0
                    # print 'Day increase.\nNext search: ' + self.qryUrl.format(self.currDate, self.currDate, self.pageNumber)
                    yield Request(self.qryUrl.format(self.currDate, self.currDate, self.pageNumber), callback=self.parse)
                else:
                    log.msg('Crawl finished: upper date range reached', level=log.INFO)
                    return # end of search
                # datetime.datetime.strptime("20140101", "%Y%m%d")
                # d = datetime.datetime.strptime("20140101", "%Y%m%d")
                # d += datetime.timedelta(days=1)
                # d.strftime('%Y%m%d')
        else:
            log.msg('Crawl finished: no payload received', level=log.INFO)
            return # end of search