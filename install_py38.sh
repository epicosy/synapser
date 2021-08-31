#!/bin/bash

# Setting Timezone
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

apt-get update

# Install Python 3.8.10
cd /tmp && wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
[[ $? -eq 1 ]] && echo "[Error] Failed to download Python 3.8.10" && exit 1 ;
tar -xvzf Python-3.8.10.tgz
[[ $? -eq 1 ]] && echo "[Error] Failed to extract Python 3.8.10 tar" && exit 1 ;
cd Python-3.8.10 && ./configure && make -j 4
[[ $? -eq 1 ]] && echo "[Error] Failed to build Python 3.8.10" && exit 1 ;
make install
[[ $? -eq 1 ]] && echo "[Error] Failed to install Python 3.8.10" && exit 1 ;

# Set default version of Python 3 to 3.8.10
cp /usr/local/bin/python3.8 /usr/bin
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2
[[ $? -eq 1 ]] && echo "[Error] Failed to set default version of Python 3 to 3.8.10" && exit 1 ;


# Install pip for Python 3.8
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to download pip for Python 3" && exit 1 ;
python3 get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to install pip for Python 3" && exit 1 ;

# Update lsb_release for pip3 install
python38="\# \!\/usr\/bin\/python3.8 -Es"
sed -i "1s/.*/$python38/" /usr/bin/lsb_release && ln -s /usr/share/pyshared/lsb_release.py /usr/local/lib/python3.8/site-packages/lsb_release.py
[[ $? -eq 1 ]] && echo "[Error] Failed to update lsb_release to python3.8" && exit 1 ;