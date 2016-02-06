from __future__ import print_function
import scrapy


class XinwenlianboSpider(scrapy.Spider):
    name = 'xinwenlianbo'
    allowed_domains = ['cntv.cn']
    start_urls = [
        'http://news.cntv.cn/2016/02/05/VIDEcgygrnQ7k037STCZ7ZCN160205.shtml'
    ]

    def parse(self, response):
        filename = response.url.split("/")[-2] + '.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
