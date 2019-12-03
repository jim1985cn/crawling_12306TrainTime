# !/usr/bin/python3.6
# -*- coding:utf-8 –*-

# 出发日期(list)
# station_dates = ["2019-02-01","2019-02-02"]
station_dates = ["2019-03-31"]

# 是否根据时间范围 和 乘车类型 购票
# 否则将需要手动填写车次
is_by_time = False

# 列车类型: 高铁 G 动车 D 其它火车 O
train_types = ['G', 'D', 'O']

# 可接受最早出发时间
departure_time = "18:00"

# 可接受最晚抵达时间
arrival_time = "21:00"

# 可接受最长旅途时间
take_time = "4:00"

# 填入需要购买的车次(list)
# station_trains = ['G6172', 'G6186', 'G6154']
station_trains = ['G6025', 'Z111', 'K1665']
# station_trains = ['T254']

# 出发城市，比如深圳北，就填深圳就搜得到
from_station = "韶关"
# from_station = '广州'

# 到达城市 比如深圳北，就填深圳就搜得到
to_station = "广州"
# to_station = '韶关'

# 座位(list) 多个座位ex:
# - "商务座"
# - "一等座"
# - "二等座"
# - "特等座"
# - "软卧"
# - "硬卧"
# - "硬座"
# - "无座"
# - "动卧"
set_type = ['二等座','硬座']

# 当余票小于乘车人，如果选择优先提交，则删减联系人和余票数一致在提交
is_more_ticket = True

# 乘车人(list) 多个乘车人
ticke_peoples = ['陈志兵']

# 12306登录账号(list)
account12306 = {
  'user': 'jim1985@126.com',
  'pwd': 'lss13420557945'
}

# 加入小黑屋时间默认为5分钟，此功能为了防止僵尸票导致一直下单不成功错过正常的票，
ticket_black_list_time = 5

# 自动打码
# is_auto_code = True
is_auto_code = False

# 打码平台， 2 为若快平台（目前只支持若快平台打码，打码兔已经关闭）, 若快注册地址：http://www.ruokuai.com/client/index?6726
auto_code_type = 2

# 打码平台账号
auto_code_account = {
  'user': 'cyber123',
  'pwd': 'j66138947'
}
'''
email_conf = {
    'is_email': True,
    'email': "931128603@qq.com ",
    'notice_email_list': "931128603@qq.com",
    'username': "931128603",
    'password': "",
    'host': "smtp.qq.com"
}
'''
#配置本人邮箱20190116
email_conf = {
    'is_email': True,
    'email': "jim1985@126.com ",
    'notice_email_list': "631608185@qq.com",
    'username': "jim1985",
    'password': "j15168428401",
    'host': "smtp.126.com"
}
# 是否开启 pushbear 微信提醒， 使用前需要前往 http://pushbear.ftqq.com 扫码绑定获取 send_key 并关注获得抢票结果通知的公众号
pushbear_conf={
  'is_pushbear': True,
  'send_key':"SCU42588T42a40240533a8786c65026dcb0d614385c45b80c40ae7"
}

# 是否开启cdn查询，可以更快的检测票票 1为开启，2为关闭
is_cdn = 1

# 下单接口分为两种，1 为快速下单，2 是普通下单
order_type = 2

# 下单模式 1 为预售，整点刷新，刷新间隔0.1-0.5S, 然后会校验时间，比如12点的预售，那脚本就会在12.00整检票，刷新订单
#         2 是捡漏，捡漏的刷新间隔时间为0.5-3秒，时间间隔长，不容易封ip
order_model = 2

# 预售放票时间, 如果是捡漏模式，可以忽略此操作
open_time = '13:00:00'

# 是否开启代理, 0代表关闭， 1表示开始
# 开启此功能的时候请确保代理ip是否可用，在测试放里面经过充分的测试，再开启此功能，不然可能会耽误你购票的宝贵时间
# 使用方法：
# 1、在agency/proxy_list列表下填入代理ip
# 2、测试UnitTest/TestAll/testProxy 测试代理是否可以用
# 3、开启代理ip
is_proxy = 0


configMap = {key: value for key, value in locals().items() if not key.startswith('__')}
