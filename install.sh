#!/bin/bash

# Update the package list
DEBIAN_FRONTEND=noninteractive apt-get update 2>&1

# Setting Timezone
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata 2>&1

apt-get install -y postgresql libpq-dev && pip3 install -r requirements.txt 2>&1
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser dependencies." && exit 1 ;

pip3 install . 2>&1
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser." && exit 1 ;

# Init DB
su -l postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER synapser WITH SUPERUSER PASSWORD 'synapser123';\"" 2>&1

#Configs
config_path="/etc/synapser"
config_plugin_path="/etc/synapser/plugins.d"
plugins_path="/var/lib/synapser/plugins/tool"
mkdir -p $config_path && cp "config/synapser.yml" $config_path
mkdir -p $config_plugin_path && cp -a "config/plugins/." $config_plugin_path
mkdir -p $plugins_path && cp -a "synapser/plugins/." $plugins_path
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser configs." && exit 1 ;
