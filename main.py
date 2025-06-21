"""
Experiment main program
Used for running SDN failure recovery experiments
"""

import sys
import os
import argparse
from src.experiment import ExperimentRunner
from src.config import ConfigManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['run', 'clean'], 
                       help='Run mode: run(run experiment) or clean(cleanup)')
    parser.add_argument('config_file', help='Configuration file name (without .json extension)')
    
    args = parser.parse_args()
    
    try:
        with open(args.config_file + '.json', 'r') as f:
            import json
            cfg_file = json.load(f)
        
        experiment_runner = ExperimentRunner(args.config_file + '.json', cfg_file['UserName'])
        
        if args.mode == 'run':
            print("Starting experiment...")
            experiment_runner.run_experiments()
        elif args.mode == 'clean':
            print("Starting experiment environment cleanup...")
            experiment_runner.cleanup_experiment_environment()
            
    except KeyboardInterrupt:
        print("\nExperiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Experiment run error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main() 