import csv
import json
import os
import redis
from pymongo import MongoClient

import numpy as np
try:
    import xml.etree.cElementTree as ET 
except ImportError:
    import xml.etree.cElementTree as ET  

from mobile_insight.analyzer.analyzer import *
from mobile_insight.monitor import OfflineReplayer

class myAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.add_source_callback(self.__msg_callback)
        self.unsupported = []
        self.field_list = []

    def set_source(self, source):
        Analyzer.set_source(self, source)
        source.enable_log_all()
        # source.enable_log("LTE_PHY_Serv_Cell_Measurement")
        # source.enable_log("5G_NR_RRC_OTA_Packet")
        # source.enable_log("LTE_RRC_OTA_Packet")
        # source.enable_log("LTE_NB1_ML1_GM_DCI_Info")

    def __msg_callback(self, msg):
        
        msg_fields ={}
        # data = msg.data.decode()
        data = msg.data.decode_json()
        data = json.loads(data)

        # print(type(data))
        # get the identifying fields like type_id, timestamp, msg_len, etc.
        for k in data.keys():
            if k != 'Msg': #and k != 'timestamp':
                msg_fields[k] = data[k]
            # if k == 'timestamp':
                # print(type(data[k]))
                # print(data[k].strftime("%Y-%m-%d %H:%M:%S.%f"))
                # msg_fields[k] = data[k].strftime("%Y-%m-%d %H:%M:%S.%f")
                # # convert datatype into a string

        # get Msg contents of Log message
        if 'Msg' in data.keys():
            log_xml = ET.XML(data['Msg'])
        else:
            self.field_list.append(msg_fields)
            return

        xml_msg = Event(msg.timestamp, msg.type_id, log_xml)
        
        msg_dict = {}
        for field in xml_msg.data.iter('field'):
            if field.get('showname') != None and field.get('value') != None:
                showname = field.get('showname')
                mask = np.array([char.isalpha() for char in list(showname)])
                start_idx = np.where(mask)[0][0]
                msg_dict[showname[start_idx:]] = field.get('value')
                # self.field_list.append([showname[start_idx:], field.get('value')])
                # print(showname[start_idx:], field.get('value'))

        msg_fields['Msg'] = msg_dict
        self.field_list.append(msg_fields)

r = redis.Redis(
    host='127.0.0.1',
    port=6379
)

client = MongoClient("localhost", 27017)
db = client['mobile_insight']

def my_analysis(input_object):
    src = OfflineReplayer()
    src.set_input_file(input_object)
    src.enable_log_all()

    analyzer = myAnalyzer()
    analyzer.set_source(src)
    src.run()

    return analyzer

def download_bytes(args):
    src = OfflineReplayer()
    src.set_input_file(db['mi2log'].find_one({'filename': args['filename']})['data'])

    if args['type_id']:
        for type_id in args['type_id']:
            src.enable_log(type_id, args['start_date'], args['end_date'])
    else:
        src.enable_log_all(args['start_date'], args['end_date'])

    # analyzer = myAnalyzer()
    # analyzer.set_source(src)
    src.run()
    return bytes(src.output_bytes_object)