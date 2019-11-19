import re
import bs4
import requests
from PipePyper.PipePyper  import PipeSet,reversePipe
from PipePyper.mytools import logger,chainElements
lg=logger('.','test',P=True)

def get_guba_list(page , name =None,logger = None):
	url = 'http://guba.eastmoney.com/list,gssz_{}.html'.format(page)
	res=requests.get(url)
	logger.log('finish downLoad page : {}'.format(page))
	return url,res.text

def process_page(res,name = None,logger = None):
	el_class = 'articleh normal_post'
	url,page = res
	soup = bs4.BeautifulSoup(page,'lxml')
	res = [i.text for  i in soup.find_all('div',{'class':el_class})]
	logger.log('finish process {}'.format(url))
	return res

def test():
	p = reversePipe(range(100)).mp_map(get_guba_list,5).mp_map(process_page,2).chainElements(1).map(lambda x:x.strip('\n'))
	for i in p:
		print(i)
	return None
	# res = p.collect()
	# print(res)

import time

def sleep1(data,name=None,logger=None):
	# lg.log('rc')
	time.sleep(0.5)
	lg.log('send')
	return 'test1!'


def sleep2(data,name=None,logger=None):
	lg.log('receive data')
	time.sleep(0.5)
	return 'test2!'

def test_sleep():

	p = PipeSet(sleep,{},2)
	p.start()
	range(10)>=p
	
	for i in p.g_collect():
		print(i)

def test_reverse():
	for i in reversePipe(range(100)).filter(lambda x:True).mp_map(sleep1,2).mp_map(sleep2,2).filter(lambda x:x):
	# for i in p:
		print(i)


if __name__=="__main__":

	test()
