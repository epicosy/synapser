#!/bin/bash

apt-get install -y postgresql libpq-dev && pip3 install -r requirements.txt
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser dependencies." && exit 1 ;

pip3 install setup.py
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser." && exit 1 ;

# Init DB
sudo -u postgres -i
/etc/init.d/postgresql start
psql --command "CREATE USER synapser WITH SUPERUSER PASSWORD 'synapser123';"
createdb synapser
exit

#Configs
config_path="/etc/synapser"
config_plugin_path="/etc/synapser/plugin"
mkdir -p $config_path && cp "config/synapser.yml" $config_path && mkdir -p $config_plugin_path
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser configs." && exit 1 ;
