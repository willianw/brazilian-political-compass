from scrapy.http.request import Request
# from scrapy.shell import inspect_response
from datetime import datetime
import scrapy
import json

from votacoes.items import CandidadoItem, VotoItem


class CamaraSenado(scrapy.Spider):
    name = 'camara_senado'

    def start_requests(self):
        url = "http://legis.senado.leg.br/dadosabertos/plenario/" \
              + "agenda/mes/{}{:02d}01"
        currentMn = datetime.now().month
        currentYr = datetime.now().year
        month = 4
        year = 2011
        while year < currentYr or month != currentMn:
            yield Request(url.format(year, month),
                          callback=self.parse_agenda,
                          headers={'Accept': 'application/json'})
            month += 1
            if month > 12:
                month = 1
                year += 1

    def parse_agenda(self, response):
        votacao_url = "http://legis.senado.leg.br/dadosabertos/materia/"\
                      + "votacoes/{:s}"
        agenda = json.loads(response.body_as_unicode())
        if not agenda \
           or 'AgendaPlenario' not in agenda \
           or agenda['AgendaPlenario'] is None:
            return None
        sessoes = agenda['AgendaPlenario']['Sessoes']['Sessao']
        if isinstance(sessoes, dict):
            sessoes = [sessoes]
        for sessao in sessoes:
            if 'Materias' in sessao:
                materias = sessao['Materias']['Materia']
                if isinstance(materias, dict):
                    materias = [materias]
                for materia in materias:
                    codigo = materia['CodigoMateria']
                    url = votacao_url.format(codigo)
                    sessao_desc = materia['DescricaoIdentificacaoMateria'] \
                        if 'Ementa' in materia else None
                    metadata = {
                        'sessao_id': codigo,
                        'sessao_name': materia[
                            'DescricaoIdentificacaoMateria'
                            ],
                        'sessao_desc': sessao_desc,
                        'sessao_url': url,
                        }
                    yield Request(url, self.parse_votacao,
                                  meta=metadata,
                                  headers={
                                    'Accept': 'application/json'
                                    })

    def parse_votacao(self, response):
        metadata = response.meta
        votacao = json.loads(response.body_as_unicode())['VotacaoMateria']
        materia = votacao['Materia']
        identif_materia = materia['IdentificacaoMateria']
        ano = identif_materia['AnoMateria'][0]
        if 'Votacoes' not in materia:
            return None
        votacoes = materia['Votacoes']['Votacao']
        if isinstance(votacoes, dict):
            votacoes = [votacoes]
        for turno in votacoes:
            date_str = turno['SessaoPlenaria']['DataSessao']
            if 'Votos' not in turno:
                return None
            for parlamentar in turno['Votos']['VotoParlamentar']:
                identif = parlamentar['IdentificacaoParlamentar']
                voto_str = parlamentar['DescricaoVoto'].lower().strip()

                candidato = CandidadoItem()
                candidato_id = identif['CodigoParlamentar']
                candidato['name'] = identif['NomeCompletoParlamentar']
                candidato['partido'] = identif.get('SiglaPartidoParlamentar',
                                                   None)
                candidato['uf'] = identif.get('UfParlamentar', None)
                candidato['ano'] = ano
                candidato['url'] = identif.get('UrlPaginaParlamentar', None)
                candidato['candidato_id'] = candidato_id
                yield candidato

                voto = VotoItem()
                voto['candidato_id'] = candidato_id
                voto['sessao_name'] = metadata['sessao_name']
                voto['sessao_desc'] = metadata['sessao_desc']
                voto['sessao_url'] = metadata['sessao_url']
                voto['sessao_id'] = metadata['sessao_id']
                voto['date'] = datetime.strptime(date_str, '%Y-%m-%d')
                voto['voto'] = {'sim': 1, 'não': -1}.get(voto_str, 0)
                yield voto
