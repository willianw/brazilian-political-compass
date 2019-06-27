# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
from scrapy.exporters import CsvItemExporter
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


class VotacoesPipeline(object):

    OUTPUT_PATH = 'output'
    OUTPUT_FILES = {
        ('CandidadoItem', 'camara_deputados'): 'candidatos_deputados.csv',
        ('CandidadoItem', 'camara_senado'): 'candidatos_senado.csv',
        ('VotoItem', 'camara_deputados'): 'votos_deputados.csv',
        ('VotoItem', 'camara_senado'): 'votos_senado.csv',
    }

    def __init__(self):
        if not os.path.exists(self.OUTPUT_PATH):
            os.mkdir(self.OUTPUT_PATH)
        dispatcher.connect(self.spider_opened, signal=signals.spider_opened)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)
        self.files = {
            name: open(os.path.join(self.OUTPUT_PATH, filename), 'wb')
            for name, filename in self.OUTPUT_FILES.items()
            }
        self.exporters = {
            name: CsvItemExporter(fp)
            for name, fp in self.files.items()
            }

    def spider_opened(self, spider):
        [e.start_exporting() for e in self.exporters.values()]

    def spider_closed(self, spider):
        [e.finish_exporting() for e in self.exporters.values()]
        [f.close() for f in self.files.values()]

    def process_item(self, item, spider):
        item_spider = (type(item).__name__, spider.name)
        if item_spider in self.OUTPUT_FILES:
            self.exporters[item_spider].export_item(item)
        else:
            combinations = list(self.OUTPUT_FILES.keys())
            raise AttributeError(
                "item {} not found in {}"
                .format(item_spider, combinations)
            )
        return item
