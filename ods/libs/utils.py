#coding=utf-8

"""
    author : niyoufa
    date : 2016-05-11

"""

import time
import datetime, logging
import json, pdb, sys, traceback
from bson.objectid import ObjectId
from bson.json_util import dumps

InfoLogger = logging.getLogger("dhui_commands")
ErrorLogger = logging.getLogger("dhui_commands_error")

#生成objectid
def create_objectid(str):
    return ObjectId(str)

#将objectid 转换为string字符串
def objectid_str(objectid):
    return  json.loads(dumps(objectid))['$oid']

#发送跨域POST请求
def send_post_request(url,data,csrftoken,headers) :
    import urllib
    import urllib2
    import cookielib

    data = urllib.urlencode(data)

    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'csrftoken=%s'%(csrftoken)))
    opener.addheaders.extend(headers.items())
    result = json.loads(opener.open(url,data).read())
    return result

#获取csrf token
def get_csrf_token(url) :
    import urllib
    import urllib2
    import cookielib
    f = urllib.urlopen(url)
    result_data = json.loads(f.read())
    result_data["headers"] = f.headers
    return result_data

#获得错误堆栈信息
def get_trace_info():
    trace_info = ""
    info = sys.exc_info()
    for file, lineno, function, text in traceback.extract_tb(info[2]):
        trace_info += "file：%s,line:%s\n in %s;\n"%(file,lineno,function)
    return trace_info

#列表排序
def sort_list(list_obj,sort_key) :
    if not type(list_obj) == type([]) :
        raise Exception("type error")
    else :
        list_obj.sort(key=lambda obj :obj[sort_key])
    return list_obj

#导入项目代码
def load_project():
    # import sys , os
    # BASE_DIR = os.path.abspath(__file__)
    # _root = os.path.dirname(BASE_DIR)
    # sys.path.append(_root)

    import sys , os
    BASE_DIR = "E:\\develop\\tornado_demo\\swallow"
    sys.path.append(BASE_DIR)

def timestamp_from_objectid(objectid):
  result = 0
  try:
    timestamp = time.mktime(objectid.generation_time.timetuple())
    temp_list = str(timestamp).split(".")
    result = int("".join(temp_list))
  except:
    pass
  return result


# odoo 数据操作

def load_obj(xmlrpcclient,obj):
    return xmlrpcclient.create(obj)

def has_obj(xmlrpcclient,query_params):
    count = xmlrpcclient.search_count(query_params)
    if count > 0 :
        return True
    else :
        return False

def read_obj(xmlrpcclient,query_params,*args):
    if query_params.has_key("id_list") and query_params.has_key("field_list") :
        result = xmlrpcclient.read_by_ids(query_params,*args)
    else :
        result = xmlrpcclient.read(query_params,*args)
    return result

def get_product_id(pt_xmlrpcclient,pp_xmlrpcclient,good):
    product_id = None
    sku = good["sku"]
    query_params = dict(
        sku=sku,
    )
    if has_obj(pt_xmlrpcclient, query_params):
        result = pt_xmlrpcclient.search(query_params)
        product_template_id = result[0]
    else:
        print "sku=%s:this good is not exist!" % good["sku"]
        return product_id

    query_params = dict(
        product_tmpl_id=product_template_id,
    )

    if has_obj(pp_xmlrpcclient, query_params):
        result = pp_xmlrpcclient.search(query_params)
        product_id = result[0]
    else:
        return product_id

    return product_id , product_template_id

def get_order_list(xmlrpcclient,query_params,extra_query_params):
    sale_order_list = read_obj(xmlrpcclient,query_params,extra_query_params)
    return sale_order_list

def update_obj_list(xmlrpcclient, obj_list):
    xmlrpcclient.batch_update(obj_list)


# dj_server
import re, time


def list_first_item(value):
    try:
        if not hasattr(value[0], '__iter__'):
            return [value[0]]
        else:
            return value[0]
    except Exception:
        return None


def float_equals(a, b):
    return abs(a - b) <= 1e-6


def uid(class_name):
    # 将大写字母换成小写并在字母前加前缀_
    return re.sub(r'([A-Z])', r'_\1', class_name).lower()[1:]


# 根据卡号返回消费类型,1:普通银行卡,2:加油卡,3:信用卡,1000:现金
def getPaymentTypeByCard(card, card_fromat=None):
    if card_fromat != None:
        reobj = re.compile(card_fromat)
        result = reobj.match(card)

        # 加油卡
        if result:
            return 2

    # 银行卡号最多为19位
    if len(card) > 19:
        return 1000

    # 银行卡至少为16位,信用卡至少为14位
    if len(card) >= 14:

        # 前六位为银行卡的BIN
        front = int(card[:6])

        # 信用卡BIN分配如下:
        # 威士卡（VISA）:400000—499999;万事达卡（MasterCard）:510000—559999;
        # 运通卡（American Express）:340000—349999，370000—379999;
        # 大来卡（DinersClub）:300000—305999，309500—309599,360000—369999，380000—399999;
        # JCB卡（JCB）:352800—358999
        if (front >= 300000 and front <= 305999) or (front >= 309500 and front <= 305999) or \
                (front >= 360000 and front <= 369999) or (front >= 380000 and front <= 399999) or \
                (front >= 352800 and front <= 358999) or (front >= 340000 and front <= 349999) or \
                (front >= 370000 and front <= 379999) or (front >= 510000 and front <= 559999) or \
                (front >= 400000 and front <= 499999):
            return 3

        else:
            if len(card) >= 16:
                card_front = card[:1]
                # 普通银行卡以6,9开头,多数为6
                if card_front == '6' or card_front == '9':
                    return 1
                else:
                    return 1000

    # 现金
    return 1000


# 序列化交易编号
def compute_trans_id(data_time, shard_id, site_id, gun_id, money):
    # 交易时间,32位
    data_time = long(int(data_time))
    data_time = data_time << 32

    # 服务器编号，6位，最多64台
    shard_id = shard_id << 26

    # 油站编号,10位，最多每个服务器上1024个
    site_id = site_id << 16

    # 油枪号，7位，一个油站最多128个
    gun_id = gun_id << 9

    # 金额 9位
    result = data_time + shard_id + site_id + gun_id + money

    return result


# 反序列化交易编号
def deserialize_trans_id(long_trans_id):
    num = long(long_trans_id)
    # 获取高32位的时间
    time = int(num >> 32)
    # 获取低32 位
    num = num & 0xFFFFFFFF
    shard_id = num >> 26
    # 取出低26位
    num = num & 0x3FFFFFF
    site_id = num >> 16
    # 取出低16位
    num = num & 0xFFFF
    gun_id = num >> 9
    # 获取金额
    money = num & 0x1FF
    return (time, shard_id, site_id, gun_id, money)


# 字典支持点操作类
class easyaccessdict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        n = easyaccessdict()
        super(easyaccessdict, self).__setitem__(name, n)
        return n

    def __getitem__(self, name):
        if name not in self:
            super(easyaccessdict, self).__setitem__(name, nicedict())
        return super(easyaccessdict, self).__getitem__(name)

    def __setattr__(self, name, value):
        super(easyaccessdict, self).__setitem__(name, value)


# 字典支持点操作
def tran_dict_to_obj(dict_data):
    obj = easyaccessdict()
    for item in dict_data:
        obj[item] = dict_data[item]
    return obj


# 把object对象转化为可json序列化的字典
def convert_to_dict(obj):
    dic = {}
    if not isinstance(obj, dict):
        dic.update(obj.__dict__)
    else:
        dic = obj
    for key, value in dic.items():
        if isinstance(value, datetime.datetime):
            dic[key] = str(value)
        elif key[0] == '_':
            dic.pop(key)

    return dic

# mongodb 相关处理

#获取东汇商城用户名
def get_customer(coll,user_id):
    result = {}
    try :
        user = coll.find_one({"_id":ObjectId(user_id)})
    except :
        return result
    if user:
        result.update(user["wx_info"])
    else :
        result = {}
    return result

#返回地址信息
def get_address(coll,address_id):
    result = {}
    try :
        address = coll.find_one({"_id":ObjectId(address_id)})
    except:
        return result

    if address :
        result["district"] = address["district"]
        result["area"] = address["area"]
        result["city"] = address["city"]
        result["detailed_address"] = address["detailed_address"]
        result["contact_mobile"] = address["contact_mobile"]
        result["contact_name"] = address["contact_name"]
        result["remark"] = address["remark"]
    else:
        result = {}
    return result

#python time时间处理相关工具

def get_report_date(time=datetime.datetime.now(),delta=0):
    curr_date = time - datetime.timedelta(days=delta)
    return curr_date

def get_curr_time(delta=0):
    curr_date = datetime.datetime.now() - datetime.timedelta(days=delta)
    curr_time = str(curr_date).split(".")[0]
    return curr_time

def get_report_time(query_time=datetime.datetime.now(),*args,**options):
    report_date = get_report_date(query_time,delta=options.get("delta",0))
    report_time = str(report_date).split(".")[0]
    cmp_time = str(report_date).split(" ")[0] + " " +"00:00:00"
    if report_time < cmp_time :
        yester_date = report_date - datetime.timedelta(days=1)
        end_time = str(report_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(yester_date).split(" ")[0] + " " + "00:00:00"
    else :
        tormo_date = report_date + datetime.timedelta(days=1)
        end_time = str(tormo_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(report_date).split(" ")[0] + " " + "00:00:00"
    return start_time, end_time

def get_time_range(query_time=datetime.datetime.now(),*args,**options):
    range_date = get_report_date(query_time,delta=options.get("delta",0))
    range_time = str(range_date).split(".")[0]
    cmp_time = str(range_date).split(" ")[0] + " " + "00:00:00"
    if range_time < cmp_time:
        yester_date = range_date - datetime.timedelta(days=1)
        end_time = str(range_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(yester_date).split(" ")[0] + " " + "00:00:00"
    else:
        tormo_date = range_date + datetime.timedelta(days=1)
        end_time = str(tormo_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(range_date).split(" ")[0] + " " + "00:00:00"
    return start_time, end_time

def get_date_time(date_time_str):
    date_time_str = str(date_time_str).split(".")[0]
    date_time_arr = time.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    this_date = datetime.datetime(date_time_arr[0],date_time_arr[1],date_time_arr[2],date_time_arr[3],
                                  date_time_arr[4],date_time_arr[5])
    this_time = str(this_date).split(".")[0]
    cmp_time = str(this_date).split(" ")[0] + " " + "00:00:00"
    if this_time < cmp_time:
        yester_date = this_date - datetime.timedelta(days=1)
        end_time = str(this_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(yester_date).split(" ")[0] + " " + "00:00:00"
    else:
        tormo_date = this_date + datetime.timedelta(days=1)
        end_time = str(tormo_date).split(" ")[0] + " " + "00:00:00"
        start_time = str(this_date).split(" ")[0] + " " + "00:00:00"
    return start_time, end_time


def get_invoice_report_name(*args, **options):
    # 每天生成一个订单发货表
    start_time, end_time = get_report_time()
    return "物流单(%s)" % (start_time.split(" ")[0])

# utc 与本地时间转换
def utc2local(utc_st):
    """UTC时间转本地时间（+8:00）"""
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st

def local2utc(local_st):
    """本地时间转UTC时间（-8:00）"""
    time_struct = time.mktime(local_st.timetuple())
    utc_st = datetime.datetime.utcfromtimestamp(time_struct)
    return utc_st

def str2datetime(timestr):
    t = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    d = datetime.datetime(*t[:6])
    return d
