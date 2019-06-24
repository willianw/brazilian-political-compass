from scrapy.http.request import Request
from scrapy.shell import inspect_response
from datetime import datetime
import scrapy
import pdb

from votacoes.items import CandidadoItem, VotoItem

class CamaraDeputados(scrapy.Spider):
    name = "camara_deputados"

    def start_requests(self):
        year = 1996
        legislature = 50
        i = 0
        currentYr = datetime.now().year
        url = "https://www.camara.leg.br/internet/deputado/RelVotacoes.asp?nuLegislatura={:d}&dtInicio=01/01/{:d}&dtFim=31/12/{:d}&nuMatricula=1"
        while year <= currentYr:
            yield Request(url.format(legislature, year, year), self.parse, meta={
                'legislature': legislature,
                'year': year,
                'matr': 1})
            year += 1
            i += 1
            if i >= 4:
                yield Request(url.format(legislature, year, year), self.parse, meta={
                    'legislature': legislature,
                    'year': year,
                    'matr': 1})
                legislature += 1
                i = 0

    def parse(self, response):
        content = response.xpath("//div[@id='content']")
        if content:
            req = response.request
            attr, matr = req.url.split('&')[-1].split('=')
            req = req.replace(
                url = "%s&%s=%d"%('&'.join(req.url.split('&')[:-1]), attr, int(matr)+1)
                )
            yield req
        title_link = content.xpath('h3/a')
        if title_link:
            cand = CandidadoItem()
            url = title_link.xpath('@href').get()
            title = title_link.xpath('text()')
            cand_id = int(url.split('/')[-1])
            cand['url'] = url.strip()
            cand['candidato_id'] = cand_id
            try:
                cand['ano'] = response.meta['year']
                cand['name'] = title.re('(.*) - [A-Za-z \.]+/[A-Z]{2}')[0].strip()
                cand['partido'] = title.re('.* - ([A-Za-z \.]+)/[A-Z]{2}')[0].strip()
                cand['uf'] = title.re('.* - [A-Za-z \.]+/([A-Z]{2})')[0].strip()
                yield cand
            except IndexError:
                inspect_response(response, self)
            for session in content.xpath('table/tr'):
                if session.xpath('self::*[contains(@class, "even")]'):
                    date_str = session.xpath('td[1]/text()').get().strip()
                    date = datetime.strptime(date_str, '%d/%m/%Y')
                    session_desc = session.xpath('td[2]/text()').get().strip()
                else:
                    voto = VotoItem()
                    sess = session.xpath('td[2]/a')
                    result = session.xpath('td[4]/text()').get()
                    voto['date'] = date
                    voto['candidato_id'] = cand_id
                    voto['sessao_desc'] = session_desc
                    if sess:
                        voto['sessao_name'] = sess.xpath('text()').get().strip()
                        voto['sessao_id'] = sess.xpath('text()').re('([0-9]+/[0-9]+)')[0]
                        voto['sessao_url'] = sess.xpath('@href').get().strip()
                    if result:
                        result = result.lower().strip()
                        voto['voto'] = 1 if result == 'sim' else -1 if result == 'não' else 0
                    else:
                        voto['voto'] = 0
                    yield voto
