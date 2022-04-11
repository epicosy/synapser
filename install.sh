#!/bin/bash

# Setting Timezone
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata 2>&1

apt-get install -y postgresql libpq-dev && pip3 install -r requirements.txt 2>&1
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser dependencies." && exit 1 ;

pip3 install . 2>&1
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser." && exit 1 ;

# Init DB
su -l postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER synapser WITH SUPERUSER PASSWORD 'synapser123';\" && createdb synapser" 2>&1

#Configs
mkdir -p ~/.synapser/config/plugins.d && mkdir -p ~/.synapser/plugins && cp config/synapser.yml ~/.synapser/config/
[[ $? -eq 1 ]] && echo "[Error] Failed to install synapser configs." && exit 1 ;
echo "[Success] Created default configuration file paths."

synapser plugin install -d $SYNAPSER_PLUGIN_PATH 2>&1
[[ $? -eq 1 ]] && echo "[Error] Failed to install plugin." && exit 1 ;

echo "[Success] Installed $SYNAPSER_PLUGIN_PATH plugin."
exit 0