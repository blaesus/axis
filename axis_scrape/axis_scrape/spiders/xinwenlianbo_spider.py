import scrapy
from urllib.parse import urljoin
from datetime import datetime, date, timedelta

# Naming indices for use in combination with url_schemes
DATE = 0
URL_FUNCTION = 1


def get_url_schemes():
    """
    See official JavaScript implementation, such as source code of
    http://news.cntv.cn/program/xwlb/20100506.shtml:

    if(time_1<20100506){
    str = "http://news.cctv.com/program/xwlb/" + year + mon + day + ".shtml";
    }
    if(time_1>=20100506&&time_1<20110406){
    str = "http://news.cntv.cn/program/xwlb/" + year + mon + day + ".shtml";
    }
    if(time_1>=20110406){
    str = "http://cctv.cntv.cn/lm/xinwenlianbo/" + year + mon + day + ".shtml";
    }
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
    return []

def extract_article_links_c1(response):
    return []


def extract_article_links_c2(response):
    return []


def extract_article_links_c3(response):
    return []


def extract_article_links_c4(response):
    return []


def extract_article_links_latest(response):
    return []


def get_period_definitions():
    periods = [
        {
            'name': 'period-a',
            'start': date(2002, 9, 8),
            'end':   date(2009, 6, 26),
            'extract_article_links': extract_article_links_a
        },
        {
            'name': 'period-b',
            'start': date(2009, 6, 27),
            'end':   date(2011, 4, 5),
            'extract_article_links': extract_article_links_b
        },
        {
            'name': 'period-c1',
            'start': date(2011, 4, 6),
            'end':   date(2012, 2, 27),
            'extract_article_links': extract_article_links_c1
        },
        {
            'name': 'period-c2',
            'start': date(2012, 2, 28),
            'end':   date(2012, 3, 29),
            'extract_article_links': extract_article_links_c2
        },
        {
            'name': 'period-c3',
            'start': date(2012, 3, 30),
            'end':   date(2013, 7, 14),
            'extract_article_links': extract_article_links_c3
        },
        {
            'name': 'period-c4',
            'start': date(2013, 7, 15),
            'end':   date(2016, 2, 6),  # Last date of confirmed use
            'extract_article_links': extract_article_links_c4
        },
        {
            'name': 'latest',
            'start': date(2016, 2, 7),
            'end':   date(2046, 6, 30),
            'extract_article_links': extract_article_links_latest
        },
    ]
    return periods

# indexUrls = get_index_urls()
# Debug
# indexUrls = get_index_urls(end_date=date(2009, 6, 26))
indexUrls = get_index_urls(start_date=date(2006, 6, 21), end_date=date(2006, 6, 21))


def getPeriod(target_date, periods):
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


class XinwenlianboSpider(scrapy.Spider):
    name = 'xinwenlianbo'

    start_urls = indexUrls.keys()

    def parse(self, response):
        current_date = indexUrls[response.url]
        periods = get_period_definitions()
        current_period = getPeriod(current_date, periods)
        extract_article_links = current_period['extract_article_links']

        yield {
            'url': response.url,
            'html': response.body,
            'title': '',
            'type': 'index',
            'pub_date': current_date,
            'scrape_time_utc': datetime.utcnow(),
        }

        article_links = extract_article_links(response)

        for index, article_link in enumerate(article_links):
            article_request = scrapy.Request(article_link,
                                             callback=self.parse_single_article)
            article_request.meta['order'] = index
            article_request.meta['pub_date'] = current_date
            yield article_request

    def parse_single_article(self, response):

        # Handle buggy pages on Xinwenlianbo's side, such as
        # http://news.cctv.com/xwlb/20060621/105163.shtml
        if len(response.body) < 300:
            return {
                'url': response.url,
                'html': response.body,
                'order': response.meta['order'],
                'type': 'report-broken',
                'pub_date': response.meta['pub_date'],
                'scrape_time_utc': datetime.utcnow(),
            }

        title = None
        title_xpaths = [
            '//*[@align="center"]/p/font[@class="fs24"]/text()',
            '//p/font[@class="title_text"]/text()',
            '//*[@align="center"]/span[@class="title"]/text()',
            '//div[@class="head_bar"]/h1/text()',
        ]
        for xpath in title_xpaths:
            xpath_matches = response.xpath(xpath).extract()
            if xpath_matches:
                title = clean_str(xpath_matches[0])
                break
        if title is None:
            raise scrapy.exceptions.CloseSpider('Cannot extract title '+response.url)

        main_text = None
        main_text_xpaths = [
            '//td[@width="608" and @colspan="3"]/text()',
            '//div[@id="content"]/p/text()',
            '//*[@align="center"]/p/text()',
            '//div[@id="md_major_article_content"]/p/text()',
            '//td[@class="large"]/p/text()',
        ]
        for xpath in main_text_xpaths:
            xpath_matches = response.xpath(xpath).extract()
            if xpath_matches:
                main_text = clean_str('\n'.join(xpath_matches))
                break
        if main_text is None:
            raise scrapy.exceptions.CloseSpider('Cannot extract main text '+response.url)

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
