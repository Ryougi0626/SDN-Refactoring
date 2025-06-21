"""
Experiment main module
Integrate all functions and provide unified experiment interface
"""

import gc
import os
import sys
import time
import traceback
import random
from threading import Event, Thread

from .config import ConfigManager, SystemManager
from .logger import Logger
from .topology import TopologyManager
from .algorithm import AlgorithmManager
from .traffic import TrafficManager
from .failure import FailureManager


class ExperimentRunner:

    def __init__(self, config_file, username):
        self.config_manager = ConfigManager(username)
        self.cfg_file = self.config_manager.read_config_file(config_file)
        self.logger = Logger()
        self.topology_manager = TopologyManager(self.logger)
        self.algorithm_manager = AlgorithmManager(self.logger)
        self.traffic_manager = TrafficManager(self.logger, self.config_manager)
        self.failure_manager = FailureManager(self.logger, self.config_manager)
        
  
        self.trace_folder = None
        self.log_folder = None
        self.result_folder = None
        
    def setup_experiment_environment(self, failure_mode):
        self.trace_folder = self.config_manager.build_folder(f'./Trace_folder/{failure_mode}/')
        num = self.config_manager.build_folder('./' + ''.join([x for x in str(sys.argv[2]) if x.isdigit()]))
        self.result_folder = self.config_manager.build_folder(num + '/result_folder/')
        self.log_folder = self.config_manager.build_folder(num + '/log_folder/')
        
        return num
    
    def create_experiment_label(self, algorithm, vertex, edge, link_bandwidth, throughput, traffic_model, control_plane_delay, flow_count, trial):
        return f"{algorithm}_{vertex}_{edge}_{link_bandwidth}_{throughput}_{traffic_model}_{control_plane_delay}_{flow_count}_{trial}"
    
    def setup_experiment_files(self, label, failure_mode, mode):
        self.config_manager.build_text('./BW.txt', str(self.cfg_file['LinkBandwidth'][0]))
        self.config_manager.build_text('./flow_throughput.txt', str(self.cfg_file['Throughput'][0]))
        self.config_manager.build_text('./result_folder_label.txt', ''.join([x for x in str(sys.argv[2]) if x.isdigit()]))
        self.config_manager.build_text('./label.txt', str(label))
        self.config_manager.build_text('./linkdown_mode.txt', str(failure_mode))
        self.config_manager.build_text('./mode.txt', mode)
        self.config_manager.build_text('./failed_link_bw.txt', '')
        
        ## note: maybe not necessary
        if os.path.isfile('traffic_mac.txt'):
            os.system('sudo rm ./traffic_mac.txt')
    
    def setup_network_topology(self, edge_set, vertex_set, flow_count, link_bandwidth):
        self.logger.log_timestamp('Build mininet topology')
        net, host_map, switch_map, traffic_flows, host_to_IP = self.topology_manager.build_topo(
            edge_set, vertex_set, flow_count, link_bandwidth)
        
        traffic_flows = [('h20_0', 'h6_0'), ('h5_0', 'h9_0'), ('h7_0', 'h2_0'), ('h3_0', 'h15_0'), 
                        ('h6_0', 'h10_0'), ('h6_0', 'h8_0'), ('h18_0', 'h8_0'), ('h6_0', 'h18_0'), 
                        ('h4_0', 'h11_0'), ('h10_0', 'h8_0'), ('h12_0', 'h8_0'), ('h2_0', 'h17_0'), 
                        ('h11_0', 'h8_0'), ('h11_0', 'h20_0'), ('h8_0', 'h19_0'), ('h2_0', 'h8_0'), 
                        ('h3_0', 'h9_0'), ('h9_0', 'h15_0'), ('h18_0', 'h9_0'), ('h14_0', 'h6_0'), 
                        ('h4_0', 'h17_0'), ('h20_0', 'h8_0'), ('h5_0', 'h18_0'), ('h2_0', 'h14_0'), 
                        ('h8_0', 'h7_0'), ('h10_0', 'h5_0'), ('h13_0', 'h5_0'), ('h20_0', 'h14_0'), 
                        ('h4_0', 'h20_0'), ('h14_0', 'h8_0'), ('h18_0', 'h2_0')]
        
        self.logger.log_timestamp('Create host to address data')
        host_to_addr, addr_to_host = self.topology_manager.create_host_to_addr_location_file(net, self.config_manager)
        
        self.logger.log_timestamp('Create traffic flows file')
        self.topology_manager.create_traffic_flows_file(traffic_flows, host_to_addr, self.config_manager)
        
        self.logger.log_timestamp('Create switch connection data')
        u_v_connection = self.topology_manager.create_u_v_connection(switch_map, edge_set)
        
        time.sleep(10)
        
        self.logger.log_timestamp('Check controller connectivity')
        self.topology_manager.check_controller_connectivity(len(edge_set))
        
        return net, host_map, switch_map, traffic_flows, host_to_IP, host_to_addr, addr_to_host, u_v_connection
    
    def run_single_link_failure_experiment(self, traffic_model, algorithm, traffic_flows, host_map, addr_to_host, u_v_connection, label, net, throughput, mode='markov'):
        try:
            # Read link_change_time parameter from config file
            link_change_time = self.cfg_file.get('LinkChangeTime', [5])[0]
            status_start = []
            status_stop = []
            change = []
            link_state_flag = True
            change_counter = 0
            
            if mode == 'markov':
                status_list = self.failure_manager.simulate_markov_chain(
                    self.failure_manager.transition_matrix, 0, 4)
            else:
                status_list = [0, 1, 2, 1, 0]
            
            self.logger.log(f'status_list: {status_list}')
            self.logger.log(f'link_change_time: {link_change_time}')
            
            failed_link, affected_traffic_flows = self.failure_manager.single_link_failure_model(
                addr_to_host, traffic_flows)
            
            self.traffic_manager.affected_traffic_flows = affected_traffic_flows
            
            # SDFFR special handling
            if algorithm.startswith('SDFFR'):
                time.sleep(3)
                SystemManager.control_plane_delay_setup(self.cfg_file['ControlPlaneDelay'][0], 'delete')
                
                os.system('sudo python3 /home/lce/yukai_thesis/experiment/SD-FFR/pre_install_select_novlan.py')
                SystemManager.control_plane_delay_setup(self.cfg_file['ControlPlaneDelay'][0], 'add')
            
            time.sleep(10)
            
            start_event = Event()
            thread_manager = self.traffic_manager.setup_traffic_flows(
                traffic_flows, host_map, self.trace_folder, label, traffic_model, throughput, start_event, mode)
            
            # Execute status changes
            priority = 21
            for idx, status in enumerate(status_list):
                # SDFFR local rerouting handling
                if algorithm.startswith('SDFFR') and status != 0:
                    # Need to implement SDFFR local rerouting logic here
                    pass
                
                status_start.append(time.time())
                
                if status == 0:
                    self.logger.log_link_status(status)
                    if idx == 0 or status != status_list[idx - 1]:
                        change.append(self.failure_manager.bw_change(
                            failed_link, u_v_connection, True, 1000, net, link_state_flag, algorithm))
                        link_state_flag = True
                        change_counter = change_counter + 1
                    else:
                        change.append(time.time())
                elif status == 1:
                    new_bw = random.randint(1, 999)
                    self.logger.log_link_status(status, new_bw)
                    change.append(self.failure_manager.bw_change(
                        failed_link, u_v_connection, True, new_bw, net, link_state_flag, algorithm))
                    link_state_flag = True
                    change_counter = change_counter + 1
                elif status == 2:
                    self.logger.log_link_status(status)
                    if status != status_list[idx - 1]:
                        change.append(self.failure_manager.bw_change(
                            failed_link, u_v_connection, True, 0, net, link_state_flag, algorithm))
                        link_state_flag = True
                        change_counter = change_counter + 1
                    else:
                        change.append(time.time())
                
                time.sleep(link_change_time)
                status_stop.append(time.time())
            
            for idx, status in enumerate(status_list):
                self.logger.log_link_status_timestamp(status, status_start[idx])
            
            time.sleep(3)
            self.failure_manager.path_record(self.trace_folder, label, 'after link failure', mode)
            
            self.traffic_manager.cleanup_processes()
            SystemManager.kill_process('record')
            
            return {
                "affected_traffic_flows": affected_traffic_flows,
                "failed_link": failed_link,
                "change": change,
                'change_counter': change_counter,
                "status1_start": status_start[0], "status1_stop": status_stop[0],
                "status2_start": status_start[1], "status2_stop": status_stop[1],
                "status3_start": status_start[2], "status3_stop": status_stop[2],
                "status4_start": status_start[3], "status4_stop": status_stop[3],
                "status5_start": status_start[4], "status5_stop": status_stop[4]
            }
            
        except Exception as e:
            self.logger.log(f'single_link_failure error: {str(e)}')
            self.traffic_manager.cleanup_processes()
            return None
    
    def run_multiple_link_failure_experiment(self, traffic_model, traffic_flows, host_map, 
                                           addr_to_host, u_v_connection, label, net, throughput):
        try:
            link_change_time = self.cfg_file.get('LinkChangeTime', [5])[0]
            
            self.logger.log(f'link_change_time: {link_change_time}')
            
            failed_links, affected_traffic_flows = self.failure_manager.multiple_link_failure_model(
                addr_to_host, traffic_flows)
            
            self.traffic_manager.affected_traffic_flows = affected_traffic_flows
            
            start_event = Event()
            thread_manager = self.traffic_manager.setup_traffic_flows(
                traffic_flows, host_map, self.trace_folder, label, traffic_model, throughput, start_event, 'fixed')
            
            # status: los
            los1_start = time.time()
            self.logger.log(f'Collecting experimental data: {los1_start}')
            time.sleep(link_change_time)
            los1_stop = time.time()
            
            # status: fnlos1
            fnlos1_start = time.time()
            change_1 = self.failure_manager.link_state_change(failed_links[0], u_v_connection, "down", "fnlos")
            time.sleep(link_change_time)
            fnlos1_stop = time.time()
            self.logger.log(f'fnlos_start: {fnlos1_start}')
            
            # status: fnlos2
            fnlos2_start = time.time()
            change_2 = self.failure_manager.link_state_change(failed_links[1], u_v_connection, "down", "fnlos")
            time.sleep(link_change_time)
            fnlos2_stop = time.time()
            self.logger.log(f'fnlos_start: {fnlos2_start}')
            
            # status: los2
            los2_start = time.time()
            change_3 = self.failure_manager.link_state_change(failed_links[1], u_v_connection, "up", "los")
            time.sleep(link_change_time)
            los2_stop = time.time()
            self.logger.log(f'los2_start: {los2_start}')
            
            # status: los3
            los3_start = time.time()
            change_4 = self.failure_manager.link_state_change(failed_links[0], u_v_connection, "up", "los")
            time.sleep(link_change_time)
            los3_stop = time.time()
            self.logger.log(f'los3_start: {los3_start}')
            
            self.failure_manager.path_record(self.trace_folder, label, 'after link failure', 'fixed')
            
            # Cleanup processes
            self.traffic_manager.cleanup_processes()
            
            return {
                "affected_traffic_flows": affected_traffic_flows,
                "failed_links": failed_links,
                "los1_start": los1_start, "los1_stop": los1_stop, "change_1": change_1,
                "fnlos1_start": fnlos1_start, "fnlos1_stop": fnlos1_stop, "change_2": change_2,
                "fnlos2_start": fnlos2_start, "fnlos_stop": fnlos2_stop, "change_3": change_3,
                "los2_start": los2_start, "los2_stop": los2_stop, "change_4": change_4,
                "los3_start": los3_start, "los3_stop": los3_stop
            }
            
        except Exception as e:
            self.logger.log(f'multiple_link_failure error: {str(e)}')
            self.traffic_manager.cleanup_processes()
            return None
    
    def run_experiment(self, failure_mode, traffic_model, algorithm, traffic_flows, host_map, addr_to_host, u_v_connection, label, net, throughput, mode='markov'):
        host_set = []
        for (src, dst) in traffic_flows:
            if src not in host_set:
                host_set.append(src)
            if dst not in host_set:
                host_set.append(dst)
        
        for host in host_set:
            cmd_set = [
                'sudo ethtool -K ' + str(host_map[host].intf()) + ' lro off',
                'sudo ethtool -K ' + str(host_map[host].intf()) + ' gso off',
                'sudo ethtool -K ' + str(host_map[host].intf()) + ' tso off'
            ]
            for cmd in cmd_set:
                host_map[host].cmd(cmd)
        
        self.logger.log(f'failed_link: {failure_mode}')
        
        if failure_mode == 'single':
            data = self.run_single_link_failure_experiment(
                traffic_model, algorithm, traffic_flows, host_map, addr_to_host, 
                u_v_connection, label, net, throughput, mode)
        elif failure_mode == 'multiple':
            data = self.run_multiple_link_failure_experiment(
                traffic_model, traffic_flows, host_map, addr_to_host, 
                u_v_connection, label, net, throughput)
        
        self.logger.log_timestamp('Testing Completed')
        self.logger.log(f'Test data: {data}')
        
        return data
    
    def cleanup_experiment(self, algorithm):
        self.algorithm_manager.close_algorithm()
        time.sleep(5)
        os.system('sudo mn -c')
    
    def cleanup_files(self):
        files_to_clean = [
            './host_to_addr_location.json',
            './Algorithm_state->Ready',
            './Algorithm_state->Error',
            './traffic_flows.pkl',
            './traffic_flow_paths.txt',
            './traffic_flow_paths.pkl',
            './remove',
            './BW.txt',
            './label.txt',
            './linkdown_mode.txt',
            './mode.txt',
            './flow_throughput.txt',
            './result_folder_label.txt',
            './failed_link_bw.txt',
            './traffic_flow_backup_paths.txt',
            './config_done',
            './SD-FFR/link_backup_path.txt',
            './traffic_mac.txt'
        ]
        
        for file_path in files_to_clean:
            if os.path.isfile(file_path):
                os.system('sudo rm ' + file_path)
    
    def count_file(self, label, mode):
        try:
            if mode == 'markov':
                file_path = f'./Trace_folder/single/markov_chain/{label}/detect_link_change.txt'
            else:
                file_path = f'./Trace_folder/single/fixed_version/{label}/detect_link_change.txt'
            
            with open(file_path, 'r') as file:
                line_count = sum(1 for line in file)
            
            self.logger.log(f"Total number of lines is: {line_count}")
            return line_count
        except FileNotFoundError:
            self.logger.log("File not found.")
            return 0
        except IOError:
            self.logger.log("Error reading the file.")
            return 0
    
    def run_experiments(self):
        """Run all experiments"""
        try:
            num = self.setup_experiment_environment(self.cfg_file['FailureMode'])
            result = {}
            
            failure_patterns = self.generate_failure_patterns()
            
            vertex = self.cfg_file['Vertex'][0]
            edge = self.cfg_file['Edge'][0]
            link_bandwidth = self.cfg_file['LinkBandwidth'][0]
            throughput = self.cfg_file['Throughput'][0]
            traffic_model = self.cfg_file['TrafficModel'][0]
            control_plane_delay = self.cfg_file['ControlPlaneDelay'][0]
            flow_count = self.cfg_file['FlowCount'][0]

            # Iterate through all experiment parameter combinations
            for i in range(self.cfg_file['Trial'][0], self.cfg_file['Trial'][1] + 1):

                for algorithm in self.cfg_file['Algorithm']:
                    label = self.create_experiment_label(
                        algorithm, vertex, edge, link_bandwidth, throughput,
                        traffic_model, control_plane_delay, flow_count, i)
                    
                    if self.cfg_file['Mode'] == 'markov':
                        if os.path.isdir(f"{self.trace_folder}markov_chain/{label}"):
                            continue
                    else:
                        if os.path.isdir(f"{self.trace_folder}fixed_version/{label}"):
                            continue
                    
                    print(f'Starting experiment: {label}')
                    
                    mode = 'markov' if self.cfg_file['Mode'] == 'markov' else 'fixed'
                    self.setup_experiment_files(label, self.cfg_file['FailureMode'], mode)
                    
                    # Get pre-generated failure pattern for this parameter combination
                    pattern_key = i
                    failure_pattern = failure_patterns.get(pattern_key)
                    
                    if failure_pattern is None:
                        self.logger.log(f"Error: No failure pattern found for {pattern_key}")
                        continue
                    
                    # Run experiment
                    success = False
                    while not success:
                        try:
                            SystemManager.reset_all()
                            
                            if self.cfg_file['Mode'] == 'markov':
                                self.config_manager.build_folder(f"{self.trace_folder}markov_chain/{label}", True)
                            else:
                                self.config_manager.build_folder(f"{self.trace_folder}fixed_version/{label}", True)
                            self.config_manager.build_folder(f"{self.log_folder}{label}", True)
                            
                            log_file = self.config_manager.build_log_file(
                                f"{self.trace_folder}{'markov' if self.cfg_file['Mode'] == 'markov' else 'fixed'}/{label}/{i}.log")
                            self.logger.set_log_file(log_file)
                            
                            # Log experiment parameters
                            self.logger.log(f"Experiment {i} start")
                            self.logger.log(f"Algorithm: {algorithm}")
                            self.logger.log(f"Vertex: {vertex}")
                            self.logger.log(f"Edge: {edge}")
                            self.logger.log(f"Link bandwidth: {link_bandwidth}")
                            self.logger.log(f"Throughput: {throughput}")
                            self.logger.log(f"Traffic model: {traffic_model}")
                            self.logger.log(f"Control plane delay: {control_plane_delay}")
                            self.logger.log(f"Flow count: {flow_count}")
                            self.logger.log(f"Failure mode: {self.cfg_file['FailureMode']}")
                            self.logger.log(f"Failure pattern: {failure_pattern}")
                            
                            # Setup network topology
                            edge_set = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20), (1, 20), (6, 2), (1, 17), (9, 11), (17, 14), (5, 11), (20, 9), (4, 18), (18, 6), (14, 11), (10, 4), (3, 19), (5, 12), (9, 12), (2, 16), (13, 3)]
                            vertex_set = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                            
                            net, host_map, switch_map, traffic_flows, host_to_IP, host_to_addr, addr_to_host, u_v_connection = self.setup_network_topology(
                                edge_set, vertex_set, flow_count, link_bandwidth)
                            
                            self.logger.log_timestamp('Setup the algorithm')
                            algorithm_setup_state = self.algorithm_manager.setup_algorithm(algorithm)
                            
                            self.logger.log_timestamp('Setup control plane delay')
                            SystemManager.control_plane_delay_setup(control_plane_delay, 'add')
                            
                            if algorithm_setup_state:
                                self.logger.log_timestamp('Run the test case')
                                data = self.run_single_link_failure_experiment_with_pattern(
                                    self.cfg_file['FailureMode'], traffic_model, algorithm,
                                    traffic_flows, host_map, addr_to_host, u_v_connection,
                                    label, net, throughput, mode, failure_pattern)
                                
                                # Cleanup network
                                self.cleanup_experiment(algorithm)
                                
                                count_line = self.count_file(label, self.cfg_file['FailureMode'])
                                
                                if count_line != data['change_counter']:
                                    print('======================================')
                                    print('Data mismatch, rerunning experiment')
                                    print(f'count_line: {count_line}')
                                    print(f'change_counter: {data["change_counter"]}')
                                    print('======================================')
                                    self.cleanup_files()
                                    SystemManager.control_plane_delay_setup(control_plane_delay, 'delete')
                                    continue
                                elif data is None:
                                    self.cleanup_files()
                                    SystemManager.control_plane_delay_setup(control_plane_delay, 'delete')
                                    continue
                                else:
                                    self.logger.log_timestamp('Analysis result')
                                    self.failure_manager.analysis_trace_file(
                                        self.cfg_file['FailureMode'], algorithm,
                                        self.trace_folder, label, data, host_map)
                                    
                                    SystemManager.control_plane_delay_setup(control_plane_delay, 'delete')
                                    SystemManager.kill_process('kill')
                                    success = True
                            else:
                                self.cleanup_files()
                                SystemManager.control_plane_delay_setup(control_plane_delay, 'delete')
                                continue
                                
                        except Exception as e:
                            self.logger.log(f"Experiment run error: {str(e)}")
                            self.cleanup_files()
                            SystemManager.control_plane_delay_setup(control_plane_delay, 'delete')
                            continue
                    
                    print('Release resources')
                    self.cleanup_files()
                    SystemManager.kill_process('remove')
                    gc.collect()
                    time.sleep(5)
            
            print('Experiment completed')
            os.system(f'sudo rm -r {num}')
            
        except Exception as e:
            self.logger.log(f"Experiment run error: {str(e)}")
            raise
    
    def generate_failure_patterns(self):
        failure_patterns = {}

        for i in range(self.cfg_file['Trial'][0], self.cfg_file['Trial'][1] + 1):
            pattern_key = (i)
            
            if self.cfg_file['Mode'] == 'markov':
                status_count = 4
                start_state = 0
                failure_pattern = self.failure_manager.simulate_markov_chain(
                    self.failure_manager.transition_matrix, start_state, status_count)
            else:
                failure_pattern = [0, 1, 2, 1, 0]  # los -> pnlos -> fnlos -> pnlos -> los
                
            failure_patterns[pattern_key] = failure_pattern
            print(f"Generated failure pattern for trial[{pattern_key}]: {failure_pattern}")
        
        return failure_patterns
    
    def run_single_link_failure_experiment_with_pattern(self, traffic_model, algorithm, traffic_flows, host_map, addr_to_host, u_v_connection, label, net, throughput, mode, failure_pattern):
        try:
            link_change_time = self.cfg_file.get('LinkChangeTime', [5])[0]
            status_start = []
            status_stop = []
            change = []
            link_state_flag = True
            change_counter = 0
            thread_manager = []

            status_list = failure_pattern
            
            self.logger.log(f'Using pre-generated failure pattern: {status_list}')
            self.logger.log(f'link_change_time: {link_change_time}')
            
            failed_link, affected_traffic_flows = self.failure_manager.single_link_failure_model(
                addr_to_host, traffic_flows)
            
            # SDFFR special handling
            if algorithm.startswith('SDFFR'):
                time.sleep(3)
                SystemManager.control_plane_delay_setup(self.cfg_file['ControlPlaneDelay'][0], 'delete')
                
                os.system('sudo python3 /home/lce/yukai_thesis/experiment/SD-FFR/pre_install_select_novlan.py')
                SystemManager.control_plane_delay_setup(self.cfg_file['ControlPlaneDelay'][0], 'add')
            
            time.sleep(10)
            
            start_event = Event()
            thread_manager = self.traffic_manager.setup_traffic_flows(
                traffic_flows, host_map, self.trace_folder, label, traffic_model, throughput, start_event, mode, affected_traffic_flows)
            
            # Execute status changes using pre-generated pattern
            for idx, status in enumerate(status_list):
                # SDFFR local rerouting handling
                if algorithm.startswith('SDFFR') and status != 0:
                    # Need to implement SDFFR local rerouting logic here
                    pass
                
                status_start.append(time.time())
                
                if status == 0:
                    self.logger.log_link_status(status)
                    if idx == 0 or status != status_list[idx - 1]:
                        change.append(self.failure_manager.bw_change(
                            failed_link, u_v_connection, True, 1000, net, link_state_flag, algorithm))
                        link_state_flag = True
                        change_counter = change_counter + 1
                    else:
                        change.append(time.time())
                elif status == 1:
                    new_bw = random.randint(1, 999)
                    self.logger.log_link_status(status, new_bw)
                    change.append(self.failure_manager.bw_change(
                        failed_link, u_v_connection, True, new_bw, net, link_state_flag, algorithm))
                    link_state_flag = True
                    change_counter = change_counter + 1
                elif status == 2:
                    self.logger.log_link_status(status)
                    if status != status_list[idx - 1]:
                        change.append(self.failure_manager.bw_change(
                            failed_link, u_v_connection, True, 0, net, link_state_flag, algorithm))
                        link_state_flag = True
                        change_counter = change_counter + 1
                    else:
                        change.append(time.time())
                
                time.sleep(link_change_time)
                status_stop.append(time.time())
            
            # Record status timestamps
            for idx, status in enumerate(status_list):
                self.logger.log_link_status_timestamp(status, status_start[idx])
            
            time.sleep(3)
            self.failure_manager.path_record(self.trace_folder, label, 'after link failure', mode)
            
            # Cleanup processes
            self.traffic_manager.cleanup_processes()
            SystemManager.kill_process('record')
            
            return {
                "affected_traffic_flows": affected_traffic_flows,
                "failed_link": failed_link,
                "change": change,
                'change_counter': change_counter,
                "status1_start": status_start[0], "status1_stop": status_stop[0],
                "status2_start": status_start[1], "status2_stop": status_stop[1],
                "status3_start": status_start[2], "status3_stop": status_stop[2],
                "status4_start": status_start[3], "status4_stop": status_stop[3],
                "status5_start": status_start[4], "status5_stop": status_stop[4]
            }
            
        except Exception as e:
            self.logger.log(f"Single link failure experiment error: {str(e)}")
            return None
    
    def cleanup_experiment_environment(self):
        try:
            # Cleanup all related files
            self.cleanup_files()
            
            # Cleanup processes
            SystemManager.kill_process('kill')
            SystemManager.kill_process('remove')
            
            # Cleanup network
            os.system('sudo mn -c')
            
            print("Experiment environment cleanup completed")
            
        except Exception as e:
            print(f"Error occurred during environment cleanup: {str(e)}")
            raise 