import json
from datetime import datetime
from scrapy import signals
from scrapy.exceptions import NotConfigured
from requests import post as post_request, exceptions as request_exceptions
from immoscraper.settings import IMMO_VIZ_API_URL

# FetchingReporterExtension is a Scrapy extension that listens explicitly to the spider_closed signal
class FetchingReporterExtension:
    def __init__(self):
        self.start_time = None
        self.item_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        """
        This method is called when the extension is created.
        It connects the spider_opened, item_scraped, and spider_closed signals to the extension.
        """
        if not crawler.settings.get('IMMO_VIZ_API_URL'):
            raise NotConfigured("IMMO_VIZ_API_URL not set")
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        spider.logger.info(f"[FetchingReporter] Started at {self.start_time.isoformat()}")

    def item_scraped(self, item, spider):
        self.item_count += 1
        # Log every 10 items or the first one
        if self.item_count == 1 or self.item_count % 10 == 0:
            spider.logger.info(f"[FetchingReporter] Processed {self.item_count} items")

    def spider_closed(self, spider, reason):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        report = {
            "source_name": spider.name,
            "fetch_type": 1,
            "success": self.item_count > 0,
            "started_at": self.start_time.isoformat(),
            "ended_at": end_time.isoformat(),
            "duration_in_seconds": duration,
            "item_processed_count": self.item_count
        }
        spider.logger.info(f"[FetchingReporter] Sending report ({self.item_count} items, {duration:.2f}s)")
        try:
            resp = post_request(
                url=IMMO_VIZ_API_URL + "/fetching_reports",
                data=json.dumps(report),
                timeout=10
            )
            if 200 <= resp.status_code < 300:
                spider.logger.info(f"[FetchingReporter] Report sent ({resp.status_code})")
            else:
                spider.logger.error(f"[FetchingReporter] Report failed ({resp.status_code})")
        except request_exceptions.ConnectionError:
            spider.logger.warning("[FetchingReporter] Cannot connect to API")
        except Exception as e:
            spider.logger.error(f"[FetchingReporter] Error: {e}") 