# -*- coding: utf-8 -*-

import scrapy


class XinwenlianboItem(scrapy.Item):
    url = scrapy.Field()
    html = scrapy.Field()
    title = scrapy.Field()
