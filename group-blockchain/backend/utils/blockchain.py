from web3 import Web3
from config.settings import GANACHE_URL, CONTRACT_ADDRESS, CONTRACT_ABI

class BlockchainManager:
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        self.contract = self.web3.eth.contract(
            address=CONTRACT_ADDRESS, 
            abi=CONTRACT_ABI
        )

    def get_course_details(self, course_code):
        """Get course details from blockchain"""
        try:
            return self.contract.functions.getCourseDetails(course_code).call()
        except Exception as e:
            return None

    def add_course(self, admin_address, name, seats, prerequisites, private_key):
        """Add a new course to the blockchain"""
        try:
            nonce = self.web3.eth.get_transaction_count(admin_address)
            txn = self.contract.functions.addCourse(
                name, 
                seats, 
                prerequisites
            ).build_transaction({
                'from': admin_address,
                'nonce': nonce,
                'gas': 3000000,
                'gasPrice': self.web3.eth.gas_price
            })

            signed_txn = self.web3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return receipt['status'] == 1
        except Exception as e:
            return False
