#!/usr/bin/env python
#coding:utf-8

import requests
from bs4 import BeautifulSoup
import re
import ConfigParser
import json

class Qsbk(object):
	def __init__(self):
		self._session = requests.Session()
		headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
        }
		self._session.headers.update(headers)
	
	def process(self):
		fw = open('qsbk.txt', 'wb')

		for i in xrange(1000):
			url = 'http://www.qiushibaike.com/hot/page/%d/' % (i)
			page = self._session.get(url)

			bs = BeautifulSoup(page.text.encode('utf-8'), "lxml")

			for item in bs.find_all(class_ = 'article block untagged mb15'):
				if item.find(class_ = 'thumb'):
					continue
				
				record = {}
				try:
					record['username'] = item.h2.string
					record['jokeid'] = item['id']
					record['content'] = item.find(class_ = 'content').get_text()
					record['likes'] = item.find(class_ = 'stats-vote').i.string
					record['comments'] = item.find(class_ = 'stats-comments').i.string
					fw.write('%s\n' % json.dumps(record))
				except:
					continue

			print 'page %d done' % (i)

		fw.close()

if __name__ == '__main__':
	qsbk = Qsbk()
	qsbk.process()
