import csv
import json
import os

import numpy as np
try:
    import xml.etree.cElementTree as ET 
except ImportError:
    import xml.etree.cElementTree as ET  

from mobile_insight.analyzer.analyzer import*
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
        data = msg.data.decode()
        # get the identifying fields like type_id, timestamp, msg_len, etc.
        for k in data.keys():
            if k != 'Msg' and k != 'timestamp':
                msg_fields[k] = data[k]
            if k == 'timestamp':
                # print(type(data[k]))
                # print(data[k].strftime("%Y-%m-%d %H:%M:%S.%f"))
                msg_fields[k] = data[k].strftime("%Y-%m-%d %H:%M:%S.%f")
                # # convert datatype into a string

        # get Msg contents of Log message
        if 'Msg' in data.keys():
            log_xml = ET.XML(data['Msg'])
        else:
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
            

def my_analysis(input_path):
    src = OfflineReplayer()
    src.set_input_path(input_path)

    analyzer = myAnalyzer()
    analyzer.set_source(src)
    src.run()

    return analyzer

input_path = "./logs/"
outfile_name = "logs.json"

# get all log files in a directory
log_list = []
if os.path.isfile(input_path):
    log_list = [input_path]
elif os.path.isdir(input_path):
    for file in os.listdir(input_path):
        if file.endswith(".mi2log") or file.endswith(".qmdl"):
            # log_list.append(self._input_path+"/"+file)
            log_list.append(os.path.join(input_path, file))
            # log_list.append(file)
else:
    print("ERROR!")

logs = {}
for log_input in log_list:
    stats = my_analysis(log_input)
    if len(stats.field_list) > 0:
        # stats.field_list = log messages in each log file
        logs[log_input] = stats.field_list
with open(outfile_name, "w") as outfile:
    json.dump(logs, outfile, indent=4)

print(logs.keys())

# # TA's .csv version
# fout = open('outlog1.csv', 'a')
# writer = csv.writer(fout)
# writer.writerow([input_path])
# for item in stats.field_list:
#     writer.writerow(item)
# fout.close()

 