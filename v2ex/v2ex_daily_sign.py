#!/usr/bin/env python
#coding:utf-8

import requests
from bs4 import BeautifulSoup
import re
import ConfigParser
import logging

class V2ex(object):
	def __init__(self):
		self._session = requests.Session()
		self._session.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36',
				'Referer': 'http://www.v2ex.com/signin'}
		self._data = {}
	
	def make_sign_data(self, account):
		signin_req = self._session.get('http://www.v2ex.com/signin')
		signin_bs = BeautifulSoup(signin_req.text, 'lxml')
		username_field = signin_bs.find('input', {'placeholder': '用户名或电子邮箱地址'})['name']
		password_field = signin_bs.find('input', {'type': 'password'})['name']
		once = signin_bs.find('input', {'name': 'once'})['value']
		
		return {
			username_field: account['username'],
			password_field: account['password'],
			'once': once,
			'next': '/'
		}

	def start_sign(self, account):
		self._data = self.make_sign_data(account)
		sigin_res = self._session.post('http://www.v2ex.com/signin', data = self._data)
		daily_req = self._session.get('http://www.v2ex.com/mission/daily')
		
		if u'每日登录奖励已领取' in daily_req.text:
			print account['username'], '已经签过到.'
		else:
			daily_bs = BeautifulSoup(daily_req.text)
			daily_url = daily_bs.find('input', {'value': '领取 X 铜币'})['onclick']
			once = re.search('once=(\d+)', daily_url).group(1)
			daily_res = self._session.get('http://www.v2ex.com/mission/daily/redeem?once=' + once)
			print account['username'], '签到成功!'
		
		last_days = re.search(u'已连续登录 \d+ 天', daily_req.text).group(0).encode('utf-8')
		print last_days

	def sign_process(self):
		config = ConfigParser.ConfigParser()
		config.read('account.conf')
		for user in config.sections():
			account = {}
			account['username'] = config.get(user, 'username')
			account['password'] = config.get(user, 'password')
			self.start_sign(account)

if __name__ == '__main__':
	v2ex = V2ex()
	v2ex.sign_process()
