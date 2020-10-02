# -*- coding: utf-8 -*-

"""
See documentation:  http://doc.scrapy.org/en/latest/topics/items.html
"""

import copy

import moment

from scrapy import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst

from titlecase import titlecase

from delancey import models


# ----------------------------------------------------------------------------
# Processors
# ----------------------------------------------------------------------------

def strip_whitespace(text):
    text = str(text).replace("\n", " ").replace("\r", " ").strip()
    if text == "":
        return None
    return text


def title_check(text):
    if text is None:
        return text
    title_parts = text.strip().split(" -")
    if len(title_parts) == 2:
        title, date = title_parts
        if title.startswith("delanceyplace"):
            return titlecase(date.strip("-")).strip()
        return titlecase(title.strip("-")).strip()
    return titlecase(text).strip()


def unix_time_to_date(text):
    try:
        date = moment.unix(int(text)).format("YYYY-MM-DD")
    except:
        date = text
    return date


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

class DefaultLoader(ItemLoader):
    default_input_processor = MapCompose()
    default_output_processor = TakeFirst()


class ModelItem(Item):
    """
    Make Peewee models easily turn into Scrapy Items.

    >>> from models import Player
    >>> item = ModelItem(Player())
    """

    def __init__(self, model=None, **kwds):
        super(ModelItem, self).__init__()

        if model:
            self.__model__ = model

        if "Meta" in dir(self):
            for key, processor in self.Meta.__dict__.items():
                if not key.startswith("__"):
                    kwds[key] = processor

        for key in self.model._meta.fields.keys():
            self.fields[key] = Field()

        if kwds is not None:
            for key, processor in kwds.items():
                self.fields[key] = Field(input_processor=MapCompose(
                    strip_whitespace, processor
                ))

    def __setitem__(self, key, value):
        if key not in self.fields:
            self.fields[key] = Field()
        self._values[key] = value

    def copy(self):
        return copy.deepcopy(self)

    def save(self):
        return self.model.from_scrapy_item(self)

    @property
    def model(self):
        return self.__model__


# ----------------------------------------------------------------------------
# Items
# ----------------------------------------------------------------------------

class Post(ModelItem):
    __model__ = models.Post

    class Meta:
        title = title_check
