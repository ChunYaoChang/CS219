from flask import Flask, jsonify, request
import redis

r = redis.Redis(
    host='redis-10435.c14.us-east-1-2.ec2.redns.redis-cloud.com',
    port=10435,
    password='BHzTa6uOoVa9F34BwZNDXxCNs7HnzEFn'
)
app = Flask(__name__)

@app.route('/')
def home_page():
    return 'Just a home page'

@app.route('/keys', methods=['POST'])
def show_keys():
    type_id = request.form.get('type_id', default='', type=str)
    filename = request.form.get('filename', default='', type=str)
    keys = [s.decode() for s in r.keys(pattern=f'*{filename}*:*{type_id}:*')]
    return jsonify({'keys': keys})

@app.route('/content', methods=['POST'])
def show_contents():
    key_name = request.form.get('key_name', default='', type=str)
    data = r.json().get(key_name)
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=1234, debug=True)