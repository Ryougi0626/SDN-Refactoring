"""
Traffic management module
Handle traffic generation, testing and data collection
"""

import os
import random
import subprocess
import time
from threading import Thread, Event


class TrafficManager:
    
    def __init__(self, logger, config_manager):
        self.logger = logger
        self.config_manager = config_manager
        self.sub_process_manager = []
        self.BASE_PORT = 50000
    
    def ping(self, src_host, dst_host):
        """Execute ping test"""
        src_host.pexec('ping -c1 ' + dst_host.IP())
    
    def tcpdump(self, host, cmd):
        """Execute tcpdump"""
        host.cmd(cmd)
    
    def iperf_server_1(self, dst_host, cmd):
        """Start iperf server (simple version)"""
        process = dst_host.popen(str(cmd))
        self.sub_process_manager.append(process)
    
    def iperf_server_2(self, src_host, dst_host, cmd, trace_folder, label):
        """Start iperf server (with data collection)"""
        path = trace_folder + 'markov_chain/' + label + '/' + str(src_host) + '_' + str(dst_host) + '_s.json'
        with open(path, 'w') as outfile:
            process = dst_host.popen(str(cmd), shell=True, stdout=outfile, stderr=subprocess.PIPE)
            self.sub_process_manager.append(process)
    
    def iperf_server_2_fixed(self, src_host, dst_host, cmd, trace_folder, label):
        """Start iperf server (fixed version)"""
        path = trace_folder + 'fixed_version/' + label + '/' + str(src_host) + '_' + str(dst_host) + '_s.json'
        with open(path, 'w') as outfile:
            process = dst_host.popen(str(cmd), shell=True, stdout=outfile, stderr=subprocess.PIPE)
            self.sub_process_manager.append(process)
    
    def iperf_send_1(self, traffic_model, src_host, dst_host, index, flow_count, throughput, start_event, use_port, trace_folder, label):
        """Send iperf traffic (collect data)"""
        if traffic_model == 1:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '25', '-b', str(throughput) + 'M', '-J', '-p', str(use_port)]
            path = trace_folder + 'markov_chain/' + label + '/' + str(src_host) + '_' + str(dst_host) + '.json'
        elif traffic_model == 2:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '25', '-b', str(throughput) + 'M', '-u', '-J', '-p', str(use_port)]
            path = trace_folder + 'markov_chain/' + label + '/' + str(src_host) + '_' + str(dst_host) + '.json'
        
        start_event.wait()
        with open(path, 'w') as outfile:
            process = src_host.popen(cmd, shell=True, stdout=outfile, stderr=subprocess.PIPE)
            self.sub_process_manager.append(process)
            self.logger.log_traffic_flow(index, src_host, dst_host)
            self.logger.log(f'here!!!!,src:{src_host.IP()} ,dst:{dst_host.IP()}, cmd:{" ".join(cmd)} ,TraceFolder:{trace_folder} , label:{label}')
    
    def iperf_send_1_fixed(self, traffic_model, src_host, dst_host, index, flow_count, throughput, start_event, use_port, trace_folder, label):
        """Send iperf traffic (fixed version, collect data)"""
        if traffic_model == 1:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '25', '-b', str(throughput) + 'M', '-J', '-i', '1', '-p', str(use_port)]
            path = trace_folder + 'fixed_version/' + label + '/' + str(src_host) + '_' + str(dst_host) + '.json'
        elif traffic_model == 2:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '25', '-b', str(throughput) + 'M', '-u', '-J', '-i', '1', '-p', str(use_port)]
            path = trace_folder + 'fixed_version/' + label + '/' + str(src_host) + '_' + str(dst_host) + '.json'
        
        start_event.wait()
        with open(path, 'w') as outfile:
            process = src_host.popen(cmd, shell=True, stdout=outfile, stderr=subprocess.PIPE)
            self.sub_process_manager.append(process)
            self.logger.log_traffic_flow(index, src_host, dst_host)
            self.logger.log(f'here!!!!,src:{src_host.IP()} ,dst:{dst_host.IP()}, cmd:{" ".join(cmd)} ,TraceFolder:{trace_folder} , label:{label}')
    
    def iperf_send_2(self, traffic_model, src_host, dst_host, index, flow_count, throughput, start_event, use_port):
        """Send iperf traffic (no data collection)"""
        if traffic_model == 1:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '60', '-b', str(throughput) + 'M', '-p', str(use_port)]
        elif traffic_model == 2:
            cmd = ['iperf3', '-c', dst_host.IP(), '-t', '60', '-b', str(throughput) + 'M', '-u', '-p', str(use_port)]
        
        process = src_host.popen(str(cmd))
        self.sub_process_manager.append(process)
        self.logger.log_traffic_flow(index, src_host, dst_host)
        self.logger.log(f'here!!!!,src:{src_host.IP()} ,dst:{dst_host.IP()}, cmd:{" ".join(cmd)}')
    
    def setup_traffic_flows(self, traffic_flows, host_map, trace_folder, label, traffic_model, throughput, start_event, mode, affected_traffic_flows):
        """Setup traffic flows"""
        thread_manager = []
        
        # Setup iptables
        commands = [
            "sudo iptables -P INPUT ACCEPT",
            "sudo iptables -P FORWARD ACCEPT",
            "sudo iptables -P OUTPUT ACCEPT",
            "sudo iptables -F"
        ]
        
        for cmd in commands:
            for src_host, dst_host in traffic_flows:
                host_map[src_host].popen(cmd, shell=True)
                host_map[dst_host].popen(cmd, shell=True)
        
        # Execute ping tests
        for idx, (src_host, dst_host) in enumerate(traffic_flows):
            ping_thread = Thread(target=self.ping, args=(host_map[src_host], host_map[dst_host]))
            ping_thread.start()
            thread_manager.append(ping_thread)
            time.sleep(0.05)
        
        for thread in thread_manager:
            thread.join()
        
        thread_manager = []
        
        # Start iperf servers and clients
        for idx, (src_host, dst_host) in enumerate(traffic_flows):
            use_port = self.BASE_PORT + idx
            
            # Non-affected traffic flows
            if (src_host, dst_host) not in affected_traffic_flows:
                cmd = "iperf3 -s -p " + str(use_port)
                iperf_server_thread = Thread(target=self.iperf_server_1, args=(host_map[dst_host], cmd))
                iperf_server_thread.setDaemon(True)
                iperf_server_thread.start()
                thread_manager.append(iperf_server_thread)
                
                iperf_send_thread = Thread(target=self.iperf_send_2, 
                                         args=(traffic_model, host_map[src_host], host_map[dst_host], 
                                               idx + 1, len(traffic_flows), throughput, start_event, use_port))
                iperf_send_thread.setDaemon(True)
                iperf_send_thread.start()
                thread_manager.append(iperf_send_thread)
        
        time.sleep(5)
        
        # Affected traffic flows
        for idx, (src_host, dst_host) in enumerate(traffic_flows):
            use_port = self.BASE_PORT + idx
            
            if (src_host, dst_host) in getattr(self, 'affected_traffic_flows', []):
                if traffic_model == 2:
                    if mode == 'markov':
                        cmd = "iperf3 -s -J -p " + str(use_port)
                        iperf_server_thread = Thread(target=self.iperf_server_2, 
                                                   args=(host_map[src_host], host_map[dst_host], cmd, trace_folder, label))
                    else:
                        cmd = "iperf3 -s -J -p " + str(use_port) + " -i 0.1"
                        iperf_server_thread = Thread(target=self.iperf_server_2_fixed, 
                                                   args=(host_map[src_host], host_map[dst_host], cmd, trace_folder, label))
                elif traffic_model == 1:
                    cmd = "iperf3 -s -p " + str(use_port)
                    iperf_server_thread = Thread(target=self.iperf_server_1, args=(host_map[dst_host], cmd))
                
                iperf_server_thread.setDaemon(True)
                iperf_server_thread.start()
                thread_manager.append(iperf_server_thread)
                
                if mode == 'markov':
                    iperf_send_thread = Thread(target=self.iperf_send_1, 
                                             args=(traffic_model, host_map[src_host], host_map[dst_host], 
                                                   idx + 1, len(traffic_flows), throughput, start_event, use_port, trace_folder, label))
                else:
                    iperf_send_thread = Thread(target=self.iperf_send_1_fixed, 
                                             args=(traffic_model, host_map[src_host], host_map[dst_host], 
                                                   idx + 1, len(traffic_flows), throughput, start_event, use_port, trace_folder, label))
                
                iperf_send_thread.setDaemon(True)
                iperf_send_thread.start()
                thread_manager.append(iperf_send_thread)
        
        start_event.set()
        return thread_manager
    
    def cleanup_processes(self):
        """Cleanup processes"""
        for sub_process in self.sub_process_manager:
            sub_process.kill()
        self.sub_process_manager = [] 