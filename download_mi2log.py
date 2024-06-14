#!/usr/bin/python
import os
import sys
from datetime import datetime
import pickle
import redis
# Import MobileInsight modules
from mobile_insight.monitor import OfflineReplayer

r = redis.Redis(
    host='127.0.0.1',
    port=6379
)

if __name__ == '__main__':
    args = pickle.loads(eval(sys.argv[1]))
    cur_path = os.getcwd()
    file_path = os.path.join(cur_path, 'tmp.mi2log')
    with open(file_path, 'wb') as file:
        file.write(r.get(f'{args["filename"]}:mi2log'))

    src = OfflineReplayer()
    src.set_input_path(os.path.join(cur_path, 'tmp.mi2log'))

    if args['type_ids']:
        for type_id in args['type_ids']:
            src.enable_log(type_id, args['start_date'], args['end_date'])
    else:
        src.enable_log_all(args['start_date'], args['end_date'])

    src.save_log_as(os.path.join(cur_path, 'filtered_log.mi2log'))
    src.run()