# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
import pdb
from scrapy.exporters import CsvItemExporter
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

class VotacoesPipeline(object):

    OUTPUT_PATH = 'output'
    OUTPUT_FILES = {
        'CandidadoItem': 'candidatos.csv',
        'VotoItem': 'votos.csv',
    }    

    def __init__(self):
        if not os.path.exists(self.OUTPUT_PATH):
            os.mkdir(self.OUTPUT_PATH)
        dispatcher.connect(self.spider_opened, signal=signals.spider_opened)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)
        self.files = {name: open(os.path.join(self.OUTPUT_PATH, filename),'wb') for name, filename in self.OUTPUT_FILES.items()}
        self.exporters = {name: CsvItemExporter(fp) for name, fp in self.files.items()}

    def spider_opened(self, spider):
        [e.start_exporting() for e in self.exporters.values()]

    def spider_closed(self, spider):
        [e.finish_exporting() for e in self.exporters.values()]
        [f.close() for f in self.files.values()]

    def process_item(self, item, spider):
        item_name = type(item).__name__
        if item_name in self.OUTPUT_FILES:
            self.exporters[item_name].export_item(item)
        else:
            raise AttributeError(f"item {item_name} not found in {list(self.OUTPUT_FILES.keys())}")
        return item