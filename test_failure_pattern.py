#!/usr/bin/env python3
"""
Test script for failure pattern generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.experiment import ExperimentRunner
from src.config import ConfigManager

def test_failure_pattern_generation():
    """Test failure pattern generation"""
    print("Testing failure pattern generation...")
    
    # Create a simple config for testing
    test_config = {
        "UserName": "test",
        "OutputFile": "test_result.pkl",
        "SaveTraceFile": "True",
        "FailureMode": "single",
        "Algorithm": ["SDFFR_MP", "SDFFR_MP_LB"],
        "Vertex": [20],
        "Edge": [35],
        "LinkBandwidth": [1000],
        "Throughput": [10],
        "TrafficModel": [1],
        "ControlPlaneDelay": [20],
        "FlowCount": [30],
        "Trial": [1, 2],
        "LinkChangeTime": [5],
        "Metric": ["Throughput", "TOTALPacketLoss", "PacketLoss", "RecoveryDelay"]
    }
    
    # Save test config
    import json
    with open('test_config.json', 'w') as f:
        json.dump(test_config, f, indent=4)
    
    try:
        # Create experiment runner
        experiment_runner = ExperimentRunner('test_config.json', 'test')
        
        # Test failure pattern generation
        failure_patterns = experiment_runner.generate_failure_patterns()
        
        print(f"Generated {len(failure_patterns)} failure patterns:")
        for pattern_key, pattern in failure_patterns.items():
            print(f"  {pattern_key}: {pattern}")
        
        # Verify that all algorithms will use the same patterns
        print("\nVerifying pattern consistency...")
        for vertex in test_config['Vertex']:
            for edge in test_config['Edge']:
                for link_bandwidth in test_config['LinkBandwidth']:
                    for throughput in test_config['Throughput']:
                        for traffic_model in test_config['TrafficModel']:
                            for control_plane_delay in test_config['ControlPlaneDelay']:
                                for flow_count in test_config['FlowCount']:
                                    for i in range(test_config['Trial'][0], test_config['Trial'][1] + 1):
                                        pattern_key = (vertex, edge, link_bandwidth, throughput, traffic_model, control_plane_delay, flow_count, i)
                                        pattern = failure_patterns.get(pattern_key)
                                        print(f"Pattern for {pattern_key}: {pattern}")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        if os.path.exists('test_config.json'):
            os.remove('test_config.json')

if __name__ == '__main__':
    test_failure_pattern_generation() 