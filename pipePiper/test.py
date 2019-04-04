# -*- coding: utf-8 -*- 
""" 
Created on 2019-04-04 15:04:32.388880 

@author: 洪宇庄
"""

from mytools import *
from PipeLogger import logger
from pipeTypes import cumPipe,PipeSet,mem_db,adapter,pipe

def T(ip,name=None,logger=None):
	res=(ip+1)*100
	# logger.log(res)
	return res

def test(ip,cum,name=None,logger=None):
	# logger.log(ip)
	cum[ip]=1
	return 1



def test_logger_with_single_pipe():
	cum=mem_db()
	log=logger('test').start()
	cp=pipe(test,{'cum':cum})+log
	cp.run()

	range(100)>=cp
	r=cp.collect()
	print(r)

def test_random_data_extract():
	cum=mem_db()
	log=logger('test').start()
	cp=pipe(test,{'cum':cum},extract_rate=0.5)+log
	cp.run()

	range(10)>=cp
	r=cp.collect()
	print(r)

def test_random_data_with_multiPipes():

	log=logger('test').start()

	ps=PipeSet(T,{},2,static=True,static_val=100)+log
	ps_2=PipeSet(T,{},2,static=True,static_val=100)+log
	cp=cumPipe(test,{})+log
	ps>>ps_2>>cp
	ps.run()

	range(1000)>=ps
	r=cp.collect()
	print(r)


if __name__=='__main__':
	test_random_data_extract()