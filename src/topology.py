"""
Topology management module
Handle network topology creation and management
"""

import random
import time
import requests
from threading import Thread
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class TopologyManager:
    """Topology manager"""
    
    def __init__(self, logger):
        self.logger = logger
    
    ## note: no reference to this function in the original code, but keeping it for completeness
    def read_topo_file(self, file_name):
        """Read topology from SNDlib file"""
        file_name = './SNDlib/' + file_name
        raw_edge_data = []
        raw_vertex_data = {}
        count = 0
        tree = ET.ElementTree(file=file_name)
        root = tree.getroot()
        
        for child in root:
            for sub_child in child:
                if sub_child.attrib != {}:
                    if list(sub_child.attrib.keys())[0] == 'coordinatesType':
                        for sub_sub_child in sub_child:
                            count = count + 1
                            raw_vertex_data[sub_sub_child.attrib['id']] = count
        
        for child in root:
            for sub_child in child:
                if sub_child.attrib == {}:
                    for sub_sub_child in sub_child:
                        edge = []
                        for sub_sub_sub_child in sub_sub_child:
                            if sub_sub_sub_child.tag == '{http://sndlib.zib.de/network}target' or sub_sub_sub_child.tag == '{http://sndlib.zib.de/network}source':
                                edge.append(raw_vertex_data[sub_sub_sub_child.text])
                        raw_edge_data.append(tuple(edge))
        
        raw_edge_data = sorted(raw_edge_data)
        raw_vertex_data = sorted(list(raw_vertex_data.values()))
        return raw_edge_data, raw_vertex_data, file_name
    
    ## note: no reference to this function in the original code, but keeping it for completeness
    def create_topo(self, edge, vertex):
        """Create topology"""
        raw_edge_data = []
        raw_vertex_data = []
        
        for i in range(1, vertex + 1):
            raw_vertex_data.append(i)
            j = i + 1
            if j < vertex + 1:
                raw_edge_data.append((i, j))
        
        self.logger.log(f"raw_edge_data : {raw_edge_data}")
        raw_edge_data.append((raw_edge_data[0][0], raw_edge_data[len(raw_edge_data) - 1][1]))
        self.logger.log(f"raw_edge_data : {raw_edge_data}")
        
        for i in range(edge - len(raw_edge_data)):
            while True:
                random_edge = random.sample(raw_vertex_data, 2)
                if tuple(random_edge) not in raw_edge_data and (random_edge[1], random_edge[0]) not in raw_edge_data:
                    raw_edge_data.append(tuple(random_edge))
                    break
        
        self.logger.log(f"raw_edge_data : {raw_edge_data}")
        self.logger.log(f"raw_vertex_data : {raw_vertex_data}")
        return raw_edge_data, raw_vertex_data
    
    def add_switch(self, net, switch_name):
        net.addSwitch(switch_name)
    
    def add_host(self, net, host_name, host_ip):
        net.addHost(host_name, ip=host_ip)
    
    def build_topo(self, edge_set, vertex_set, flow_count, link_bandwidth):
        """Build Mininet topology"""
        self.logger.log(f'Number of nodes: {len(vertex_set)}')
        self.logger.log(f'Number of links: {len(edge_set)}')
        
        for s_node, d_node in edge_set:
            self.logger.log(f"{s_node-1}, {d_node-1}")
            self.logger.log(f"{d_node-1}, {s_node-1}")
        
        self.logger.log('Topology file reading completed')
        
        thread_manager = []
        host_list = [0]
        net = Mininet(controller=RemoteController, link=TCLink)
        c0 = net.addController('c0', ip='127.0.0.1', port=6633)
        switch_map = {}
        host_map = {}
        host_to_IP = {}
        traffic_flows = []
        edge_switches = random.sample(vertex_set, int(len(vertex_set)))
        
        # Add switches
        for vertex in vertex_set:
            switch_name = 's' + str(vertex)
            add_switch_thread = Thread(target=self.add_switch, args=(net, switch_name))
            add_switch_thread.start()
            thread_manager.append(add_switch_thread)
        
        # Generate traffic flows
        for i in range(flow_count):
            while True:
                host_num = random.sample(host_list, 1)
                traffic_flow = list(map(lambda x: 'h' + str(x) + '_' + str(host_num[0]), 
                                       random.sample(edge_switches, 2)))
                if (tuple(traffic_flow) not in traffic_flows and 
                    tuple((traffic_flow[1], traffic_flow[0])) not in traffic_flows and 
                    traffic_flow[0][1] != traffic_flow[1][1]):
                    traffic_flows.append(tuple(traffic_flow))
                    break
        
        # Add hosts
        for switch in edge_switches:
            for host_num in host_list:
                host_name = 'h' + str(switch) + '_' + str(host_num)
                host_ip = '10.0.0.' + str(switch) + '/24'
                add_host_thread = Thread(target=self.add_host, args=(net, host_name, host_ip))
                add_host_thread.start()
                thread_manager.append(add_host_thread)
        
        # Wait for all threads to complete
        for thread in thread_manager:
            thread.join()
        
        # Create mappings
        for host in net.hosts:
            host_map[host.name] = host
        for switch in net.switches:
            switch_map[switch.name] = switch
        
        # Add host to switch links
        for switch in edge_switches:
            for host_num in host_list:
                net.addLink(switch_map['s' + str(switch)], 
                           host_map['h' + str(switch) + '_' + str(host_num)],
                           bw=1000, max_queue_size=1000, delay='0.5ms', use_htb=True)
        
        # Add switch to switch links
        for edge in edge_set:
            net.addLink(switch_map['s' + str(edge[0])], switch_map['s' + str(edge[1])],
                       bw=link_bandwidth, max_queue_size=1000, delay='0.5ms', use_htb=True)
        
        net.build()
        
        for host in net.hosts:
            host_to_IP[host.name] = host.IP()
        
        c0.start()
        for switch in switch_map.values():
            switch.start([c0])
        
        self.logger.log('Mininet topology deployment completed')
        return net, host_map, switch_map, traffic_flows, host_to_IP
    
    def create_host_to_addr_location_file(self, net, config_manager):
        """Create host address location file"""
        host_map = {}
        host_to_addr_location = {}
        
        for host in net.hosts:
            host_map[host.name] = host.MAC()
        
        for switch in net.switches:
            for _host in net.hosts:
                connection_list = switch.connectionsTo(_host)
                if connection_list != []:
                    for connection in connection_list:
                        node = connection[0].name
                        host = connection[1].name
                        node_split = node.split('-')
                        node_name = node_split[0]
                        node_port = node_split[1].replace('eth', '')
                        host_split = host.split('-')
                        host_name = host_split[0]
                        host_mac = host_map[host_name]
                        host_port = host_split[1].replace('eth', '')
                        host_to_addr_location.setdefault(host_mac, {})
                        host_to_addr_location[host_mac][node_name] = node_port
        
        config_manager.build_json('./host_to_addr_location.json', host_to_addr_location)
        self.logger.log('Host location file creation completed')
        return {value: key for value, key in host_map.items()}, {value: key for key, value in host_map.items()}
    
    def create_traffic_flows_file(self, traffic_flows, host_to_addr, config_manager):
        """Create traffic flows file"""
        data = []
        for (src, dst) in traffic_flows:
            data.append((host_to_addr[src], host_to_addr[dst]))
        config_manager.build_pickle('traffic_flows.pkl', data)
        self.logger.log('Traffic flow set creation completed')
    
    def create_u_v_connection(self, switch_map, edge_set):
        """Create switch connection data"""
        u_v_connection = {}
        for edge in edge_set:
            connection_list = switch_map['s' + str(edge[0])].connectionsTo(switch_map['s' + str(edge[1])])
            for connection in connection_list:
                u = connection[0].name
                v = connection[1].name
                u_split = u.split('-')
                u_name = u_split[0]
                u_port = u_split[1].replace('eth', '')
                v_split = v.split('-')
                v_name = v_split[0]
                v_port = v_split[1].replace('eth', '')
                
                if u not in u_v_connection.keys():
                    u_v_connection.setdefault(u_name, {})
                if v not in u_v_connection.keys():
                    u_v_connection.setdefault(v_name, {})
                
                u_v_connection[u_name][v_name] = u_port
                u_v_connection[v_name][u_name] = v_port
        
        self.logger.log('Switch connection data creation completed')
        return u_v_connection
    
    def check_controller_connectivity(self, edge):
        """Check controller connectivity"""
        self.logger.log('Check the connectivity of SDN controller')
        url = 'http://localhost:8181/onos/v1/topology/clusters/0/links'
        headers = {'Accept': 'application/json'}
        auth = ('onos', 'rocks')
        
        while True:
            time.sleep(5)
            try:
                r = requests.get(url, headers=headers, auth=auth)
                raw_topo = r.json()['links']
                if int(len(raw_topo) / 2) == edge:
                    break
            except:
                self.logger.log('check_controller_connectivity error')
                continue
        
        self.logger.log('All SDN switches and SDN controller connections are established') 