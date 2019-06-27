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
            sessao_id = sessao['CodigoSessao']
            sessao_name = sessao['NumeroSessao']
            if 'Materias' in sessao:
                materias = sessao['Materias']['Materia']
                if isinstance(materias, dict):
                    materias = [materias]
                for materia in materias:
                    codigo = materia['CodigoMateria']
                    url = votacao_url.format(codigo)
                    materia_desc = materia['DescricaoIdentificacaoMateria'] \
                        if 'Ementa' in materia else None
                    metadata = {
                        'materia_id': codigo,
                        'materia_name': materia[
                            'DescricaoIdentificacaoMateria'
                            ],
                        'materia_desc': materia_desc,
                        'materia_url': url,
                        'sessao_id': sessao_id,
                        'sessao_name': sessao_name,
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
            sessao_num = turno['SessaoPlenaria']['NumeroSessao']
            sessao_id = turno['SessaoPlenaria']['CodigoSessao']
            date_str = turno['SessaoPlenaria']['DataSessao']
            if 'Votos' not in turno:
                return None
            for parlamentar in turno['Votos']['VotoParlamentar']:
                identif = parlamentar['IdentificacaoParlamentar']
                voto_str = parlamentar['DescricaoVoto'].lower().strip()
                candidato_id = identif['CodigoParlamentar']

                voto = VotoItem()
                voto['candidato_id'] = candidato_id
                voto['candidato_name'] = identif['NomeCompletoParlamentar']
                voto['candidato_part'] = identif.get(
                    'SiglaPartidoParlamentar', None)
                voto['candidato_uf'] = identif.get('UfParlamentar', None)
                voto['proposition_id'] = metadata['materia_id']
                voto['proposition_name'] = metadata['materia_name']
                voto['sessao_desc'] = sessao_id
                voto['sessao_id'] = sessao_num
                voto['date'] = datetime.strptime(date_str, '%Y-%m-%d')
                voto['voto'] = {'sim': 1, 'não': -1}.get(voto_str, 0)
                yield voto
