"""
Log management module
Handle experiment logging
"""

import time
import json

class Logger:

    def __init__(self, log_file=None):
        self.log_file = log_file
    
    def set_log_file(self, log_file):
        self.log_file = log_file
    
    def log(self, data=""):
        if self.log_file and data != "":
            with open(self.log_file, 'a') as f:
                f.write(str(data))
                f.write('\n')
    
    def log_timestamp(self, message):
        timestamp = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
        self.log(f"{timestamp} {message}")
    
    def log_experiment_info(self, algorithm, vertex, edge, link_bandwidth, throughput, 
                           traffic_model, control_plane_delay, flow_count, failure_mode):
        self.log(f"Experiment start")
        self.log(f"Algorithm: {algorithm}")
        self.log(f"Vertex: {vertex}")
        self.log(f"Edge: {edge}")
        self.log(f"Link bandwidth: {link_bandwidth}")
        self.log(f"Throughput: {throughput}")
        self.log(f"Traffic model: {traffic_model}")
        self.log(f"Control plane delay: {control_plane_delay}")
        self.log(f"Flow count: {flow_count}")
        self.log(f"Failure mode: {failure_mode}")
    
    def log_traffic_flow(self, index, src_host, dst_host):
        self.log_timestamp(f"{index:5}: {src_host.name:5} {src_host.MAC():5} {src_host.IP():5}-> {dst_host.name:5} {dst_host.MAC():5} {dst_host.IP():5}")
    
    def log_link_status(self, status, bw=None):
        if status == 0:
            self.log('los_start')
        elif status == 1:
            self.log(f'pnlos_start, bw = {bw}')
        elif status == 2:
            self.log('fnlos_start')
    
    def log_link_status_timestamp(self, status, timestamp):
        if status == 0:
            self.log(f'los_start: {timestamp}')
        elif status == 1:
            self.log(f'pnlos_start: {timestamp}')
        elif status == 2:
            self.log(f'fnlos_start: {timestamp}')
    
    def log_failed_link(self, failed_link):
        self.log_timestamp(f"Failed link: {failed_link}")
    
    def log_affected_flows(self, affected_traffic_flows):
        self.log_timestamp(f"Affected traffic flow set: {affected_traffic_flows}")
    
    def log_completion(self, message):
        self.log_timestamp(f"{message} completed") 