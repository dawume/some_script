#!/usr/bin/env python
#coding:utf-8

import requests
from bs4 import BeautifulSoup
import re
import ConfigParser
import datetime
import time

import smtplib
from email.mime.text import MIMEText

class SmzdmJd(object):
	def __init__(self):
		self._session = requests.Session()
		self._session.headers.update(
				{'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'}
				)
		self._data = {}
		self._last_time = 0
		self._max_time = 0
		self._price_thr = 0.0

	def get_time(self, item):
		time_field = item.address.span.get_text()
		item_time = datetime.datetime.now()

		if time_field == u'刚刚':
			pass

		elif re.search(u'(\d+)分钟前', time_field):
			minite_ago = int(re.search(u'(\d+)分钟前', time_field).group(1))
			item_time = (item_time - datetime.timedelta(seconds = minite_ago * 60))

		elif re.search('(\d+):(\d+)', time_field):
			cur_hour, cur_minite = re.search('(\d+):(\d+)', time_field).groups()
			item_time = item_time.replace(hour = int(cur_hour), minute = int(cur_minite))

			if re.search('(\d+)-(\d+)', time_field):
				cur_month, cur_day = re.search('(\d+)-(\d+)', time_field).groups()
				item_time = item_time.replace(month = int(cur_month), day = int(cur_day))
		
		else:
			print 'err, use current time'
			pass

		time_stamp = int(time.mktime(item_time.timetuple()))
		return time_stamp

	def get_price(self, item):
		price_field = item.find('div', {'class': 'tips'}).em.get_text().encode('utf-8')
		return float(re.search(r'([\d\.]+)元', price_field).group(1))

	def get_title(self, item):
		title = item.h2.get_text().encode('utf-8').strip()
		return title

	def get_url(self, item):
		url = item.a['href']
		sid = re.search(r'/(\d+)', url)
		return sid.expand(r'http://www.smzdm.com/p/\1/')

	def get_jd_item(self, item):
		if u'京东' in item.get_text():
			timestamp = self.get_time(item)
			price = self.get_price(item)
			title = self.get_title(item)
			url = self.get_url(item)
			return [title, price, url, timestamp]
		else:
			return None

	def parser(self):
		config = ConfigParser.ConfigParser()
		config.read('jd.conf')
		self._last_time = config.getint('jd', 'lasttime')
		self._price_thr = config.getfloat('jd', 'price_thr')

		subject = ''
		contents = ''
		# url = 'http://m.smzdm.com/tag/%E7%99%BD%E8%8F%9C%E5%85%9A/youhui/'
		url = 'http://m.smzdm.com/youhui/'

		page = self._session.get(url)
		bs = BeautifulSoup(page.text, 'lxml')
		item_list = bs.find(class_ = 'list list_preferential')
		for item in item_list.find_all('li'):
			result = self.get_jd_item(item)
			if result and result[1] <= self._price_thr and result[-1] > self._last_time:
				if not subject:
					subject += 'smzdm_jd 白菜 %s 等' % (result[0])
				contents += '%s\t\t%.2f元\t\t%s\n ' % (result[0], result[1], result[2])

				if self._max_time < result[-1]:
					self._max_time = result[-1]

		return (subject, contents)


	def send_mail(self, subject, contents, with_debug = 0):
		config = ConfigParser.ConfigParser()
		config.read('mail.conf')
		username = config.get('mail_user', 'username')
		password = config.get('mail_user', 'password')
		smtpserver = config.get('mail_user', 'smtpserver')
		mailto_list = []
		for user, mailto in config.items('mailto_list'):
			mailto_list.append(mailto)
		
		msg = MIMEText(contents, 'plain', 'utf-8')
		msg['Subject'] = subject
		msg['From'] = '%s <%s>' % (re.search('(.*)@', username).group(1), username)
		msg['To'] = '%s' % (';'.join(mailto_list))

		server = smtplib.SMTP(smtpserver)
		server.set_debuglevel(with_debug)
		server.login(username, password)
		server.sendmail(username, mailto_list, msg.as_string())
		server.quit()

	def update_timestamp(self):
		config = ConfigParser.ConfigParser()
		config.read('jd.conf')
		self._last_time = config.set('jd', 'lasttime', self._max_time)
		with open('jd.conf', 'wb') as configfile:
			config.write(configfile)

	def do_process(self):
		subject, contents = self.parser()

		if subject:
			self.send_mail(subject, contents)
			self.update_timestamp()
		else:
			print 'no new item found'

if __name__ == '__main__':
	jd = SmzdmJd()
	jd.do_process()
