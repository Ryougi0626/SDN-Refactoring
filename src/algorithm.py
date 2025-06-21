"""
Algorithm management module
Handle setup and management of different algorithms
"""

import os
import time
from .config import ONOSConfig


class AlgorithmManager:
    
    def __init__(self, logger):
        self.logger = logger
    
    def setup_algorithm(self, algorithm):
        if algorithm == 'LB':
            self.logger.log("Perform LB algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/LP/target/LP-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            self.logger.log('\n')
            
        elif algorithm == 'MP':
            self.logger.log("Perform MP algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/MP/target/MP-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            self.logger.log('\n')
            
        elif algorithm == 'MP_LB':
            self.logger.log("Perform MP_LB algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/MP_LP/target/MP_LP-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            self.logger.log('\n')
            
        elif algorithm == 'DRAF':
            self.logger.log("Perform DRAF algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/DRAF/target/DRAF-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            self.logger.log('\n')
            
        elif algorithm == 'SDFFR':
            self.logger.log("Perform SDFFR algorithm")
            os.system('sudo python3 /home/lce/yukai_thesis/experiment/SD-FFR/pre_install_select_novlan_spforex.py')
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/SDFFR/target/SDFFR-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            ONOSConfig.configure_onos()
            self.logger.log('\n')
            
        elif algorithm == 'SDFFR_MP':
            self.logger.log("Perform SD-FFR algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/SDFFR_MP/target/SDFFR_MP-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            ONOSConfig.configure_onos()
            self.logger.log('\n')
            
        elif algorithm == 'SDFFR_MP_LB':
            self.logger.log("Perform SDFFR_MP_LB algorithm")
            os.system('sudo curl -X POST -H Content-Type:application/octet-stream http://127.0.0.1:8181/onos/v1/applications --data-binary @/home/lce/onos/apps/SDFFR_MP_LB/target/SDFFR_MP_LB-1.0-SNAPSHOT.oar --user onos:rocks')
            os.system('curl -X POST --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app/active" --user onos:rocks')
            ONOSConfig.configure_onos()
            self.logger.log('\n')
        
        while True and algorithm == 'SDFFR':
            time.sleep(1)
            self.logger.log('Check if the configuration of the algorithm is completed')
            if os.path.isfile('./config_done'):
                os.remove('./config_done')
                break

        while True:
            time.sleep(1)
            self.logger.log('Check if the algorithm is ready')
            if os.path.isfile('./Algorithm_state->Ready'):
                return True
            if os.path.isfile('./Algorithm_state->Error'):
                return False
    
    def close_algorithm(self):
        os.system('curl -X DELETE --header "Accept: application/json" "http://localhost:8181/onos/v1/applications/org.foo.app" --user onos:rocks') 