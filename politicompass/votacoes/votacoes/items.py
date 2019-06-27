# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class CandidadoItem(Item):
    name = Field()
    partido = Field()
    uf = Field()
    ano = Field()
    url = Field()
    candidato_id = Field()


class VotoItem(Item):
    candidato_id = Field()
    sessao_name = Field()
    sessao_desc = Field()
    sessao_url = Field()
    sessao_id = Field()
    date = Field()
    voto = Field()



