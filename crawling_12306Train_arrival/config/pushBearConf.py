# !/usr/bin/python3.6
# -*- coding:utf-8 -*-

import requests
from config import ticketConf
from config import urlConf
from config.ticketConf import configMap
# import urlConf
# from ticketConf import configMap
# import sys
# sys.path.append("..")
from myUrllib.httpUtils import HTTPClient

def sendPushBear(msg):
	"""
	pushBear微信通知
	:param str:通知内容 content
	:return:
	"""
	# print()	
	if configMap["pushbear_conf"]["is_pushbear"] and configMap["pushbear_conf"]["send_key"].strip()!="":
	# if 1!=2:
		try:
			sendPushBearUrls = urlConf.urls["Pushbear"]
			print(sendPushBearUrls)
			data = {
    		   "send_key": configMap["pushbear_conf"]["send_key"].strip(),
    		   "text": "抢票情况通知",
    		   "desp": msg
    		}
    		#以下方法测试老是报pushbear配置有误
			HTTPClient1 = HTTPClient(0)
			sendPushBearRSP = HTTPClient1.send(sendPushBearUrls, data=data)
			# print(sendPushBearRSP)
			# if sendPushBearRSP["errno"] is 0:
			if sendPushBearRSP.get("errno") is 0:
				print(u"已下发 pushbear 微信通知,请查收")
			else:
				print(sendPushBearRSP)
		except Exception as e:
			print(u"pushbear配置有误{}".format(e))
		else:
			pass
		finally:
			pass
	else:
		pass
	

if __name__ == '__main__':
	sendPushBear("陈志兵")