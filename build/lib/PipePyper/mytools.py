# -*- coding: utf-8 -*- 
""" 
Created on 2019-08-29 13:59:47.428778 

@author: 洪宇庄
"""

import datetime

class Inf(int):
    def __add__(self,other):
        return self
    def __sub__(self,other):
        return self
    def __eq__(self,other):
        if other.__class__==self.__class__:
            return True
        else:
            return False
    def __gt__(self,other):
        return True
    def __lt__(self,other):
        return False    
    def __ge__(self,other):
        return True
    def __le__(self,other):
        return False  
        
class logger(object):
    def __init__(self,logpath,name=None,P=False,level='MSG'):

        self.level_d={'MSG':1,'DEBUG':0,'ERROR':2,'LOG':1}

        self.logpath=logpath
        self.perfix=now
        if name:
            self.name=name
        else:
            self.name=""
        self.P=P
        self.level=level
    def log(self,msg,exp='LOG'):
        if self.level_d[self.level]<=self.level_d[exp]:
            with open(self.logpath+'/log_{}_{}'.format(self.name,parseDate(now())),'a',encoding='utf') as F:
                msg="{}   {}    : {} \n".format(self.perfix(),exp,msg)
                if self.P:
                    print(msg)
                F.write(msg)
    def msg(self,msg):
        self.log(msg,'MSG')
    def error(self,msg):
        self.log(msg,'ERROR')
    def debug(self,msg):
        self.log(msg,'DEBUG')



def parseDate(Date,format=0):
    #format  0 '2017-01-01'
    #format  1 '20170101'
    #gormat  2 '2017-01-01 00:00:00'
    #forward 0 string to date
    #forward 1 date to string
    F={0:'%Y-%m-%d',1:'%Y%m%d',2:'%Y-%m-%d %H:%M:%S'}
    W={0:datetime.datetime.strptime,1:datetime.datetime.strftime}
    PT={'\d{4}-\d{2}-\d{2}':0,'\d{8}':1,'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}':2}
    if Date.__class__==str:
        try:
            format=max([PT[i] for i in PT if re.match(i,Date)])
        except Exception:
            raise DatePatternException
        forward=0
    elif Date.__class__==datetime.datetime:
        forward=1
    else:
        raise FormatException
    return W[forward](Date,F[format])

def now():
    return datetime.datetime.now()

def timeAJ(delta=0,date=None):
    if not date:
        date=datetime.datetime.now()
    return date+datetime.timedelta(delta)

def GetCalendar(StartDay,EndDay=parseDate(timeAJ()),format=1):
    return [ parseDate(timeAJ(-i,parseDate(EndDay)),format) for i in range((parseDate(EndDay)-parseDate(StartDay)).days+1)]
  
  

def chainElements(In_iterable,Require_Depth=Inf()):
    for i in In_iterable:
        if Require_Depth>0 and (getattr(i,'__iter__',None)!=None):
            for j in  chainElements(i,Require_Depth-1):
                yield j
        else:
            yield i