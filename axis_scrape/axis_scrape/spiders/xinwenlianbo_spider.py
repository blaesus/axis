import scrapy
from urllib.parse import urljoin
from datetime import datetime, date, timedelta

# Naming indices for use in combination with url_schemes
DATE = 0
URL_FUNCTION = 1


def get_url_schemes():
    """
    Get the a tuple representing relationship between dates and urls of index pages.
    :return: {tuple}

    See official JavaScript implementation, such as source code of
    http://news.cntv.cn/program/xwlb/20100506.shtml
    """

    # [(Start-date, URL function)]
    return (
        (date(2002, 9, 8), lambda s:
            'http://www.cctv.com/news/xwlb/' + s + '/index.shtml'),
        (date(2009, 6, 26), lambda s:
            'http://news.cctv.com/program/xwlb/' + s + '.shtml'),
        (date(2010, 5, 6), lambda s:
            'http://news.cntv.cn/program/xwlb/' + s + '.shtml'),
        (date(2011, 4, 6), lambda s:
            'http://cctv.cntv.cn/lm/xinwenlianbo/' + s + '.shtml'),
    )


def get_index_urls(start_date=None, end_date=None):
    """
    Get a list of urls to candidate index pages and the publication date.
    The list is not ordered by date.
    :param start_date:
    :param end_date:
    :return: {dict} such as {'http://stuff.com/...': date(2015, 3, 4)}
    """

    url_schemes = get_url_schemes()

    if not start_date:
        start_date = url_schemes[0][DATE]
    if not end_date:
        end_date = date.today()
    index_urls = {}

    today = start_date
    while today <= end_date:
        date_numerals = str(today).replace('-', '')

        index_url = None
        for scheme in reversed(url_schemes):
            if scheme[DATE] <= today:
                index_url = scheme[URL_FUNCTION](date_numerals)
                break

        index_urls[index_url] = today
        today += timedelta(days=1)
    return index_urls


def extract_article_links_a(response):
    return [urljoin(response.url, path)
            for path in response.xpath('//a[@class="color4"]/@href').extract()
            if path]


def extract_article_links_b(response):
    return response.xpath('//ul[@class="title_list tl_f14 tl_video"]//a[@target="_blank"]/@href').extract()


def extract_article_links_c(response):
    return extract_article_links_b(response)


def extract_article_links_d1(response):
    return response.xpath('//script/text()').re("title_array_01.*,'(.*?)'")


def extract_article_links_d2(response):
    return extract_article_links_d1(response)


def extract_article_links_d3(response):
    return extract_article_links_d1(response)


def extract_article_links_d4(response):
    return response.xpath('//ul[contains(@class, "fs_14")]/li/a/@href').extract()


def extract_article_links_latest(response):
    return extract_article_links_d4(response)


def get_period_definitions():
    periods = [
        {
            'name': 'period-a',
            'start': date(2002, 9, 8),
            'end':   date(2009, 6, 25),
            'extract_article_links': extract_article_links_a
        },
        {
            'name': 'period-b',
            'start': date(2009, 6, 26),
            'end':   date(2010, 5, 5),
            'extract_article_links': extract_article_links_b
        },
        {
            'name': 'period-c',
            'start': date(2010, 5, 6),
            'end':   date(2011, 4, 5),
            'extract_article_links': extract_article_links_c
        },
        {
            'name': 'period-d1',
            'start': date(2011, 4, 6),
            'end':   date(2012, 2, 26),
            'extract_article_links': extract_article_links_d1
        },
        {
            'name': 'period-c2',
            'start': date(2012, 2, 27),
            'end':   date(2012, 3, 28),
            'extract_article_links': extract_article_links_d2
        },
        {
            'name': 'period-c3',
            'start': date(2012, 3, 30),
            'end':   date(2013, 7, 14),
            'extract_article_links': extract_article_links_d3
        },
        {
            'name': 'period-c4',
            'start': date(2013, 7, 15),
            'end':   date(2016, 2, 6),  # Last date of confirmed use
            'extract_article_links': extract_article_links_d4
        },
        {
            'name': 'latest',
            'start': date(2016, 2, 7),
            'end':   date(2046, 6, 30),
            'extract_article_links': extract_article_links_latest
        },
    ]
    return periods



def get_period(target_date, periods):
    period = None
    for period in periods:
        if period['start'] <= target_date <= period['end']:
            period = period
            break
    if not period:
        return next(period for period in periods if period['name'] == 'latest')
    return period


def clean_str(s):
    return s.replace('\xa0', ' ')\
        .replace('\u3000', ' ')\
        .replace('\r\n', '\n') \
        .replace('\n\n', '\n') \
        .replace('\n  ', '\n')\
        .strip()


def make_minimal_record(response, response_type='unexpected'):
    return {
        'url': response.url,
        'html': response.body,
        'order': response.meta['order'],
        'type': response_type,
        'pub_date': response.meta['pub_date'],
        'scrape_time_utc': datetime.utcnow(),
    }


class XinwenlianboSpider(scrapy.Spider):

    name = 'xinwenlianbo'

    def __init__(self, start=None, end=None, *args, **kwargs):
        super(XinwenlianboSpider, self).__init__(*args, **kwargs)

        date_format = '%Y%m%d'
        start_date = date.today()
        end_date = date.today()

        if start:
            start_date = datetime.strptime(start, date_format).date()
        if end:
            end_date = datetime.strptime(end, date_format).date()
        self.indexUrls = get_index_urls(start_date, end_date)

        self.start_urls = self.indexUrls.keys()

        self.handle_httpstatus_list = [404]

    def parse(self, response):
        current_date = self.indexUrls[response.url]
        periods = get_period_definitions()
        current_period = get_period(current_date, periods)
        extract_article_links = current_period['extract_article_links']
        response.meta['order'] = None
        response.meta['pub_date'] = current_date

        yield make_minimal_record(response, 'index')

        article_links = extract_article_links(response)

        for index, article_link in enumerate(article_links):
            article_request = scrapy.Request(article_link,
                                             callback=self.parse_single_article)
            article_request.meta['order'] = index
            article_request.meta['pub_date'] = current_date
            yield article_request

    def parse_single_article(self, response):
        """
        Gather information about one report in a day
        :param response:
        :return: {dict}
        """

        # Handle 404
        if response.status == 404:
            yield make_minimal_record(response, response_type='missing')

        # Handle buggy pages on Xinwenlianbo's side, such as
        # http://news.cctv.com/xwlb/20060621/105163.shtml
        if len(response.body) < 300:
            yield make_minimal_record(response)
        else:
            title = None
            title_xpaths = [
                '//*[@align="center"]/p/font[@class="fs24"]/text()',
                '//p/font[@class="title_text"]/text()',
                '//*[@align="center"]/span[@class="title"]/text()',
                '//div[@class="head_bar"]/h1/text()',
                '//div[@class="title padd"]/h1/text()',
                '//div[@class="top_title"]/h1[@class="b-tit"]/text()'
            ]
            for xpath in title_xpaths:
                xpath_matches = response.xpath(xpath).extract()
                if xpath_matches:
                    title = clean_str(''.join(xpath_matches))
                    break

            main_text = None
            main_text_xpaths = [
                '//td[@width="608" and @colspan="3"]/text()',
                '//div[@id="content"]//*[self::p or self::span]/text()',
                '//*[@align="center"]//*[self::p or self::span]/text()',
                '//div[@id="md_major_article_content"]//*[self::p or self::span]/text()',
                '//td[@class="large"]//*[self::p or self::span]/text()',
                '//div[@class="text_box"]//*[self::p or self::span]/text()',
                '//div[@id="content_body"]//*[self::p or self::span]/text()',
                '//div[@id="top_title"]/p[@class="art-info"]/text()'
            ]
            for xpath in main_text_xpaths:
                xpath_matches = response.xpath(xpath).extract()
                if xpath_matches:
                    main_text = clean_str('\n'.join(xpath_matches))
                    break

            if (title is None) or (main_text is None):
                yield make_minimal_record(response)
            else:
                yield {
                    'url': response.url,
                    'html': response.body,
                    'title': title,
                    'order': response.meta['order'],
                    'type': 'report',
                    'pub_date': response.meta['pub_date'],
                    'scrape_time_utc': datetime.utcnow(),
                    'main_text': main_text
                }
