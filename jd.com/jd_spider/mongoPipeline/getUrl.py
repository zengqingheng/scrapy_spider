# -*- coding: utf-8 -*-
# @Time    : 2018/9/25 0:22
# @Author  : ZengQingheng
# @Email   : 1107753149@qq.com
# @File    : getUrl.py
# @Software: PyCharm
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
# if __name__=="__main__":
#     urlList = GetJdUrlList()
#     urlList.getAllUrl()