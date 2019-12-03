from urllib import parse
import requests
import datetime
import time
import sqlite3
import csv
import logging
#检查路径是否是文件
import pathlib
import os
from pushBearConf import sendPushBear
from ctypes import cdll

_SH_DENYRW = 0x10

class RunTask(object):
    def __init__(self):
        pass
#     判断是否是时间
    def Is_Valid_Time(self,str):
        try:
    #         print(str)
            time1 = datetime.datetime.strptime(str,'%H:%M')
    #         print(time1)
            return True
        except:
            return False
       

#    获取列车正晚点时间
#   查询的时候要考虑跨天的情况
    def getTrianTime(self,cz,cc,Acxlx):
        url_header = 'http://dynamic.12306.cn/mapping/kfxt/zwdcx/LCZWD/cx.jsp?'
        cxlx='cxlx=%s'%Acxlx
        rq=datetime.datetime.now().strftime('%Y-%m-%d')
        if cz.strip()!='':
            postData_cz={'cz':cz}
            postdata_czEn={'czEn':cz}
            rb_cz= parse.urlencode(postData_cz,encoding='gb2312')
            rb_czEn= parse.urlencode(postdata_czEn,encoding='utf-8').replace('%','-')
            if cc.strip()!='':
                postData_cc='cc='+cc
#         url= url_header + rb_cz +'&'+postData_cc+'&'+cxlx+'&rq='+rq+'&'+rb_czEn
        url = '%s%s&%s&%s&rq=%s&%s'%(url_header,rb_cz,postData_cc,cxlx,rq,rb_czEn)
        print(url)
        res= requests.get(url)
        #20180904加入新情况，列车有可能停开，返回的信息如“列车时刻表中无K9023次列车的信息”
        if '列车时刻表中无' in res.text:
            return '无此趟列车'
        elif '请稍候重新查询' in res.text:
            sReturn = '查询异常：系统'
            return sReturn
        else:
            rbTime= res.text[-6:].strip()
    #     print(rbTime)
            if self.Is_Valid_Time(rbTime):
                return rbTime
            else:
                return "查询异常：%s"%(rbTime)
        
           
    def GetLocaltimeHM(self):
        return time.strftime('%H:%M',time.localtime())
   
    def GetNextQueryTime(self,aActTime):
        #计算当前时间与查询时间之差，取半返回
        sdate = time.strftime('%Y-%m-%d',time.localtime())
        dnow = time.mktime(time.localtime())
        dAct = time.mktime(time.strptime(sdate+' ' + aActTime,'%Y-%m-%d %H:%M'))
        if dnow >= dAct:
            return time.strftime('%H:%M',time.localtime()),0
        else:
            dnext = dnow + (dAct-dnow)/2
            dspanTime = (dAct-dnow)/2
            return time.strftime('%H:%M',time.localtime(dnext)),int(dspanTime)
       
    def calcSpanTime(self,aActualTime,aScheduleTime):
        
        '''计算正晚点时间差
       入参：列车实际到达或出发时间点，正点时间点
       出参：返回以分为单位的时间差;
       '''
        sdate = time.strftime('%Y-%m-%d',time.localtime())
        dSchedule = time.mktime(time.strptime(sdate + ' '+ aScheduleTime,'%Y-%m-%d %H:%M'))
        dActual = time.mktime(time.strptime(sdate+' ' + aActualTime,'%Y-%m-%d %H:%M'))
        return int((dActual - dSchedule)/60)
   
    def ReadDataFromCSV(self):
        csv_File = csv.reader(open('trainlatetime.csv','r'))
        return csv_File
    '''判断文件中是否有相关纪录
       入参：字段纪录(车次+日期+站名+进出站类型)   
       出参：True or False 
    '''
    def IsExistsRecord(self,aRow):
        #先处理aRow(格式:k9006,2018-8-22,韶关东,进站,21:24,21:31,1,7)
        lstRow = aRow[0:4]
#         print(lstRow)
        bExist = False
        with open('trainlatetime.csv') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
#                 print(row)
                d = [False for c in lstRow if c not in row]
                if not d:
                    bExist = True
                    break
            return bExist
        
    #判断文件是否已被打开
    def is_open(self,filename):
        if not os.access(filename, os.F_OK):
            return False # file doesn't exist
        h = _sopen(filename, 0, _SH_DENYRW, 0)
        if h == 3:
            _close(h)
            return False # file is not opened by anyone else
        return True # file is already open
   
    #把数据写入到csv文件
    def WriteDataToCSV(self,aRow):
        #csv 写入之前判断纪录是否存在
        if not self.IsExistsRecord(aRow):
            #打开之前先判断文件是否已经被打开
#             if self.is_open('trainlatetime.csv'):
#                 print("文件已被打开，请关闭")
#                 sleep(10)
            #打开文件，追加a
            out = open('trainlatetime.csv','a', newline='')  
            #设定写入模式
            csv_write = csv.writer(out,dialect='excel')
            #写入具体内容
            csv_write.writerow(aRow)
            print('写入文件成功')
            sendPushBear(','.join(aRow))
            return None
       
       
    def WriteDataTODB(self,aActTime,ascheduleTime,sCZ,sCC,bcxlx):
        #如果表不存在，则创建
        sql_create_table = '''create table if not exists trainlatetime(
                           TrainID Text not null,
                           QueryDate Text not null,
                           Station Text not null,
                           EntryFlag Text not null,
                           PunctualTime integer not null,
                           ActualTime Text not null,
                           PunctualFlag integer,
                           LateSpanTime integer,
                           primary key(TrainID,QueryDate));'''
        conn = sqlite3.connect('/tmp/TrainLateTime.db')
        cur = conn.cursor()
       
        cur.execute(sql_create_table)
        conn.commit()
        #计算实际到达时间与正点时间之差，返回以分钟为单位的整型
        spanTime = calcSpanTime(aActTime,ascheduleTime)
        if spanTime>0:
            bPunctual = 1
        else:
            bPunctual = -1
        #插入数据到表中
        Sql_Insert_Table = 'Insert into trainlatetime values(?,?,?,?,?,?,?,?)'
        record = (sCC,time.strftime('%Y-%m-%d',time.localtime()),sCC,self.IsEntry(bcxlx),ascheduleTime,aActTime,bPunctual,abs(spanTime))
        cur.execute(sql_Insert_Table,record)
        conn.commit()
       
    def IsWriteType(self,bSaveType,sActTime,i,sCZ,sCC,bcxlx):
        if bSaveType == 0:
            WriteDataTODB(sActTime,i,sCZ,sCC,bcxlx)
        else:
            spanTime = self.calcSpanTime(sActTime,i)
            if spanTime>0:
                bPunctual = '晚点'
            else:
                bPunctual = '正点'                           
            sRow = '%s,%s,%s,%s,%s,%s,%s,%s'%(sCC,time.strftime('%a %Y-%m-%d',time.localtime()),sCZ,self.IsEntry(bcxlx),i,sActTime,bPunctual,abs(spanTime))
            self.WriteDataToCSV(sRow.split(','))
        return None
   
    def IsEntry(self,bcxlx):
        if bcxlx == 0:
            return '进站'
        elif bcxlx == 1:
            return '出站'
        else:
            return None                 
       
    def GetNextTime(self,spanTimeMinute):
        #解析出后面的分钟数
#         spanTimeMinute= list(time_span).pop(1)
        TimeInt = int(time.time() + spanTimeMinute*60)
        TimeStr = time.strftime('%H:%M',time.localtime(TimeInt))
        return TimeInt
   
    def run(self,schedule_timeList_old,Train_StationList_old,sCCList_old):
#         actual_Time=[]
#         print(Train_StationList_old)
       #创建字典，保存当前车次下个查询时间点，用来比较几趟车下次查询的时间点，取出最早时间来做查询，其它的可以忽略
        dict_queryNextTime={}
        bLastTime = False
#         bQuery = False
        while True:
            if len(schedule_timeList_old) == 0 and bLastTime and not dict_queryNextTime:
                ss = '所有列车车次正晚点查询已完成'
                print(ss)
                sendPushBear(ss)
                break
            #判断字典是否为空，如果为空说明是首次查询,所有车次都需要进行一次查询
            if not dict_queryNextTime:
#                 print('字典为空')
                #注意了，不能直接赋值，直接赋值，这2个变量会指向同一块内存地址，对其中之一操作，同时会影响另一个变量的值
                schedule_timeList = schedule_timeList_old.copy()
                Train_StationList = Train_StationList_old.copy()
                sCCList = sCCList_old.copy()
                bQuery = True
            else:
                #如果不为空，进行时间比较，利用sorted函数进行排序（reverse=false为升序，reverse=true为降序），
                #取出最小时间点，进行下一次查询
#                 print(dict_queryNextTime.items())
                sorted_timeList = sorted(dict_queryNextTime.items(),key = lambda dict_queryNextTime:dict_queryNextTime[1],reverse=False)
                print(sorted_timeList)
                #此处的sorted_timeList.pop(0)格式为元组（'k9006','12:20'）,需要做进一步解析取出后面的value:12:20
                list_timeList0 = list(sorted_timeList.pop(0))
                spanTimeKey = list_timeList0[0]
                print(spanTimeKey)
                spanTimeMinute= list_timeList0[1]
                print(spanTimeMinute)
                #同时需删除字典中的对应key/value值
                dict_queryNextTime.pop(spanTimeKey)   
                print(dict_queryNextTime)
#                 Query_NextTime = self.GetNextTime(sorted_timeList.pop(0))
                bQuery = False
            if not bQuery:
                time.sleep(spanTimeMinute)
                schedule_timeList = schedule_timeList_old.copy()
                Train_StationList = Train_StationList_old.copy()
                sCCList = sCCList_old.copy()                

            for index in range(len(schedule_timeList)):
#                 print(Train_StationList_old)
#                 print(Train_StationList)
                
                schedule_time_old = schedule_timeList.pop(0)
                Train_Station_old = Train_StationList.pop(0)
                print(Train_StationList_old)
                print(Train_StationList)
                sCC_old = sCCList.pop(0) 
                
                schedule_time = schedule_time_old.copy()
                Train_Station= Train_Station_old.copy()
                sCC = sCC_old
                #20180910如何判断第一站为始发站还是中途站？
                sCZST = Train_Station[0]
                sCZSE = Train_Station[-1]
                #查询类型（1为发车时间，0为到达时间），初始为0
                #发车只考虑由南往北的发车，且终点站为韶关东
                #其它都是由北往南开的车次，查询开始点都为到达时间且一般终点站都是广州。
                bcxlx = 0
                #保存最后一次的时间，以此来判断是否到了查询末尾。
                sLastStationTime = schedule_time[-1]
                for i in schedule_time:
                #下面的写法有问题，这等于每次取出一个时刻，都要去查询所有车站，改为使用pop(0),每次弹出第一个元素
        #             for sCZ in (Train_Station):
                    #当前时间与本次时间作对比,eg:
                    if bcxlx == 0:
                        sCZ = Train_Station.pop(0)
                    if sCZ== sCZST and sCZSE=='韶关东':
                        bcxlx = 1
#                     if sCZ == sCZST and (sCZSE!='广州' or sCZSE!='广州北' or sCZSE!='广州东' or sCZSE!='广州南'):
#                         bcxlx = 1
        #                 print(self.get123())
    
                    print(sCZ,sCC)
                    sActTime = self.getTrianTime(sCZ,sCC,bcxlx)
                    #如果查询异常
                    #20180904新增查询返回无此趟列车信息
                    if '无此趟列车' in sActTime:
                        bLastTime = True
                        if Train_StationList_old!=[]:                               
                            Train_StationList_old.remove(Train_Station_old)
                            schedule_timeList_old.remove(schedule_time_old)
                            sCCList_old.remove(sCC_old)
                            self.WriteDataToCSV([sCC,time.strftime('%Y-%m-%d',time.localtime()),'列车停开'])
                            print('{0}:趟列车今日停开！'.format(sCC))
                            break
                        
                    if '查询异常' in sActTime:
                        print('查询异常')
                        #如果查询异常，再连续查询2次，中间间隔5s钟
                        for index in range(2):
                            time.sleep(5)
                            sActTime = self.getTrianTime(sCZ,sCC,bcxlx)
                            if '查询异常' not in sActTime:
                                break
                            else:
                                print('%s%s查询异常'%(sCZ,self.IsEntry(bcxlx)))
                                if i == sLastStationTime and self.GetLocaltimeHM() > i:
                                    bLastTime = True
                                    if Train_StationList_old!=[]:    
                                        print(Train_StationList_old)
                                        print(Train_Station_old)
                                        Train_StationList_old.remove(Train_Station_old)
                                        schedule_timeList_old.remove(schedule_time_old)
                                        sCCList_old.remove(sCC_old)
                                        print('{0}:查询已完成！'.format(sCC))  
                                        break
                        bcxlx = ~bcxlx + 2
                    #如果查询到的时间已经小于或等于现有时间点，说明列车已经进站或者出站,保存数据进数据库并进入下一步查询
                    #20180830这里有一种情况需要考虑，就是时间跨天的情况，以下条件是会做出错误判断的
                    elif sActTime <= self.GetLocaltimeHM():
                        #这里面分2种情况，一种是在当天内，另一种是跨天
                        #判断标志当前时间大于等于20：00，查询到的时间小于10:00，即可判断已跨天。
                        try:
                            snow = self.GetLocaltimeHM()
                            sQTimeH = sActTime.split(':')[0]
                            sQTimeMM = sActTime.split(':')[1]
                            snowH = snow.split(':')[0]
                            snowMM = snow.split(':')[1]
                        except:
                            print('%s;%s时间格式可能不正确!'%(snow,sActTime))
#                             print('{0}{1}时间格式不正确!'.format(sActTime))
                            continue
#                         icolon = sActTime.find(":")
#                         if icolon > 0:
#                             iqueryTime = sActTime[:icolon]
#                         else:
#                             print('{0}时间格式不正确!'.format(sActTime))
#                             continue
                         #如果是跨天这种情况，需要对查询到的时间作进一步处理再比较
                        if int(sQTimeH) <10 and int(snowH) >=20:
                            #说明列车尚未到站，直接进行下一站查询
                            break
                        
                        else:
                            print(i,sLastStationTime)
                            #判断本趟列车是否是已到达最后一站,如果此趟列车已经到达终点站，则从原列表中删除此趟列车，无需浪费资源作进一步的查询
                            if i == sLastStationTime:
                                bLastTime = True
                                if Train_StationList_old!=[]:                               
                                    Train_StationList_old.remove(Train_Station_old)
                                    schedule_timeList_old.remove(schedule_time_old)
                                    sCCList_old.remove(sCC_old)
                                    print('{0}:查询已完成！'.format(sCC))

                            self.IsWriteType(bSaveType,sActTime,i,sCZ,sCC,bcxlx)
                            bcxlx = ~bcxlx + 2
                            continue
#                         不再进行下一车站的查询，等待下次查询时间到再进行查询
#                         break
                        
                    #如果查询到的时间大于当前时间，说明列车尚未进站或出站，需要进一步查询列车进站或出站时间
                    elif  self.GetLocaltimeHM() < sActTime:
                        #本趟列车可以暂时不用占用查询资源，等到下一次的查询时间到了再作查询,GetNextQueryTime返回以秒为单位的下次查询时间
                        sHalfTime,ispanTime = self.GetNextQueryTime(sActTime)
                        #判断当前车次是否已存在字典当中，如果存在，则更新键值，不存在则创建(原来python中新增key/value无需自己判断，字典会自行
                        #进行判断新增还是作个性，写法dict['k9006']='12:36')
                        #对ispanTime进行判断比较，小于10分钟的不再进行查询，等10分钟之后再进行查询
                        if ispanTime <= 10*60:
                            ispanTime = 10*60
                        dict_queryNextTime[sCC] = ispanTime
                        #同时保存本趟列车剩余的时刻表及车站
                        break
                        #下面的代码感觉没有必要添加，纯属浪费时间地等待，可以优化进行下一次查询
                        #判断本次列车查询需要结束的标志是：当前时间>查询终点站的到站时间。
                        '''
                        #计算当前时间与查询到的时间差作比较，返回下一个查询时间参考点
                        while True:
                            sHalfTime = self.GetNextQueryTime(sActTime)
                            #如果当前时间等于要查询的时间点，开始查询
                            if self.GetLocaltimeHM() == sHalfTime:
                                print(sHalfTime)
                                time.sleep(60)
                                sActTime = self.getTrianTime(sCZ,sCC,bcxlx).strip()
                                #如果当前时间大于查询到的时间，保存数据并退出循环，进行下一步查询。
                            elif self.GetLocaltimeHM() >= sActTime:
                                    self.IsWriteType(bSaveType,sActTime,i,sCZ,sCC,bcxlx)
                                    bcxlx = ~bcxlx + 2
                                    break
                                    '''
                       
               
           


    def timerFun(self,sched_Timer):
        flag = 0
        while True:
            TimeNow = datetime.datetime.now()
            if TimeNow >= sched_Timer and flag == 0:
                print(sCC_Old)
                sCCList1 = sCC_Old
#                 print(TimeNow,sched_Timer)
                schedule_timeList1 = punctualTime
                Train_StationList1 = TrainStation
                #判断以下三项的数据长度是否相等，不相等给出提示并退出
                if len(sCCList1)!=len(schedule_timeList1)!=len(Train_StationList1):
                    print('数据长度不合法，请检查!')
                    break
       
                print('开始执行查询')
                self.run(schedule_timeList1,Train_StationList1,sCCList1)
                flag = 1
            elif flag == 1:
                    sched_Timer = sched_Timer + datetime.timedelta(days=1)
                    flag = 0


if __name__ == "__main__":
#     print()
    cs = RunTask()
    #Z111/Z114:哈尔滨西-海口
    scc_Z111 = 'Z111'
    sTime_Z111=['8:46','8:49','10:44','10:48','11:52','12:02','14:03','14:07','15:58','16:22','18:42','18:48','21:10']
    sStation_Z111=['麻城','九江','南昌西','吉安','赣州','韶关东','广州']   
    #Z111/Z114:乌鲁木齐-广州
    scc_Z137 = 'Z137'
    sTime_Z137=['9:35','9:56','11:53','11:56','13:17','13:23','13:59','14:03','15:24','15:28','17:06','17:11','18:48','18:54','21:22']
    sStation_Z137=['武昌','岳阳','长沙','株洲','衡阳','郴州','韶关东','广州']    
    #2018-10-18加入k9121，k1159到查询列表中
    #K9121:衡阳-深圳
    scc_K9121 = 'K9121'
    sTime_K9121=['17:37','17:40','19:13','19:16','20:15']
    sStation_K9121=['韶关东','源潭','广州'] 

    #K1159:烟台-广州
    scc_K1159 = 'K1159'
    sTime_K1159=['17:46','17:52','20:32']
    sStation_K1159=['韶关东','广州']     

    sCC_Old =[]
    #punctualTime
    punctualTime = []
    TrainStation=[]
    
    #添加新车次Z111
    sCC_Old.append(scc_Z111)
    punctualTime.append(sTime_Z111)
    TrainStation.append(sStation_Z111)  
    #添加新车次Z137
    sCC_Old.append(scc_Z137)
    punctualTime.append(sTime_Z137)
    TrainStation.append(sStation_Z137)     
    #2018-10-18添加新车次k9121,k1159
    sCC_Old.append(scc_K9121)
    punctualTime.append(sTime_K9121)
    TrainStation.append(sStation_K9121) 
    sCC_Old.append(scc_K1159)
    punctualTime.append(sTime_K1159)
    TrainStation.append(sStation_K1159) 
    
    # print(sCC_Old)
    # print(punctualTime) 
    # print(TrainStation)
    #应用执行开始时间
#     sched_Timer = time.strftime('%Y-%m-%d %H:%M',time.localtime())
    sched_Timer = datetime.datetime.now()
    #数据保存方式,0为sqlite3数据库，1为csv文件
    bSaveType = 1
    if bSaveType == 1:
        #sCZ,bcxlx,i,sActTime,bPunctual,abs(spanTime)
        #写入标题先需要先判断标题是否已经有了
        #判断文件trainlatetime.csv是否存在
        path = pathlib.Path('trainlatetime.csv')
        #如果文件不存在，则创建
        if not path.is_file():
            csvfile = open('trainlatetime.csv','w')
            csvfile.close()
        bExists = False
        for line in cs.ReadDataFromCSV():
            if '车次' in line:
                print('标题已存在')
                bExists = True
                break
        if not bExists:
            sheetHeader = ['车次','查询日期','停靠车站','进站或出站','正点时间','实际停靠时间','正点标志','晚点时间']
            cs.WriteDataToCSV(sheetHeader)
       
    # print ('run the timer task at {0}'.format(sched_Timer))
#     print(cs.GetLocaltimeHM)
    cs.timerFun(sched_Timer)

   
