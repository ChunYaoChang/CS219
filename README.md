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

