# -*- coding: utf-8 -*- 
""" 
Created on 2019-04-04 15:19:30.419244 

@author: 洪宇庄
"""


class endSignal(Exception):
	""" 
	管道数据结束信号 
	"""
	pass
class filteredData(Exception):
	"""
		管道数据流过滤
		在传入函数内引用
	"""
	pass