# -*- coding: utf-8 -*- 
""" 
Created on 2019-04-04 15:19:40.729834 

@author: 洪宇庄
"""

import sys
import time
import random

from functools import partial,reduce
from .mytools import parseDate,timeAJ,logger,chainElements

import multiprocessing
from multiprocessing import Process,Queue,Manager

class endSignal(Exception):
	""" 
	管道数据结束信号 
	"""

	def __str__(self):
		return 'endSig'
class filteredData(Exception):
	"""
		管道数据流过滤
		在传入函数内引用
	"""
	pass

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

		self.name = str(int(random.random()*100))

		self.add_logger  = 'logger' in t_func.__code__.co_varnames

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
		return True
	def pipeLoop(self):
		"""
			循环体
			-阻塞等待上游管道结果
			-##新增预警:拥塞重传时 若存在 主控器,向主控器报告重传次数
			-接受endSignal 结束循环
		"""
		end_flag=False
		if self.ps ==None:
			raise Exception('no actived pipe')

		while(not (self.ip_q.empty() and end_flag )  ):
			data=self.ip_q.get()
			# self.logger.log('{},{} get : {}'.format(self.__class__,self.name,data))
			if data.__class__ not in ( endSignal,filteredData):
					if self.extract_rate<1:
						if random.random()>self.extract_rate:
							continue
					if self.add_logger:
						r=self.t_func(data,**self.c_data,logger=self.logger)
					else:
						r=self.t_func(data,**self.c_data)

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
			
			elif data.__class__ == endSignal:
				end_flag =self.end()
		
		self.ot_q.put(endSignal())

	def __lt__(self,iterable):
		"""
			从管道输入数组
		"""
		if getattr(iterable,'__iter__',None)!=None:

			for i in iterable:
				# self.logger.log('input {} into :{} ,'.format(i,self.name))
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

	def collect(self,format=list):
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
			
			return R
		else:
			return self.t.collect(format)

	def g_collect(self):
		'''
			收集计算结果,以生成器方式收集:
		'''
		if self.ps ==None:
			raise Exception('no actived pipe')

		if self.t ==None:
			r=None
			while(r.__class__!=endSignal):
				try:
					r=self.ot_q.get(timeout=self.timeout)
					if r.__class__!=endSignal:
						yield r
				except Exception:
					break
		else:
			return self.t.g_collect(format)

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
		if isinstance(other,logger):
			self.logger=other
			return self
		else:
			raise Exception('required a logger')
	def wait(self,timeout=None):
		if self.ps ==None:
			raise Exception('no actived pipe')
		self.ps.join(timeout)

	def init(cl,t_func,c_data,cache_size=1000,timeout=10,try_Count=10,extract_rate=1):
		return cl(t_func,c_data,cache_size,timeout,try_Count,extract_rate)

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
			# if data==None:
			# 	continue
			if data.__class__ not in (endSignal,filteredData):
					if self.extract_rate<1:
						if random.random()>self.extract_rate:
							continue

					self.t_func(data,**self.c_data,logger=self.logger,cum=self.cum)
			elif data.__class__==filteredData:
				continue
			
			elif data.__class__==endSignal:
				# self.ot_q.put(self.cum,timeout=self.timeout)
				try:
					self.end()
				except Exception:
					break
	
class PipeSet(pipe):
	"""
		管道子类 ：管道组
		-- 替换单个管道使用
	"""
	def __init__(self,t_func,c_data,p_num,cache_size=100,timeout=10,try_Count=10,extract_rate=1,static_val=1000,static=False,cum=False):
		""" 
			--调用父类构造函数
			--pipes	: 初始化一组管道
		# """
		# print(static)
		self.extract_rate=extract_rate
		super(self.__class__,self).__init__(t_func,c_data,cache_size=cache_size,timeout=timeout,try_Count=try_Count,extract_rate=self.extract_rate)
		self.genPipe=partial(pipe.init,cl=(cumPipe if cum else pipe),t_func=t_func,c_data=c_data,cache_size=cache_size,timeout=timeout,try_Count=try_Count,extract_rate=extract_rate)
		self.static_val=static_val
		self.p_num=p_num
		self.pipes=[self.genPipe() for i in range(p_num)]
		# print((cumPipe if cum else pipe))
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
	def lineFunc(self,ip,logger=None):
		r=ip
		if self.static:
			self.processed_num+=1
			if self.processed_num%self.static_val==0:
				ot=self.lt
				self.lt=time.time()
				if logger:
					logger.log( "pv : {}/s" .format(self.static_val/(self.lt-ot)))
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

		if self.check_count>=self.p_num:
			return True
		else:
			return  False
			# self.ot_q.put(endSignal())
			# raise Exception('Task Done')

def mem_db():
	return Manager().dict()

class multiFunc_wrapper(object):
	def wrapper(self,*args,name=None,logger=None,**kwargs):
		res=self.func(*args,**kwargs)
		return res
	def __call__(self,func):
		self.func=func
		return self.wrapper

from itertools import groupby
class simple_logger(logger):

	def __init__(self,*args,**kwargs):
		pass

	def log(self,msg):
		print(msg)



def sort_and_groupby(I,key):
	return groupby(sorted(I,key=key),key=key)

def ft_timer(logger,val):
	def kwrapper(func):
		def warpper(*args,**wargs):
			time_s=time.time()
			r=func(*args,**wargs)
			time_e=time.time()
			df = time_e-time_s
			if df>val:
				logger.log('costs :{} '.format(df))
			return r
		return warpper
	return kwrapper
def shards(ITER,shard_size):
	tmp_pack = []

	for I in ITER:
		if len(tmp_pack)<shard_size:
			tmp_pack.append(I)
		else:
			yield tmp_pack
			tmp_pack=[]
	if tmp_pack:
		yield tmp_pack

class reversePipe(object):
	def __init__(self,pipe,lg=None):
		self.pipe=pipe
		self.func=None
		self.tlg= ft_timer(simple_logger(),0.01)
		self.lg = lg

	def sort_and_groupby(self,key):
		return reversePipe(sort_and_groupby(iter(self),key=key),self.lg)

	def shardby(self,size):
		return reversePipe(shards(iter(self),shard_size= size),self.lg )
	def show(self):
		def s(data):
			print(data)
			return data
		return self.map(s)
	def zip(self,Iter):
		return reversePipe(zip(iter(self),Iter),self.lg)
	def enumerate(self):
		return reversePipe(enumerate(iter(self),self.lg))
	def tm_map(self,func):
		return reversePipe(map(lambda x:self.tlg(func)(x),iter(self)),self.lg)
	def map(self,func):
		return reversePipe(map(lambda x:func(x),iter(self)),self.lg)
	def mp_map(self,func,num=10,c_data ={},cum=False,**kwargs):
		'''
			多进程
		'''
		# print(kwargs)
		self.func=func
		ps = PipeSet(self.func,c_data,num,timeout=None,cum=cum,**kwargs)+(self.lg if self.lg else simple_logger())

		return mp_reverse_pipe(ps,self,self.lg)
	def filter(self,func):
		return reversePipe(filter(lambda x:func(x),iter(self)),self.lg)
	def reduce(self,func,init=None):
		if init:
			res= reduce(func,iter(self),init)
		else:
			res= reduce(func,iter(self))
		if getattr(res,'__iter__',None)==None:
			res= [res]
		# else:
		return reversePipe(res,self.lg)


	def __iter__(self):
		# print(self.pipe)
		return self.pipe.__iter__()
		# else:
			# return self.pipe
	def collect(self):
		return list(self)
	def chainElements(self,p_level):
		return reversePipe(chainElements(iter(self),p_level) ,self.lg)

	def sort(self,key,reverse=True):
		return reversePipe(sorted(iter(self),key=key,reverse=reverse),self.lg)
	def activate(self):
		pass


class mp_reverse_pipe(reversePipe):
	def __init__(self,ps,src=None,lg=None):
		self.pipe=ps
		self.src=src
		self.lg= lg 
	def activate(self):
		self.pipe.run()

		if isinstance(self.src,reversePipe):
			self.src.activate()


		if self.src.__class__!=mp_reverse_pipe :
			self.src.pipe >= self.pipe
		# else:
			# print(self)
			# print(self.src)

	def mp_map(self,func,num,c_data={},cum=False,**kwargs):
		'''
			多进程
		'''
		# print(kwargs)
		self.func=func
		ps = PipeSet(self.func,c_data,num,timeout=None,cum=cum,**kwargs)+(self.lg if self.lg else simple_logger())
		# ps.run()
		self.pipe>>ps
		# print('connect!')
		return mp_reverse_pipe(ps,self,self.lg)
	def __iter__(self):
		# print(self.pipe)
		self.activate()
		print('fully connected')
		return self.pipe.g_collect()



if __name__=="__main__":
	# log=logger().start()
	Test={}
	cp=cumPipe(test,{'cum':Test})
	cp.run()

	range(10)>=cp
	r=cp.collect()
	print(r)


