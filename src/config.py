"""
Configuration management module
Handle experiment configuration, file operations and system settings
"""

import json
import os
import pickle
import subprocess
import time
import requests
from requests.auth import HTTPBasicAuth


class ConfigManager:

    def __init__(self, username):
        self.username = username
    
    def read_config_file(self, config_file_name):
        with open(config_file_name, 'r') as load_f:
            return json.load(load_f)
    
    def build_folder(self, folder, check):
        if check:
            if os.path.isdir(folder):
                os.system('sudo rm -r ' + folder)
            if not os.path.isdir(folder):
                os.mkdir(folder)
                os.system('sudo chown -R ' + self.username + ' ' + folder)
        else:
            if not os.path.isdir(folder):
                os.mkdir(folder)
                os.system('sudo chown -R ' + self.username + ' ' + folder)
            return folder
    
    def build_pickle(self, file, data, check_file_exist=False):
        if check_file_exist:
            if not os.path.isfile(file):
                pickle.dump(data, open(file, 'wb'))
        else:
            pickle.dump(data, open(file, 'wb'))
        os.system('sudo chown -R ' + self.username + ' ' + file)
        return file
    
    def build_json(self, file, data):
        with open(file, 'w') as f:
            json.dump(data, f)
        os.system('sudo chown -R ' + self.username + ' ' + file)
    
    def build_text(self, text_name, data, element=True, valid_element=[True], operation='a'):
        if element in valid_element:
            with open(text_name, operation) as f:
                f.write(data)
                f.write('\n')
            os.system('sudo chown -R ' + self.username + ' ' + text_name)
    
    def build_log_file(self, log_file):
        with open(log_file, 'w') as f:
            f.truncate()
        os.system('sudo chown -R ' + self.username + ' ' + log_file)
        return log_file
    
    def read_output_file(self, file):
        with open(file, 'rb') as f:
            return pickle.load(f)


class ONOSConfig:

    @staticmethod
    def configure_onos():
        base_url = "http://localhost:8181/onos/v1"
        username = "onos"
        password = "rocks"
        
        config_url = f"{base_url}/configuration/org.onosproject.net.flow.impl.FlowRuleManager"
        
        payload = {
            "allowExtraneousRules": True,
            "importExtraneousRules": True
        }
        
        try:
            response = requests.post(config_url, json=payload, auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                print("Configuration updated successfully!")
            else:
                print(f"Failed to update configuration: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {e}")
    
    @staticmethod
    def reset_onos():
        script_path = os.path.expanduser('~/yukai_thesis/reset_onos/reset_onos.py')
        subprocess.Popen(['sudo', 'python3', script_path])
        time.sleep(30)
        
        while True:
            url = "http://localhost:8181/onos/v1/applications/org.onosproject.openflow/active"
            auth = HTTPBasicAuth("onos", "rocks")
            
            response = requests.post(url, headers={"Accept": "application/json"}, auth=auth)
            if response.status_code == 200:
                return
            time.sleep(10)


class SystemManager:

    @staticmethod
    def kill_process(cmd):

        os.system('sudo python3 pid_kill.py ' + cmd)
    
    @staticmethod
    def kill_ovs_pid():

        os.system('sudo rmmod openvswitch')
        os.system('sudo killall ovsdb-server')
        os.system('sudo killall ovs-vswitchd')
    
    @staticmethod
    def setup_ovs_pid():

        os.system('sudo modprobe gre')
        os.system('sudo modprobe openvswitch')
        os.system('sudo modprobe libcrc32c')
        os.system('sudo rm /usr/local/etc/openvswitch/conf.db')
        os.system('sudo ovsdb-tool create /usr/local/etc/openvswitch/conf.db /usr/local/share/openvswitch/vswitch.ovsschema')
        os.system('sudo ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock --remote=db:Open_vSwitch,Open_vSwitch,manager_options  --private-key=db:Open_vSwitch,SSL,private_key --certificate=db:Open_vSwitch,SSL,certificate --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert --pidfile --detach --log-file')
        os.system('sudo ovs-vsctl --no-wait init')
        os.system('sudo ovs-vswitchd --pidfile --detach --log-file')
        os.system('sudo ovs-vsctl --version')
    
    @staticmethod
    def reset_all():

        os.system('sudo mn -c')
        time.sleep(5)
        SystemManager.kill_ovs_pid()
        time.sleep(3)
        SystemManager.setup_ovs_pid()
        time.sleep(3)
        ONOSConfig.reset_onos()
    
    @staticmethod
    def control_plane_delay_setup(control_plane_delay, action):

        if action == 'add':
            os.system('sudo tc qdisc add dev lo root netem delay ' + str(control_plane_delay) + 'ms')
        elif action == 'delete':
            os.system('sudo tc qdisc del dev lo root netem delay ' + str(control_plane_delay) + 'ms') 