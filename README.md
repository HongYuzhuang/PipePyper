# PipePyper
this module is design to simplify the useage of Process in Python.

## Install:
pip install PipePyper

## Usage :
```python
import re
import bs4
import requests
from PipePyper.PipePyper  import PipeSet,reversePipe,mem_db
from PipePyper.mytools import logger,chainElements
lg=logger('.','test',P=True)

def get_guba_list(page,test ,logger =None):
	url = 'http://guba.eastmoney.com/list,gssz_{}.html'.format(page)
	res=requests.get(url)
	logger.log('finish downLoad page : {}'.format(page))
	test[url] = page
	return url,res.text

def process_page(res,logger = None,cum=None):
	el_class = 'articleh normal_post'
	url,page = res
	soup = bs4.BeautifulSoup(page,'lxml')

	cum[url]= 1
	res = [i.text for  i in soup.find_all('div',{'class':el_class})]
	logger.log('finish process {}'.format(cum))
	return res

def test():
	#happy lambda 
	t = mem_db()
	p = reversePipe(range(100)).mp_map(get_guba_list,3,{'test':t}).mp_map(process_page,2,{},cum=True).chainElements(1).map(lambda x:x.strip('\n'))
	for i in p:
		print(i)
	print(t)
	return None


if __name__=="__main__":

	test()

```