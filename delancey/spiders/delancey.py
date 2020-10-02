# -*- coding: utf-8 -*-

"""
Scrape some sort of website...
"""

import moment
from markdownify import markdownify as md

from scrapy import Request, Spider

from delancey.items import DefaultLoader, Post
from delancey.models import Post as PostModel


class DelanceyPlaceSpider(Spider):

    name = "delancey"
    allowed_domains = ["delanceyplace.com"]
    spider_url = "https://www.delanceyplace.com/view-archives.php?p={}"

    def start_requests(self):
        query = PostModel.select().where(
            PostModel.book_date.is_null()
        )
        # for post_id in range(2424, 4200 + 1):
        for post in query:
            post_id = post.id
            url = self.spider_url.format(post_id)
            meta = {"id": post_id}
            yield Request(url, meta=meta)


    def parse(self, response):
        article = response.css("article")[0]
        load = DefaultLoader(Post(), article)
        load.add_value("id", response.meta.get("id"))

        load.add_css("title", "h2::text")

        day = article.css(".dateDay::text").extract_first()
        month = article.css(".dateMonth::text").extract_first()
        year = article.css(".dateYear::text").extract_first()
        date = moment.date(f"{month} {day}, {year}").format("YYYY-MM-DD")
        load.add_value("date", date)

        body = "\n\n".join(article.css("section > p").extract())
        body = md(body).strip()
        load.add_value("body", body)

        rows = article.css(".table tr")
        for row in rows:
            about = row.css("h4::text").extract_first().strip(":")
            if about in {"author", "title", "pages", "publisher", "date"}:
                text = row.xpath("normalize-space(td[2])").extract_first().strip()
                load.add_value(f"book_{about}", text)

        yield load.load_item()
