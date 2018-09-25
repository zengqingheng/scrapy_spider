# scrapy_spider
项目简介：
此项目的目的是从本地的mongodb数据库中获取京东商品的URL，然后抓取商品的详细信息

1、获取数据库中的URL数据
在项目中新建了一个mongoPipeline文件夹，用来操作mongoDB数据库
在jd_spider/mongoPipeline/getUrl.py文件中定义了getAllUrl（）函数
这个函数可以获取所有的url

import pymongo
class GetJdUrlList(object):
    # 1.连接数据库服务器,获取客户端对象
    mongo_client=pymongo.MongoClient('localhost',27017)
    # 2.获取数据库对象
    db=mongo_client.SpiderJdUrl
    # 3.获取集合对象
    collection_jdUrl=db.jd_clothes_url2

    @classmethod
    def getAllUrl(cls):
        cursor = cls.collection_jdUrl.find()
        #print(cursor.count(),type(cursor))
        return cursor

if __name__=="__main__":
    li = GetJdUrlList().getAllUrl()
    for i in li[0:10]:
        print(i['url'])


jd_spider/mongoPipeline/pipeline.py
这个pipeline用户在将数据存入数据库的pipeline
import pymongo
from scrapy.conf import settings

class ClothesPipeline(object):
    def __init__(self):
        # 链接数据库
        self.client = pymongo.MongoClient(host=settings['MONGO_HOST'], port=settings['MONGO_PORT'])
        # 数据库登录需要帐号密码的话
        # self.client.admin.authenticate(settings['MINGO_USER'], settings['MONGO_PSW'])
        self.db = self.client[settings['MONGO_DB']]  # 获得数据库的句柄
        self.coll = self.db[settings['MONGO_COLL']]  # 获得collection的句柄

    def process_item(self, item, spider):
        postItem = dict(item)  # 把item转化成字典形式
        self.coll.insert(postItem)  # 向数据库插入一条记录
        return item  # 会在控制台输出原item数据，可以选择不写
        
2、spider文件，爬虫的主要逻辑全在这个文件里面
这里主要获取的字段是title，trade,detail,sku_list,url,count
sku：最小存货单位，某种商品的大小和颜色组合成一个sku，每个sku的存货状态都不一样
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
    start_urls =GetJdUrlList().getAllUrl() #获取所有的url，进行数据抓取
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
    
3、设置user-agent池以用来反爬，设置后每个请求的User-Agent都是随机的
jd_spider/downloadMiddleware.py
import random
from scrapy.contrib.downloadermiddleware.useragent import UserAgentMiddleware

class MyUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self,user_agent):
        self.user_agent=user_agent
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
           #。。。详细的部分在这个文件里面，也是在网上收集的，可以随便用
        ]
		#设置随机的user-agent
    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        if ua:
            request.headers.setdefault('User-Agent',ua)
