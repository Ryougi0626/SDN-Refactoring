"""
Failure management module
Handle link failures and state changes
"""

import os
import random
import re
import time
import numpy as np


class FailureManager:
    """Failure manager"""
    
    def __init__(self, logger, config_manager):
        self.logger = logger
        self.config_manager = config_manager
        
        # Markov chain transition matrix
        self.transition_matrix = np.array([
            [0.3, 0.5, 0.2],
            [0.4, 0.2, 0.4],
            [0.3, 0.5, 0.2]
        ])
    
    def simulate_markov_chain(self, trans_matrix, start_state, num_steps):
        """Simulate Markov chain"""
        current_state = start_state
        sequence = [current_state]
        
        for _ in range(num_steps):
            next_state = np.random.choice([0, 1, 2], p=trans_matrix[current_state])
            sequence.append(next_state)
            current_state = next_state
        
        return sequence
    
    def extract_number_and_decrement(self, s):
        """Extract number and decrement by 1"""
        return str(int(s[1:]) - 1)
    
    def single_link_failure_model(self, addr_to_host, traffic_flows):
        """Single link failure model"""
        link_to_traffic_flows = {}
        traffic_flow_paths = []
        
        f = open("./traffic_flow_paths.txt")
        raw_data_set = f.read().splitlines()
        
        for raw_data in raw_data_set:
            raw_data = raw_data.split('|')
            traffic_flow = raw_data[0].split(',')
            path = list(map(lambda x: 's' + str(x + 1), eval(raw_data[1])))
            path.insert(0, traffic_flow[0].lower())
            path.append(traffic_flow[1].lower())
            traffic_flow_paths.append(path)
        
        for path in traffic_flow_paths:
            path = list(map(lambda x: "s" + str(int(x.replace('of:', ""), 16))
                           if "of:" in x else x, list(map(str, path))))
            src = path.pop(0)
            dst = path.pop()
            
            for i in range(len(path)):
                j = i + 1
                if j < len(path):
                    uselink = (path[i], path[j])
                    if uselink not in link_to_traffic_flows.keys():
                        link_to_traffic_flows.setdefault(uselink, [])
                    if (uselink[1], uselink[0]) not in link_to_traffic_flows.keys():
                        link_to_traffic_flows.setdefault((uselink[1], uselink[0]), [])
                    if (addr_to_host[src], addr_to_host[dst]) in traffic_flows:
                        link_to_traffic_flows[uselink].append((addr_to_host[src], addr_to_host[dst]))
        
        max_flow = 0
        for link in link_to_traffic_flows.keys():
            if len(link_to_traffic_flows[link]) + len(link_to_traffic_flows[(link[1], link[0])]) > max_flow:
                failed_link = link
                max_flow = len(link_to_traffic_flows[link]) + len(link_to_traffic_flows[(link[1], link[0])])
        
        self.logger.log_timestamp('Failed link generation Completed')
        
        affected_traffic_flows = []
        for affected_traffic_flow in link_to_traffic_flows[failed_link]:
            if affected_traffic_flow not in affected_traffic_flows:
                affected_traffic_flows.append(affected_traffic_flow)
        
        for affected_traffic_flow in link_to_traffic_flows[(failed_link[1], failed_link[0])]:
            if affected_traffic_flow not in affected_traffic_flows:
                affected_traffic_flows.append(affected_traffic_flow)
        
        self.logger.log_failed_link(failed_link)
        self.logger.log_affected_flows(affected_traffic_flows)
        
        return failed_link, affected_traffic_flows
    
    def multiple_link_failure_model(self, addr_to_host, traffic_flows):
        """Multiple link failure model"""
        link_to_traffic_flows = {}
        failed_links = []
        affected_flows = []
        affected_traffic_flows = []
        
        with open('./traffic_flow_backup_paths.txt', 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                addr, paths_s = line.split('|')
                dict_now_mac = {int(k): [int(s) for s in v.split(', ')] for k, v in re.findall(r'(\d+)=\[([0-9, ]*)\]', paths_s[1:-1])}
                
                if len(dict_now_mac) == 2:
                    with open('./traffic_flow_paths.txt', 'r') as fp_2:
                        lines_2 = fp_2.readlines()
                        for line_2 in lines_2:
                            if addr in line_2:
                                addr_2, paths_s_2 = line_2.split('|')
                                paths_s_2 = paths_s_2[1:-1].rstrip(']')
                                main_path = paths_s_2.split(',')
                                main_path = [element.strip() for element in main_path]
                                failed_links.append(('s' + str(int(main_path[0]) + 1), 's' + str(int(main_path[1]) + 1)))
                                affected_flows.append(('h' + str(int(main_path[0]) + 1) + '_0', 'h' + str(int(main_path[len(main_path) - 1]) + 1) + '_0'))
                                affected_flows.append(('h' + str(int(main_path[len(main_path) - 1]) + 1) + '_0', 'h' + str(int(main_path[0]) + 1) + '_0'))
                                break
                    
                    for k in dict_now_mac:
                        failed_links.append(('s' + str(dict_now_mac[k][0] + 1), 's' + str(dict_now_mac[k][1] + 1)))
                        break
                    break
        
        for flow in affected_flows:
            if flow in traffic_flows:
                affected_traffic_flows.append(flow)
        
        self.logger.log_timestamp(f"Failed links: {failed_links}")
        self.logger.log_timestamp(f"Affected traffic flow set: {affected_traffic_flows}")
        
        return failed_links, affected_traffic_flows
    
    def link_state_change(self, link, u_v_connection, state, link_state='', target_bw=0):
        """Change link state"""
        switch_name = link[0]
        port = u_v_connection[link[0]][link[1]]
        
        cmd = "sudo ovs-ofctl mod-port " + switch_name + " " + port + " " + state
        now_time = time.time()
        
        if link_state == 'pnlos':
            with open('./failed_link_bw.txt', 'w') as f:
                f.write('pnlos\n')
                f.write(f'{target_bw}\n')
                f.write(f'{self.extract_number_and_decrement(link[0])}\n')
                f.write(f'{self.extract_number_and_decrement(link[1])}\n')
                f.close()
        elif link_state == 'los':
            with open('./failed_link_bw.txt', 'w') as f:
                f.write('los\n')
                f.write(f'{target_bw}\n')
                f.write(f'{self.extract_number_and_decrement(link[0])}\n')
                f.write(f'{self.extract_number_and_decrement(link[1])}\n')
                f.close()
        elif link_state == 'fnlos':
            with open('./failed_link_bw.txt', 'w') as f:
                f.write('fnlos\n')
                f.write('0\n')
                f.write(f'{self.extract_number_and_decrement(link[0])}\n')
                f.write(f'{self.extract_number_and_decrement(link[1])}\n')
                f.close()
        
        os.system(cmd)
        return now_time
    
    def bw_change(self, link, u_v_connection, smooth_change, target_bw, net, link_state_flag, algorithm=''):
        """Change bandwidth"""
        if target_bw != 0 and target_bw != 1000:
            if link_state_flag:
                self.link_state_change(link, u_v_connection, "down")
            now_time = self.link_state_change(link, u_v_connection, "up", 'pnlos', target_bw)
        elif target_bw == 1000:
            if link_state_flag:
                self.link_state_change(link, u_v_connection, "down")
            now_time = self.link_state_change(link, u_v_connection, "up", 'los', target_bw)
        elif target_bw == 0:
            now_time = self.link_state_change(link, u_v_connection, "down", 'fnlos', 0)
        
        if target_bw != 0:
            switch_name = link[0]
            switch_name2 = link[1]
            port = u_v_connection[link[0]][link[1]]
            port2 = u_v_connection[link[1]][link[0]]
            switch = net.get(switch_name)
            switch2 = net.get(switch_name2)
            
            for sw_port, intf in switch.intfs.items():
                if str(sw_port) == port:
                    intf.config(bw=target_bw, smooth_change=smooth_change)
                    break
            for sw_port, intf in switch2.intfs.items():
                if str(sw_port) == port2:
                    intf.config(bw=target_bw, smooth_change=smooth_change)
                    break
        
        # SDFFR special handling
        if algorithm.startswith('SDFFR'):
            switch_name = link[0]
            switch_name2 = link[1]
            port = u_v_connection[link[0]][link[1]]
            port2 = u_v_connection[link[1]][link[0]]
            self.logger.log(f'switch1 = {switch_name}, port1 = {port}, switch2 = {switch_name2}, port2 = {port2}, target_bw = {target_bw}')
            
            if target_bw != 1000:
                # Need to import flow_table_change function
                try:
                    from switch_ff import flow_table_change
                    flow_table_change(switch_name, port, "down")
                    flow_table_change(switch_name2, port2, "down")
                except ImportError:
                    self.logger.log("flow_table_change function not available")
            else:
                try:
                    from switch_ff import flow_table_change
                    flow_table_change(switch_name, port, "up")
                    flow_table_change(switch_name2, port2, "up")
                except ImportError:
                    self.logger.log("flow_table_change function not available")
        
        return now_time
    
    def path_record(self, trace_folder, label, state, mode='markov'):
        """Record paths"""
        if state == 'after link failure':
            if os.path.isfile('./traffic_flow_paths.txt'):
                if mode == 'markov':
                    os.system('sudo cp ./traffic_flow_paths.txt ' + trace_folder + 'markov_chain/' + label + '/main_path.txt')
                    os.system('sudo chown -R ' + self.config_manager.username + ' ' + trace_folder + 'markov_chain/' + label + '/main_path.txt')
                else:
                    os.system('sudo cp ./traffic_flow_paths.txt ' + trace_folder + 'fixed_version/' + label + '/main_path.txt')
                    os.system('sudo chown -R ' + self.config_manager.username + ' ' + trace_folder + 'fixed_version/' + label + '/main_path.txt')
                
                if os.path.isfile('./traffic_flow_backup_paths.txt'):
                    if mode == 'markov':
                        os.system('sudo cp ./traffic_flow_backup_paths.txt ' + trace_folder + 'markov_chain/' + label + '/backup_path.txt')
                        os.system('sudo chown -R ' + self.config_manager.username + ' ' + trace_folder + 'markov_chain/' + label + '/backup_path.txt')
                    else:
                        os.system('sudo cp ./traffic_flow_backup_paths.txt ' + trace_folder + 'fixed_version/' + label + '/backup_path.txt')
                        os.system('sudo chown -R ' + self.config_manager.username + ' ' + trace_folder + 'fixed_version/' + label + '/backup_path.txt')
    
    def analysis_trace_file(self, failure_mode, algorithm, trace_folder, label, data, host_map):
        """Analyze trace file"""
        if failure_mode == 'single':
            sub_trace_folder = trace_folder + 'markov_chain/' + label + '/'
        else:
            sub_trace_folder = trace_folder + 'fixed_version/' + label + '/'
        
        if failure_mode == 'single':
            file_path = sub_trace_folder + 'timestamp_record.txt'
            order = ['status1_start', 'status1_stop', 'status2_start', 'status2_stop',
                     'status3_start','status3_stop','status4_start', 'status4_stop',
                     'status5_start','status5_stop']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')

            file_path = sub_trace_folder + 'Affected_traffic_flows_rocord.txt'
            order = ['affected_traffic_flows']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')

            file_path = sub_trace_folder + 'link_change_time.txt'
            order = data['change']
            with open(file_path, 'w') as f:
                for link_change_time in order:
                    f.write(str(link_change_time)+'\n')
            
            file_path = sub_trace_folder + 'failed_link_rocord.txt'
            order = ['failed_link']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')
            if algorithm == 'DRAF':
                file_path = sub_trace_folder + 'addflow_to_addr.txt'
                order = 'affected_traffic_flows'
                with open(file_path, 'w') as f:
                    for value in data[order]:
                        f.write(str(value[0])+' '+str(value[1])+' '+host_map[value[0]].MAC().upper()+','+host_map[value[1]].MAC().upper()+'\n')
        elif failure_mode == 'multiple':
            file_path = sub_trace_folder + 'timestamp_record.txt'
            order = ['los1_start', 'los1_stop', 'fnlos1_start', 'fnlos1_stop',
                     'fnlos2_start','fnlos2_stop','los2_start', 'los2_stop',
                     'los3_start','los3_stop']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')

            file_path = sub_trace_folder + 'Affected_traffic_flows_rocord.txt'
            order = ['affected_traffic_flows']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')

            file_path = sub_trace_folder + 'link_change_time.txt'
            order = ['change_1', 'change_2','change_3','change_4']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')
            
            file_path = sub_trace_folder + 'failed_link_rocord.txt'
            order = ['failed_links']
            with open(file_path, 'w') as f:
                for key in order:
                    if key in data:
                        value = data[key]
                        f.write(str(value)+'\n')

        self.logger.log_timestamp('Analysis result completed') 