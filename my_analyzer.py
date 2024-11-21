import json
from pymongo import MongoClient
from gridfs import GridFS

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

    def __msg_callback(self, msg):
        msg_fields = {}
        data = msg.data.decode_json()
        data = json.loads(data)

        # get the identifying fields like type_id, timestamp, msg_len, etc.
        for k in data.keys():
            if k != "Msg":
                msg_fields[k] = data[k]

        # get Msg contents of Log message
        if "Msg" in data.keys():
            log_xml = ET.XML(data["Msg"])
        else:
            self.field_list.append(msg_fields)
            return

        xml_msg = Event(msg.timestamp, msg.type_id, log_xml)

        msg_dict = {}
        for field in xml_msg.data.iter("field"):
            if field.get("showname") != None and field.get("value") != None:
                showname = field.get("showname")
                mask = np.array([char.isalpha() for char in list(showname)])
                start_idx = np.where(mask)[0][0]
                msg_dict[showname[start_idx:]] = field.get("value")

        msg_fields["Msg"] = msg_dict
        self.field_list.append(msg_fields)


client = MongoClient("localhost", 27017)
db = client["mobile_insight"]


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
    file_id = db["mi2log"].find_one({"filename": args["filename"]})["data_id"]
    # Retrieve the file data from GridFS
    file_data = GridFS(db).get(file_id).read()
    src.set_input_file(file_data)

    if args["type_id"]:
        for type_id in args["type_id"]:
            src.enable_log(type_id, args["start_date"], args["end_date"])
    else:
        src.enable_log_all(args["start_date"], args["end_date"])

    src.run()
    return bytes(src.output_bytes_object)
