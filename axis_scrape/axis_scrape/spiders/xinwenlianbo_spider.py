import scrapy
from datetime import date, timedelta

def getIndexUrls(start_date=None, end_date=None):
    """
    :param start_date:
    :param end_date:
    :return: {dict} such as {'http://stuff.com/...': date(2015, 3, 4)}

    Official JavaScript implementation, see source code of
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

    FIRST_AVAILABLE_DATE = date(2009, 6, 27)
    URL_SCHEMA_CHANGE_DATE_A = date(2010, 5, 6)
    URL_SCHEMA_CHANGE_DATE_B = date(2011, 4, 6)

    if not start_date:
        start_date = FIRST_AVAILABLE_DATE
    if not end_date:
        end_date = date.today()

    index_urls = {}
    today = start_date
    while today < end_date:
        date_numerals = str(today).replace('-', '')
        if today < URL_SCHEMA_CHANGE_DATE_A:
            index_url = 'http://news.cctv.com/program/xwlb/' + \
                        date_numerals + '.shtml'
        elif today < URL_SCHEMA_CHANGE_DATE_B:
            index_url = 'http://news.cntv.cn/program/xwlb/' + \
                        date_numerals + '.shtml'
        else:
            index_url = 'http://cctv.cntv.cn/lm/xinwenlianbo/' + \
                        date_numerals + '.shtml'
        index_urls[index_url] = today
        today += timedelta(days=1)
    print('index_urls', index_urls)
    return index_urls


def extract_article_links_a(response):
    pass


def extract_article_links_b1(response):
    pass


def extract_article_links_b2(response):
    pass


def extract_article_links_b3(response):
    pass


def extract_article_links_b4(response):
    pass


def extract_article_links_latest(response):
    pass


def get_period_definitions():
    periods = [
        {
            'name': 'period-a',
            'start': date(2009, 6, 27),
            'end':   date(2011, 4, 5),
            'extract_article_links': extract_article_links_a
        },
        {
            'name': 'period-b1',
            'start': date(2011, 4, 6),
            'end':   date(2012, 2, 27),
            'extract_article_links': extract_article_links_b1
        },
        {
            'name': 'period-b2',
            'start': date(2012, 2, 28),
            'end':   date(2012, 3, 29),
            'extract_article_links': extract_article_links_b2
        },
        {
            'name': 'period-b3',
            'start': date(2012, 3, 30),
            'end':   date(2013, 7, 14),
            'extract_article_links': extract_article_links_b3
        },
        {
            'name': 'period-b4',
            'start': date(2013, 7, 15),
            'end':   date(2016, 2, 6),  # Last date of confirmed use
            'extract_article_links': extract_article_links_b4
        },
        {
            'name': 'latest',
            'start':   date(2016, 2, 7),
            'end':   date(2046, 6, 30),
            'extract_article_links': extract_article_links_latest
        },
    ]
    return periods

indexUrls = getIndexUrls()
# Debug
indexUrls = getIndexUrls(date(2016, 2, 5), date.today())


def getPeriod(target_date, periods):
    period = None
    for period in periods:
        if period['start'] <= target_date <= period['end']:
            period = period
            break
    if not period:
        return next(period for period in periods if period['name'] == 'latest')
    return period


class XinwenlianboSpider(scrapy.Spider):
    name = 'xinwenlianbo'
    allowed_domains = ['cntv.cn']

    start_urls = indexUrls.keys()

    def parse(self, response):
        current_date = indexUrls[response.url]
        periods = get_period_definitions()
        current_period = getPeriod(current_date, periods)
        extract_article_links = current_period['extract_article_links']
        article_links = extract_article_links(response.body)

        for article_link in article_links:
            article_request = scrapy.Request(article_link,
                                             callback=self.parse_single_report)
            article_request.meta['period'] = current_period
            yield article_request

    def parse_single_report(self, response):
        yield {
            'title': ''
        }
