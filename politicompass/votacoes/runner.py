from scrapy.cmdline import execute

try:
    execute(
        [
            'scrapy',
            'crawl',
            'camara_deputados',
            '-o',
            'out.csv',
        ]
    )
except SystemExit:
    pass