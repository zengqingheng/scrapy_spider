# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector
import re
import json
import requests
from jd_spider.items import JdSpiderItem
from jd_spider.mongoPipeline.getUrl import GetJdUrlList
from jd_spider.settings import DEFAULT_REQUEST_HEADERS
import logging
logging.basicConfig(filename='jdgoods.log',filemode='w',level=logging.ERROR,datefmt='%m/%d/%Y %I:%M:%S %p')
class ClothesSpider(scrapy.Spider):
    name = 'clothes'
    allowed_domains = ['item.jd.com']
    start_urls =GetJdUrlList().getAllUrl()
    #start_urls = ['https://item.jd.com/30217153261.html','https://item.jd.com/31276005125.html','https://item.jd.com/262665088211.html']

    def start_requests(self):
        reqs = []
        for url in self.start_urls:
            req = scrapy.Request(url['url'])
            reqs.append(req)
        return reqs

    def parse(self, response):
        item = JdSpiderItem()
        site = Selector(response)
        item['url'] = response.url
        item['title']= site.xpath('//div[@class="sku-name"]/text()').extract_first().strip()
        item['trade'] = site.xpath('//ul[@id="parameter-brand"]/li/@title').extract_first()
        item['detail']= site.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()').extract()
        colorSize = json.loads(re.search('colorSize:(.*?\])',response.text).group(1))
    #获取sku
        stock_js = 'https://c0.3.cn/stock?skuId=%s&area=1_72_2799_0&cat=1315,1343,9711&extraParam={"originid":"1"}'
        sku_list =[]
        for msg in colorSize:
            sku = {}
            sku['尺码']=msg['尺码']
            try:
                global img_url
                sku['颜色']=msg['颜色']
                img_url = site.xpath('//div[@data-value="%s"]/a/img/@src' % (msg['颜色'])).extract_first()
                print('img_url:',img_url)
                sku['图片'] = get_big_img(img_url)
            except KeyError:
                sku['颜色'] = '无'
                sku['图片'] = site.xpath('//img[@id="spec-img"]/@data-origin').extract_first()
                print('img:',sku['图片'])
            stock_dict = json.loads(requests.get(stock_js%(msg['skuId'])).text)
            sku['库存'] = re.search(">(.*)<",stock_dict['stock']['stockDesc']).group(1)
            sku['价格'] = stock_dict['stock']['jdPrice']['p']

            sku_list.append(sku)
        item['sku_list']=sku_list
        item['count'] = len(colorSize)
        return item

def get_big_img(img_url):
    old_str = "60x76"
    new_str = "350x449"
    return img_url.replace(old_str,new_str,img_url.count(old_str))