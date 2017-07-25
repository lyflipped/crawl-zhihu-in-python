'''
Created on Jul 15 2017
author: ihtyc
'''
import urllib.request
import gzip
import re
import sys
import time
import random
import json

#defult directory:'~/desktop/zhihuCrawl'
workSpace = os.path.join(os.path.expanduser('~'), 'desktop', 'zhihuCrawl')
if not os.path.exists(workSpace):
    os.makedirs(workSpace)
#save by the relative path
os.chdir(workSpace)

def getHeaders():
    headers = {}
    #the headers info in file 'headers'
    if not os.path.exists('headers'):
        sys.exit('no headers in %s...' % os.getcwd())

    with open('headers', 'r', encoding='utf8') as fi:
        for line in fi:
            line = line.rstrip()
            if not line:
                continue
            #separate by the first colon
            index = line.find(':')
            headers[line[:index]] = line[index+1:]
    return headers

headers = getHeaders()

def getJson(offset=-1, headers=headers):
    #no print info
    if offset == -1:
        offset = 0
    else:
        print('--- offset: %s...' % offset)

    url = 'https://www.zhihu.com/api/v4/questions/37787176/answers?include=data%5B*%5D.is_normal%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=' + str(offset) + '&limit=20&sort_by=default'

    request = urllib.request.Request(url, data=None, headers=headers)
    response = urllib.request.urlopen(request)
    jsonResult = gzip.decompress(response.read())  
    
    #random float
    time.sleep(random.uniform(1, 2))
    return jsonResult

def parseJson(jsonResult):
    print('parse json...')
    #bytes to str
    js = json.loads(jsonResult.decode('utf-8'))

    imgUrlSet = set()
    invalidImgUrlSet = set()
    skipCount = 0
    for dataDict in js['data']:
        #filter by voteup
        if dataDict['voteup_count'] < 100:
            print('\rskip %s user...' % skipCount, end='')
            continue
        #get the label in js['data']
        result = re.findall('<img .*?>', dataDict['content'])
        for res in result:
            #get the image url from label
            imgRes = re.search('src="(.*?)"', res)
            if imgRes:
                orgImgUrl = imgRes.groups()[0]
                #if the suffix
                if re.search('_.*?(jpg|png|gif|jpeg)$',orgImgUrl):
                    #remove '_.' in the url
                    imgUrl = re.sub('_.*?(jpg|png|gif|jpeg)$', r'.\1', orgImgUrl)
                    imgUrlSet.add(imgUrl)
                else:
                    invalidImgUrlSet.add(orgImgUrl)
    
    print('\ninvalid / valid url: %s / %s...' %\
            (len(invalidImgUrlSet), len(imgUrlSet)))

    return imgUrlSet

def getTotals():
    #total answers
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
        #save image
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
        #if not downloaded yet
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
