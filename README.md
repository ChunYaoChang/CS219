# CS219

MobileInsight-Cloud (Cloud service and Web interface of MobileInsight)

## Prerequisite

1. Install MobileInsight. Please refer to https://github.com/mobile-insight/mobileinsight-core/tree/ubuntu22-py310.
2. Install Docker. Please refer to https://docs.docker.com/engine/install/ubuntu/.
3. Install RedisJSON. Please refer to https://github.com/RedisJSON/RedisJSON.

## Usage

1. Ssh to the server.
```bash
# port 8501 for streamlit, port 6379 for redis
ssh -L 8501:localhost:8501 -L 6379:localhost:6379 -p 3722 chunyao@131.179.22.71
```
2. Follow the report to modify the source code of MobileInsight and recompile it. Or refer to `timestamp_filter.zip`.
3. Install dependencies by running the following command.
```bash
pip install -r requirement.txt
```
4. Run MobileInsight Cloud.
```bash
streamlit run gui.py
```

## Compilation
This repo supports timestamp-based filtering which requires recompiling modified code. To recompile, follow these steps:
```bash
cd mobileinsight-core
sudo python3 setup.py bdist_wheel
sudo pip install ./dist/MobileInsight-6.0.0-cp310-cp310-linux_x86_64.whl --force-reinstall
```

