import scrapy
from django.conf import settings
from urllib.parse import urlparse

class KeywordSpider(scrapy.Spider):
    name = 'keyword-spider'

    custom_settings = {
        'LOG_ENABLED': settings.DEBUG
    }

    def start_requests(self):
        if self.urls in ['' or None]:
            return

        for url in self.urls:
                yield scrapy.Request(url)

    def parse(self, response):
        text = response.text
        parts = urlparse(response.url)

        obj = {
            'domain': parts.netloc,
            'url': response.url
        }

        for keyword in self.keywords:
            obj[f"\"{keyword}\" count"] = text.count(keyword)


        yield obj
