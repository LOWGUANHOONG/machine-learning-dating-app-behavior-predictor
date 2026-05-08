@echo off
d:
cd "ML autosklearn"
docker run --rm -it -v "%cd%:/opt/nb" -p 8888:8888 mfeurer/auto-sklearn:master /bin/bash -c "mkdir -p /opt/nb && jupyter notebook --notebook-dir=/opt/nb --ip='0.0.0.0' --port=8888 --no-browser --allow-root"
pause