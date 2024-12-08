from web3 import Web3
import json
import os

# Blockchain Configuration
GANACHE_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = Web3.to_checksum_address('0x2c63Ddb5287f4145a723679d65424606b65dDefe')

# Admin Configuration
ADMIN_ADDRESS = Web3.to_checksum_address("0x7A74E60d64f28f12D737628Cf32Fbac824f2a258")
ADMIN_PRIVATE_KEY = "6c37a3e500efba447728dbd8cbf8bc7c60a97000111ab1f04de4c1387800b3a1"

# Load ABI from build file
try:
    # Get the path to the build file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    build_path = os.path.join(project_root, 'build', 'contracts', 'StudentEnrollment.json')
    
    # Load and parse the JSON file
    with open(build_path, 'r') as file:
        contract_json = json.load(file)
        CONTRACT_ABI = contract_json['abi']
        
    # Convert JavaScript booleans to Python booleans
    def convert_booleans(obj):
        if isinstance(obj, dict):
            return {k: convert_booleans(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_booleans(item) for item in obj]
        elif obj == 'false':
            return False
        elif obj == 'true':
            return True
        return obj
        
    CONTRACT_ABI = convert_booleans(CONTRACT_ABI)
    
except Exception as e:
    print(f"Error loading ABI: {e}")
    CONTRACT_ABI = []  # Empty ABI as fallback
