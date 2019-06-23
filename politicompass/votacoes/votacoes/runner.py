import scrapy
from scrapy.crawler import CrawlerProcess
import votacoes

process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
})

process.crawl(votacoes.spiders.CamaraDeputados)
process.start()