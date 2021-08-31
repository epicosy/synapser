#!/bin/bash

# Setting Timezone
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

apt-get install -y postgresql libpq-dev && pip3 install -r requirements.txt
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser dependencies." && exit 1 ;

pip3 install .
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser." && exit 1 ;

# Init DB
su -l postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER synapser WITH SUPERUSER PASSWORD 'synapser123';\" && createdb synapser && exit"

#Configs
config_path="/etc/synapser"
config_plugin_path="/etc/synapser/plugin"
plugins_path="/var/lib/synapser/plugin/tool"
mkdir -p $config_path && cp "config/synapser.yml" $config_path && mkdir -p $config_plugin_path && mkdir -p $plugins_path
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser configs." && exit 1 ;
