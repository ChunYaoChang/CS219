# CS219

MobileInsight-Cloud (Cloud service and Web interface of MobileInsight)

## Redis

Currently, I use Redis Cloud as temporary solution because I don't have sudo permission on share environment. Will discuss with TA next Monday. You can connect the Redis with the following instruction.

```python
# python

import redis

r = redis.Redis(
    host='redis-10435.c14.us-east-1-2.ec2.redns.redis-cloud.com',
    port=10435,
    password='BHzTa6uOoVa9F34BwZNDXxCNs7HnzEFn'
)
```

```js
import { createClient } from 'redis';

const client = createClient({
    password: 'BHzTa6uOoVa9F34BwZNDXxCNs7HnzEFn',
    socket: {
        host: 'redis-10435.c14.us-east-1-2.ec2.redns.redis-cloud.com',
        port: 10435
    }
});
```

## Flask Backend

Please refer to `backend.py` and `ugly_frontend.html`.


## example-analyzer.py

## Location:
Place and run this file in: mobileinsight-core/examples

## Parameters 
1. input_path: either a file or directory containing logs
2. outfile_name: name of output .json file 

## .json file format
.json file maps from {Log file name: [List of Dictionaries, one per Log Message]}

- Each log file contains multiple log messages.
- Each log message is represented as a dictionary. 
- **Some** log messages have a "Msg" key.

### Example
- See offline_log_examples_2.json
- Parses two .mi2log files inside ./logs/offline_log_examples directory

