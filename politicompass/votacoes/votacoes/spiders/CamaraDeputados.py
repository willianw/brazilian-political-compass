from scrapy.http.request import Request
# from scrapy.shell import inspect_response
from datetime import datetime
import scrapy

from votacoes.items import VotoItem


class CamaraDeputados(scrapy.Spider):
    name = "camara_deputados"

    def start_requests(self):
        url = "https://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/" \
              + "ListarProposicoesVotadasEmPlenario?ano={}&tipo="
        currentYr = datetime.now().year
        for year in range(1991, currentYr + 1):
            yield Request(url.format(year),
                          self.parse_year,
                          meta={'year': year})
            break

    def parse_year(self, response):
        url_prop = "https://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/" \
                   + "ObterVotacaoProposicao?tipo={}&numero={}&ano={}"
        for proposicao in response.xpath("//proposicoes/proposicao"):
            codigo = proposicao.xpath('codProposicao/text()').get()
            nome_prop = proposicao.xpath('nomeProposicao/text()')
            type_prop, code_prop, year_prop = \
                nome_prop.re('([A-Z]+) (\d+)/(\d+)')
            nome = nome_prop.get()
            data = proposicao.xpath('dataVotacao/text()').get()
            yield Request(url=url_prop.format(type_prop, code_prop, year_prop),
                          callback=self.parse_proposal,
                          meta={
                              'prop_id': codigo,
                              'prop_name': nome,
                              'prop_date': data
                          })

    def parse_proposal(self, response):
        metadata = response.meta
        prop_id = metadata['prop_id']
        prop_name = metadata['prop_name']

        for votacao in response.xpath('//Votacoes/Votacao'):
            votacao_date = votacao.xpath('@Data').get()
            votacao_name = votacao.xpath('@ObjVotacao').get()
            votacao_id = votacao.xpath('@codSessao').get()
            for voto in votacao.xpath('votos/Deputado'):
                dep = VotoItem()
                dep['candidato_id'] = voto.xpath('@ideCadastro').get()
                dep['candidato_name'] = voto.xpath('@Nome').get()
                dep['candidato_part'] = voto.xpath('@Partido').get()
                dep['candidato_uf'] = voto.xpath('@UF').get()
                dep['proposition_id'] = prop_id
                dep['proposition_name'] = prop_name
                dep['sessao_desc'] = votacao_name
                dep['sessao_id'] = votacao_id
                dep['date'] = votacao_date
                voto_str = voto.xpath('@Voto').get().lower().strip()
                dep['voto'] = 1 if voto_str == 'sim' \
                    else -1 if voto_str == 'não' \
                    else 0
                yield dep
