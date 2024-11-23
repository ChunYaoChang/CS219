# MobileInsight-Cloud

**MobileInsight-Cloud** is a cloud-based iteration of the original [MobileInsight](https://github.com/mobile-insight/mobileinsight-core/tree/ubuntu22-py310) tool, designed to enhance accessibility and streamline functionality. With this version, users can visualize, filter, upload, and download logs directly from a client machine—eliminating the need to install MobileInsight locally.  

This cloud solution leverages [Streamlit](https://streamlit.io/), a powerful framework for building and sharing interactive data applications, to provide a user-friendly interface. For data storage, [MongoDB](https://www.mongodb.com) is utilized to ensure efficient and scalable management of log files.  

MobileInsight-Cloud is your go-to platform for seamless log management in a cloud-based environment.

## Prerequisite

1. Install [MobileInsight](https://github.com/mobile-insight/mobileinsight-core/tree/ubuntu22-py310).
2. Follow the [pull request](https://github.com/mobile-insight/mobileinsight-core/pull/139) to modify the source code of MobileInsight.
3. Recompile the source code via the following steps:
```bash
cd mobileinsight-core
sudo python3 setup.py bdist_wheel
sudo pip install ./dist/MobileInsight-6.0.0-cp310-cp310-linux_x86_64.whl --force-reinstall
```
4. Install [MongoDB](https://www.mongodb.com).

## Usage

1. Ssh to the server.
```bash
# port 8501 for streamlit (ssh port forwarding)
ssh -L 8501:localhost:8501 [user@server_ip]
```
2. Install dependencies by running the following command.
```bash
pip install -r requirements.txt
```
3. Run MobileInsight Cloud.
```bash
streamlit run app.py
```