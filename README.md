# example-analyzer.py

## Location:
Place and run this file in: mobileinsight-core/examples

## Parameters 
1. input_path: either a file or directory containing logs
2. outfile_name: name of output .json file 

## .json file format
.json file maps from {Log file name: [List of Dictionaries per Log Message]}

- Each log file contains multiple log messages.
- Each log message is represented as a dictionary. 
- **Some** log messages have a "Msg" key.

- Please see how_logs_json_looks.png for a snipit of how the generated logs.json looks.
- Please see **only_1_log_bc_size.json** as an example. Note: This is only 1 log file in the ./example/logs directory because of GitHub size constraint.


