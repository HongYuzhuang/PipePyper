# PipePyper
this module is design to simplify the useage of Process in Python.

## Install:
pip install PipePyper

## Usage :
```python

import re
import time
import bs4
import requests
from PipePyper.PipePyper  import PipeSet,reversePipe,mem_db
from PipePyper.mytools import logger,chainElements
lg=logger('.','test',P=False)

def get_guba_list(page,logger =None):
	url = 'http://guba.eastmoney.com/list,gssz_{}.html'.format(page)
	res=requests.get(url)
	logger.log('finish downLoad page : {}'.format(page))
	# test[url] = page

	return url,res.text
	# return None
def s(data):
	return data
def process_page(res,logger = None):
	el_class = 'articleh normal_post'
	url,page = res
	soup = bs4.BeautifulSoup(page,'lxml')

	res = [i.text for  i in soup.find_all('div',{'class':el_class})]
	logger.log('finish process {}'.format(url))
	return res

def test_1(data,logger=None):
	logger.log('get {}'.format(data))
	time.sleep(0.1)
	logger.log('send {}'.format(data))
	return data

def test_2(data):
	time.sleep(0.1)
	return data

def test_case():
	t = mem_db()

	p = reversePipe(range(5),lg).mp_map(get_guba_list,1).mp_map(s,1).mp_map(process_page,1,{}).chainElements(1).map(lambda x:x.strip('\n'))
	
	for i in p:
		print(i)
	# print(t)
	return None

def test():

	p = reversePipe(range(40)).mp_map(test_1,4).mp_map(test_1,4).mp_map(test_1,4)#.mp_map(test_1,1,{})
	
	for i in p:
		print(i)
	# print(t)
	return None


if __name__=="__main__":
	test()
```