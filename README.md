# CS219

MobileInsight-Cloud (Cloud service and Web interface of MobileInsight)

## Usage

1. First install MobileInsight. Please refer to https://github.com/mobile-insight/mobileinsight-core/tree/ubuntu22-py310.
2. Follow the report to modify the source code of MobileInsight and recompile it.
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
python3 ./examples/offline-analysis-filtering.py
```

