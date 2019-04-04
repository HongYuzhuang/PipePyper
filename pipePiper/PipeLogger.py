# -*- coding: utf-8 -*- 
""" 
Created on 2019-04-04 15:19:34.809495 

@author: 洪宇庄
"""

import os
import sys
import datetime

from multiprocessing import Process,Queue
from mytools import timeAJ,parseDate
from PipeException import endSignal
# from PipeException import endSignal

class logger(object):
	""" 
		pipepyper 专用 logger 类
		启动进程,派发
	"""
	def __init__(self,path=None):
		self.path=path
		self.q=Queue()
	def i(self):
		"""
			初始化
		"""
		if self.path==None:
			self.io=sys.stdout
		else:
			path ,file_name = os.path.split(self.path)
			self.io=open( os.path.join( path,'log_{}_{}.log'.format(file_name,parseDate(timeAJ()))),'a')
	def log(self,msg):
		"""
			对外提供包装后的队列插入
		"""
		self.q.put(msg)
	def log_loop(self):
		"""
			循环体
			-接受消息输入
		"""
		self.i()
		while(True):
			try:	
				msg=self.q.get(timeout=5)
				if msg.__class__==endSignal:
					raise Exception('received End signal')
				else:
					self.io.write('at {} msg:{} \n'.format(datetime.datetime.now(),msg))
					self.io.flush()
			except Exception as E:
				self.log('End logging')
				break
	def start(self):
		"""
			启动消息循环
		"""
		self.ps=Process(target=self.log_loop,daemon=True)
		self.ps.start()
		return self
	def wait(self):
		"""
			等待日志打印完成
		"""
		self.ps.join()
	def end(self):
		"""
			结束任务
		"""
		self.q.put(endSignal())