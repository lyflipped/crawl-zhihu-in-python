#coding=utf8
'''
Created on Jul 15 2017
author: ihtyc
description: parse json of zhihu question-37787176 to get image url, and download
'''
import urllib.request
import urllib.parse
import lxml.etree
import http.cookiejar
import gzip
import re
import os
import time
import random
import json
import sys

#设置存储目录
workSpace = os.path.join(os.path.expanduser('~'), 'desktop', 'zhihu')
if not os.path.exists(workSpace):
    os.makedirs(workSpace)
#以相对路径存储图片
os.chdir(workSpace)

def getHeaders():
    headers = {}
    #将请求头放在文件headers中
    if not os.path.exists('headers'):
        sys.exit('no headers in %s...' % os.getcwd())

    with open('headers', 'r', encoding='utf8') as fi:
        for line in fi:
            #去'\n'
            line = line.rstrip()
            #空行
            if not line:
                continue
            #以第一个冒号为断点读取数据
            index = line.find(':')
            headers[line[:index]] = line[index+1:]
    return headers

headers = getHeaders()

def getJson(offset=-1, headers=headers):
    #自定义当offset为-1时访问offset=0的json，仅用于getTotals，不打印输出信息
    if offset == -1:
        offset = 0
    else:
        print('--- offset: %s...' % offset)
    
    #如果URL请求方法为POST，一般会附加数据，并且对数据进行编码
    #data = {}
    #data = urllib.parse.urlencode(data)

    url = 'https://www.zhihu.com/api/v4/questions/37787176/answers?include=data%5B*%5D.is_normal%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=' + str(offset) + '&limit=20&sort_by=default'

    request = urllib.request.Request(url, data=None, headers=headers)
    response = urllib.request.urlopen(request)
    #从Request headers中的Accept-Encoding:gzip, deflate, br可以发现请求的数据经过gzip压缩
    jsonResult = gzip.decompress(response.read())  
    
    #返回浮点随机数
    time.sleep(random.uniform(1, 2))
    return jsonResult

def parseJson(jsonResult):
    print('parse json...')
    #response返回数据为字节型数据，需要进行解码为str类型的数据
    js = json.loads(jsonResult.decode('utf-8'))

    imgUrlSet = set()
    invalidImgUrlSet = set()
    #一个Json中有20个用户的数据，从每个用户中获取其中图片的URL
    skipCount = 0
    for dataDict in js['data']:
        #以点赞数过滤
        if dataDict['voteup_count'] < 100:
            print('\rskip %s user...' % skipCount, end='')
            continue
        #在json['data']中，图片是以标签的格式嵌入的，先提取标签
        result = re.findall('<img .*?>', dataDict['content'])
        for res in result:
            #再从标签中提取URL
            imgRes = re.search('src="(.*?)"', res)
            if imgRes:
                orgImgUrl = imgRes.groups()[0]
                #判断URL是否为以图片格式为后缀
                if re.search('_.*?(jpg|png|gif|jpeg)$',orgImgUrl):
                    imgUrl = re.sub('_.*?(jpg|png|gif|jpeg)$', r'.\1', orgImgUrl)
                    imgUrlSet.add(imgUrl)
                else:
                    invalidImgUrlSet.add(orgImgUrl)
    
    print('\ninvalid / valid url: %s / %s...' %\
            (len(invalidImgUrlSet), len(imgUrlSet)))

    return imgUrlSet

def getTotals():
    #从json中直接获得总回答数目
    print('--- totals: ', end='')
    js = json.loads(getJson().decode('utf-8'))
    totals = js['paging']['totals']
    print('%s...' % totals)
    return totals

def saveImg(imgUrl, imgName):
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
    }
    request = urllib.request.Request(imgUrl, data=None, headers=headers)
    try:
        response = urllib.request.urlopen(request)
        res = response.read()
        #返回的数据为字节数据，直接以2进制写入即可
        with open(imgName, 'wb') as fi:
            fi.write(res)
    except:
        with open('log', 'a') as fi:
            fi.write('except in %s\n' % imgUrl)
    
    time.sleep(random.uniform(1, 2))

def download(imgUrlSet):
    imgSet = set(os.listdir(os.getcwd()))

    count = 0
    new = 0
    print('download %s has %s new...' % (count, new), end='')
    
    for imgUrl in imgUrlSet:
        count += 1
        imgName = imgUrl.split('/')[-1]
        if imgName not in imgSet:
            new += 1
            imgSet.add(imgName)
            saveImg(imgUrl, imgName)
            print('\rdownload %s has %s new...' % (count, new), end='')

    print('')

def process():
    totals = getTotals()
    offset = 0
    while offset < totals:
        download(parseJson(getJson(offset)))
        offset += 20

if __name__ == '__main__':
    process()
