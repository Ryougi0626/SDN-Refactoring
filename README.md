# SDN Failure Recovery Experiment Framework

This is a modular SDN failure recovery experiment framework for testing and comparing different failure recovery algorithms.

## Project Structure

```
test/
├── main.py                   # Main program entry
├── config/                   # Configuration directory
│   ├── config.py             # Configuration management module
│   └── configuration1.json   # Example configuration file
├── src/                      # Source code directory
│   ├── experiment.py         # Experiment runner
│   ├── logger.py             # Log management module
│   ├── topology.py           # Topology management module
│   ├── algorithm.py          # Algorithm management module
│   ├── traffic.py            # Traffic management module
│   └── failure.py            # Failure management module
└── README.md                 # Documentation
```

## Module Functions

### 1. Configuration Management (config.py)
- Read and manage JSON configuration files
- File operation utility functions
- System management functions

### 2. Log Management (logger.py)
- Unified logging interface
- Support for timestamps and status recording
- File log output

### 3. Topology Management (topology.py)
- Mininet network topology construction
- Host and switch management
- Connection status checking

### 4. Algorithm Management (algorithm.py)
- Failure recovery algorithm deployment
- ONOS application management
- Algorithm status monitoring

### 5. Traffic Management (traffic.py)
- iperf traffic generation
- Traffic monitoring and data collection
- Process management

### 6. Failure Management (failure.py)
- Link failure simulation
- Failure detection and recovery
- Data analysis

### 7. Experiment Runner (experiment.py)
- Integrate all module functions
- Experiment flow control
- Result management

## Usage

### 1. Configuration File Setup

Create a configuration file in the `config/` directory, for example `configuration.json`:

```json
{
    "UserName": "lce",
    "OutputFile": "single_link_failure_result_data.pkl",
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
```

### 2. Running Experiments

```bash
# Run experiment
python3 main.py run configuration1

# Clean experiment environment
python3 main.py clean configuration1
```

### 3. Parameter Description

- `mode`: Run mode
  - `run`: Run experiment
  - `clean`: Clean experiment environment
- `config_file`: Configuration file name (without .json extension)

### 4. Configuration Parameters

- `UserName`: Username
- `FailureMode`: Failure mode (single/multiple)
- `Algorithm`: List of algorithms to test
- `Vertex`: Number of nodes
- `Edge`: Number of links
- `LinkBandwidth`: Link bandwidth
- `Throughput`: Traffic throughput
- `TrafficModel`: Traffic model
- `ControlPlaneDelay`: Control plane delay
- `FlowCount`: Number of flows
- `Trial`: Experiment trial range
- `LinkChangeTime`: Link change time interval
- `Metric`: Evaluation metrics

## Experiment Process

1. **Environment Setup**: Initialize experiment environment and directory structure
2. **Topology Construction**: Create Mininet network topology
3. **Algorithm Deployment**: Deploy failure recovery algorithms on ONOS controller
4. **Traffic Generation**: Generate test traffic using iperf
5. **Failure Injection**: Simulate link failures and recovery
6. **Data Collection**: Collect performance metrics and logs
7. **Result Analysis**: Analyze experiment results and save

## Notes

1. Ensure Mininet, ONOS and other dependencies are installed
2. Requires sudo privileges to run
3. Ensure network environment is properly configured
4. Please backup important data before experiments

## Troubleshooting

- If experiments fail, check log files
- Ensure all dependent services are running normally
- Check network configuration and permission settings 