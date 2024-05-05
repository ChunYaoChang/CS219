import json

filename = 'test.json'
out_file = 'all_types.json'

type_dict = {}

# Function to parse multiple JSON objects in a single file
def parse_multiple_jsons(file):
    cnt = 0
    content = ''
    for line in file:
        content += line.strip()
        try:
            obj = json.loads(content)
            yield obj
            content = ''
        except json.JSONDecodeError:
            continue  # Continue accumulating content if JSON is incomplete

with open(filename, 'r') as file:
    cnt = 0
    output = []
    for block in parse_multiple_jsons(file):
        type_id = block['type_id']
        if type_id in type_dict:
            type_dict[type_id] += 1
        else:
            type_dict[type_id] = 1
        if type_dict[type_id] <= 3:
            print(block)  # Print each JSON block
            output.append(block)

with open(out_file, 'w') as outfile:
    json.dump(output, outfile, indent=4)
