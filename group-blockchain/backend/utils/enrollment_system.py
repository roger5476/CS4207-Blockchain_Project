import hashlib
import threading
from threading import Lock
from web3 import Web3

# Block Class from lab-05
class Block:
    def __init__(self, index: int, previous_hash: str, data: dict):
        self.index = index
        self.previous_hash = previous_hash
        self.data = data
        self.hash = self._hash_computation()

    def _hash_computation(self) -> str:
        block_content = f"{self.index}{self.previous_hash}{self.data}"
        return hashlib.sha256(block_content.encode()).hexdigest()

# BlockChain Class from lab-05
class Blockchain:
    def __init__(self):
        self.chain = [self._create_initial_block()]

    def _create_initial_block(self):
        return Block(0, "0", {"info": "Genesis Block"})

    def add_block(self, data: dict):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), previous_block.hash, data)
        self.chain.append(new_block)

# EnrollmentSystem Class combining lab-06 with blockchain integration
class EnrollmentSystem:
    def __init__(self, web3_provider, contract_address, contract_abi, admin_address, admin_private_key):
        # Web3 setup
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract = self.web3.eth.contract(address=contract_address, abi=contract_abi)
        
        # Admin credentials
        self.admin_address = admin_address
        self.admin_private_key = admin_private_key
        
        # From lab-06
        self.students = {}
        self.modules = {}
        self.blockchain = Blockchain()
        self.lock = Lock()

    def add_student(self, student_id: str):
        """Add student to local tracking"""
        self.students[student_id] = {
            "completed_courses": set(),
            "address": None
        }

    def add_module(self, course_code: str, prerequisites=None, available_slots=1):
        """Add module to local tracking"""
        self.modules[course_code] = {
            "prerequisites": prerequisites if prerequisites else [],
            "available_slots": available_slots
        }

    def _prerequisites_met(self, student_id: str, course_code: str) -> bool:
        """Check prerequisites locally before blockchain transaction"""
        if student_id not in self.students or course_code not in self.modules:
            return False
        
        prerequisites = self.modules[course_code]["prerequisites"]
        completed_courses = self.students[student_id]["completed_courses"]
        return all(prereq in completed_courses for prereq in prerequisites)

    def enroll(self, student_id: str, course_code: str, student_address: str, private_key: str):
        """Thread-safe enrollment combining local and blockchain operations"""
        with self.lock:
            try:
                # Local prerequisite check
                if not self._prerequisites_met(student_id, course_code):
                    return "Prerequisites not met"

                # Check blockchain course availability
                course_details = self.contract.functions.getCourseDetails(course_code).call()
                if not course_details[3]:  # isActive check
                    return "Course not available"

                # Build and send blockchain transaction
                nonce = self.web3.eth.get_transaction_count(student_address)
                txn = self.contract.functions.enroll(course_code).build_transaction({
                    'from': student_address,
                    'nonce': nonce,
                    'gas': 3000000,
                    'gasPrice': self.web3.eth.gas_price
                })

                signed_txn = self.web3.eth.account.sign_transaction(txn, private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt['status'] == 1:
                    # Add to local blockchain record
                    self.blockchain.add_block({
                        "student_id": student_id,
                        "course_code": course_code,
                        "transaction_hash": tx_hash.hex()
                    })
                    return f"Successfully enrolled in {course_code}"
                else:
                    return "Enrollment failed"

            except Exception as e:
                return f"Error during enrollment: {str(e)}"

    def complete_course(self, student_id: str, course_code: str):
        """Mark course as completed locally"""
        if student_id in self.students:
            self.students[student_id]["completed_courses"].add(course_code)
            return True
        return False

    def add_course(self, name: str, available_seats: int, prerequisites: list):
        """Add a new course to both local storage and blockchain"""
        try:
            with self.lock:
                print("\n=== Debug Info ===")
                print(f"Adding course: {name}")
                print(f"Available seats: {available_seats}")
                print(f"Prerequisites: {prerequisites}")
                print(f"Admin address: {self.admin_address}")
                print(f"Contract address: {self.contract.address}")
                print(f"Private key length: {len(self.admin_private_key)}")
                
                if name in self.modules:
                    return "Course already exists"

                try:
                    # Get nonce
                    nonce = self.web3.eth.get_transaction_count(self.admin_address)
                    print(f"Nonce: {nonce}")

                    # Build transaction
                    print("Building transaction...")
                    txn = self.contract.functions.addCourse(
                        name,
                        available_seats,
                        prerequisites
                    ).build_transaction({
                        'from': self.admin_address,
                        'nonce': nonce,
                        'gas': 3000000,
                        'gasPrice': self.web3.eth.gas_price
                    })
                    print("Transaction built successfully")

                    # Sign transaction
                    print("Signing transaction...")
                    signed_txn = self.web3.eth.account.sign_transaction(
                        txn, 
                        private_key=self.admin_private_key
                    )
                    print("Transaction signed successfully")

                    # Send transaction
                    print("Sending transaction...")
                    tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"Transaction hash: {tx_hash.hex()}")

                    # Wait for receipt
                    print("Waiting for receipt...")
                    receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    print(f"Transaction receipt status: {receipt['status']}")

                    if receipt['status'] == 1:
                        self.modules[name] = {
                            "prerequisites": prerequisites,
                            "available_slots": available_seats
                        }
                        return "Course added successfully"
                    else:
                        return "Transaction failed"

                except Exception as inner_e:
                    print(f"Inner error details: {str(inner_e)}")
                    return f"Transaction error: {str(inner_e)}"

        except Exception as e:
            print(f"Outer error details: {str(e)}")
            return f"Failed to add course: {str(e)}"

    def get_all_courses(self):
        """Get all courses from the blockchain"""
        try:
            print("\n=== Getting All Courses ===")
            print(f"Modules in memory: {self.modules}")
            courses = []

            for name, details in self.modules.items():
                try:
                    print(f"Fetching details for course: {name}")
                    course_details = self.contract.functions.getCourseDetails(name).call()
                    print(f"Got course details: {course_details}")

                    course = {
                        "name": name,
                        "availableSeats": course_details[1],
                        "prerequisites": course_details[2],
                        "isActive": course_details[3]
                    }
                    print(f"Adding course to list: {course}")
                    courses.append(course)
                except Exception as e:
                    print(f"Error getting course {name}: {str(e)}")
                    continue

            print(f"Returning courses: {courses}")
            return courses
        except Exception as e:
            print(f"Error in get_all_courses: {str(e)}")
            return []