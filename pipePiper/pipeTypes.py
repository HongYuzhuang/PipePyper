# -*- coding: utf-8 -*- 
""" 
Created on 2019-04-04 15:19:40.729834 

@author: 洪宇庄
"""

import sys
import time
import random

from functools import partial

from PipeLogger import logger
from PipeException import endSignal,filteredData
# from PipeLogger import logger
# from PipeException import endSignal,filteredData

import multiprocessing
from multiprocessing import Process,Queue,Manager

class pipe(object):
	def __init__(self,t_func,c_data,cache_size=0,timeout=10,try_Count=10,extract_rate=1):
		"""
			timeout	,管道等待超时时长
			ot_q	,输出队列
			ip_q	,输入队列
			s		,source
			t		,target
			ps		,process ID
			try_Count,输出拥塞时重试次数
			notice	,是否通知下游任务结束
		"""
		self.t_func=t_func
		self.c_data=c_data
		self.timeout=timeout

		self.ot_q=Queue(cache_size)
		self.ip_q=Queue(cache_size)
		self.s=None
		self.t=None
		self.ps=None
		self.logger=None
		self.warn_queue=None

		self.try_Count=try_Count
		self.extract_rate=extract_rate
	def end(self):
		self.ip_q.put(endSignal())
		self.ot_q.put(endSignal())
		raise Exception('closs pipe')
	def pipeLoop(self):
		"""
			循环体
			-阻塞等待上游管道结果
			-##新增预警:拥塞重传时 若存在 主控器,向主控器报告重传次数
			-接受endSignal 结束循环
		"""
		if self.ps ==None:
			raise Exception('no actived pipe')
		while(True):
			data=self.ip_q.get()
			if data==None:
				continue
			elif data.__class__!=endSignal:
					if self.extract_rate<1:
						if random.random()>self.extract_rate:
							continue
					r=self.t_func(data,**self.c_data,name=self.ps._name,logger=self.logger)
					count=0
					while(count<self.try_Count):
						try:
							self.ot_q.put(r,timeout=self.timeout)
							break
						except Exception:
							count+=1
							if count > (self.try_Count//2):
								if self.warn_queue !=None:
									self.warn_queue.put(count)
							time.sleep((self.timeout*count//10+1)**2)
					if count==self.try_Count:
						self.ip_q.put(data)
			elif data.__class__==filteredData:
				continue
			else:
				try:
					self.end()
				except Exception:
					break

	def __lt__(self,iterable):
		"""
			从管道输入数组
		"""
		if getattr(iterable,'__iter__',None)!=None:
			for i in iterable:
				self.ip_q.put(i)
		else:
			raise Exception('insert iterable plz')
	def __le__(self,iterable):
		"""
			从管道输入数组 追加结束符
		"""
		if self.ps ==None:
			raise Exception('no actived pipe')

		iterable>self
		self.ip_q.put(endSignal())
	def __lshift__(self,other):
		""" 
			重载 << 运算符,连接前序管道 或者缓冲队列 self<< other
		"""
		if isinstance(other,pipe):
			self.s=other
			other.t=self
			self.ip_q=other.ot_q
			return other
		elif other.__class__==multiprocessing.queues.Queue:
			self.ip_q=other
			return self
		else:
			raise Exception('Not Correct PipeLine Format')
	def __rshift__(self,other):
		"""
			重载 >> 运算符,连接后序管道 或者缓冲队列 self>>other
		"""
		if isinstance(other,pipe) :
			self.t=other
			other.s=self
			other.ip_q=self.ot_q
			return other	
		elif other.__class__==multiprocessing.queues.Queue:
			self.ot_q=other
			return self
		else:
			raise Exception('Not Correct PipeLine Format')
	def collect(self,format=list,log_fin=False):
		"""
			收集计算结果;
			log_fin 为真将关闭日志流
		"""
		if self.ps ==None:
			raise Exception('no actived pipe')

		if self.t ==None:
			if format==list:
				R=[] 
				insert_func=R.append
			r=None
			while(r.__class__!=endSignal):
				try:
					r=self.ot_q.get(timeout=self.timeout)
					if r.__class__!=endSignal:
						insert_func.__call__(r)	
				except Exception:
					break
			if log_fin and self.logger!=None:
				self.logger.end()
				self.logger.wait()
			return R
		else:
			return self.t.collect(format)
	def start(self):
		"""
			启动函数,可重载
		"""		
		self.ps=Process(target=self.pipeLoop,daemon=True)
		self.ps.start()
	def run(self):
		"""
			链式启动
		"""
		self.start()
		if self.t!=None:
			if self.t.ps ==None:
				self.t.run()
		if self.s!=None:
			if self.s.ps ==None:
				self.s.run()
		return self.ps
	def __add__(self,other):
		"""
			连接logger
		"""
		if other.__class__==logger:
			self.logger=other
			return self
		else:
			raise Exception('required a logger')
	def wait(self,timeout=None):
		if self.ps ==None:
			raise Exception('no actived pipe')
		self.ps.join(timeout)
	# def close(self):
	# 	self.ip_q.put(endSignal())
	# 	return 1
	# def shutdown(self):
	# 	self.close()
	# 	self.join(timeout=10)
	# 	if self.ps.is_alive():
	# 		self.ps.terminate()
	def init(t_func,c_data,cache_size=1000,timeout=10,try_Count=10,extract_rate=1):
		return pipe(t_func,c_data,cache_size,timeout,try_Count,extract_rate)

class cumPipe(pipe):
	def __init__(self,*args,**wargs):
		super(self.__class__,self).__init__(*args,**wargs)
		self.cum={}
	def end(self):
		self.ip_q.put(endSignal())
		self.ot_q.put(endSignal())
		raise Exception('closs pipe')
	def pipeLoop(self):
		"""
			循环体
			-阻塞等待上游管道结果
			-##新增预警:拥塞重传时 若存在 主控器,向主控器报告重传次数
			-接受endSignal 结束循环
		"""
		if self.ps ==None:
			raise Exception('no actived pipe')
		while(True):
			data=self.ip_q.get()
			if data==None:
				continue
			elif data.__class__!=endSignal:
					if self.extract_rate<1:
						if random.random()>self.extract_rate:
							continue

					self.t_func(data,**self.c_data,name=self.ps._name,logger=self.logger,cum=self.cum)
			elif data.__class__==filteredData:
				continue
			else:
				self.ot_q.put(self.cum,timeout=self.timeout)
				try:
					self.end()
				except Exception:
					break
	
class PipeSet(pipe):
	"""
		管道子类 ：管道组
		-- 替换单个管道使用
	"""
	def __init__(self,t_func,c_data,p_num,cache_size=0,timeout=10,try_Count=10,extract_rate=1,static_val=1000,static=False):
		""" 
			--调用父类构造函数
			--pipes	: 初始化一组管道
		# """
		self.extract_rate=extract_rate
		super(self.__class__,self).__init__(t_func,c_data,cache_size=cache_size,timeout=timeout,try_Count=try_Count,extract_rate=self.extract_rate)
		self.genPipe=partial(pipe.init,t_func=t_func,c_data=c_data,cache_size=cache_size,timeout=timeout,try_Count=try_Count,extract_rate=extract_rate)
		self.static_val=static_val
		self.p_num=p_num
		self.pipes=[self.genPipe() for i in range(p_num)]
		self.adapter=adapter(self,static)
		self.ot_q=self.adapter.ot_q
		#
	def bind(self):
		for p in self.pipes:
			self.bind_one(p)
	def bind_one(self,p):
		"""
			绑定输入输出
			绑定logger
		"""
		p<<self.ip_q
		p>>self.adapter.ip_q

		if self.logger:
			p+self.logger
			self.adapter+self.logger
		return p
	def start(self):
		self.bind()
		self.ps=[i.run() for i in self.pipes]
		self.adapter.run()

class adapter(pipe):
	def lineFunc(self,ip,name,logger):
		r=ip
		if self.static:
			self.processed_num+=1
			if self.processed_num%self.static_val==0:
				ot=self.lt
				self.lt=time.time()
				if self.logger:
					self.logger.log( "pv : {}/s" .format(self.static_val/(self.lt-ot)))
		return r
	def __init__(self,pipeset,static=True):
		super(self.__class__,self).__init__(t_func=self.lineFunc,c_data={},cache_size=0)
		self.pipeset=pipeset
		self.check_count=0
		self.processed_num=0
		self.p_num=pipeset.p_num
		self.ip_q=pipeset.ot_q
		self.static_val=self.pipeset.static_val
		self.lt=time.time()
		self.static=static
	def end(self):
		self.check_count+=1
		if self.logger!=None:
			self.logger.log(' {}/{}'.format(self.check_count,self.p_num))
		if self.check_count==self.p_num:
			self.ot_q.put(endSignal())
			self.ip_q.put(endSignal())
			raise Exception('Task Done')
def mem_db():
	return Manager().dict()

class multiFunc_wrapper(object):
	def wrapper(self,*args,name=None,logger=None,**kwargs):
		res=self.func(*args,**kwargs)
		return res
	def __call__(self,func):
		self.func=func
		return self.wrapper


if __name__=="__main__":
	# log=logger().start()
	Test={}
	cp=cumPipe(test,{'cum':Test})
	cp.run()

	range(10)>=cp
	r=cp.collect()
	print(r)


