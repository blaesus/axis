# -*- coding: utf-8 -*-

from sqlalchemy.orm import sessionmaker
from axis_scrape.models import Reports, db_connect, create_deals_table


class XinwenlianboScrapePipeline(object):
    def __init__(self):
        engine = db_connect()
        create_deals_table(engine)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        session = self.Session()
        report = Reports(**item)

        try:
            session.add(report)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

        return item
