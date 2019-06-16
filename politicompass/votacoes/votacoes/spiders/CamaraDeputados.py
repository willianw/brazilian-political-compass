from scrapy.http.request import Request
from scrapy.shell import inspect_response
import datetime
import scrapy

class CamaraDeputados(scrapy.Spider):
    name = "camara_deputados"

    def start_requests(self):
        year = 1991
        legislature = 49
        i = 0
        currentYr = datetime.datetime.now().year
        url = "https://www.camara.leg.br/internet/deputado/RelVotacoes.asp?nuLegislatura={:d}&dtInicio=01/01/{:d}&dtFim=31/12/{:d}&nuMatricula=1"
        while year <= currentYr:
            yield Request(url.format(legislature, year, year), self.parse, headers={'meta': {
                'legislature': legislature,
                'year': year,
                'matr': 1}})
            year += 1
            i += 1
            if i >= 4:
                yield Request(url.format(legislature, year, year), self.parse, headers={'meta': {
                    'legislature': legislature,
                    'year': year,
                    'matr': 1}})
                legislature += 1
                i = 0
            break # REMOVE ME

    def parse(self, response):
        content = response.xpath("//div[@id='content']")
        if content:
            req = response.request
            attr, matr = req.url.split('&')[-1].split('=')
            req = req.replace(
                url = "%s&%s=%d"%('&'.join(req.url.split('&')[:-1]), attr, int(matr)+1)
                )
            yield req
        content = content.xpath('/h3/a')
        if content:
            inspect_response(response, self)
            item = scrapy.Item()

            item['name'] = content.xpath('').re(r'ID: (\d+)')
            item['name'] = response.xpath('//td[@id="item_name"]/text()').get()
            item['description'] = response.xpath('//td[@id="item_description"]/text()').get()
            return item