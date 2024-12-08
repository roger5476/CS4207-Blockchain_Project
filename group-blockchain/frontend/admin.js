let adminAccount = null;
let web3 = null;
let contract = null;

// Connect admin wallet
async function connectAdminWallet() {
    console.log('Connecting wallet...');
    
    if (typeof window.ethereum !== 'undefined') {
        try {
            // Request account access
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });
            
            adminAccount = accounts[0];
            console.log('Connected to account:', adminAccount);

            // Initialize Web3
            web3 = new Web3(window.ethereum);
            
            // Convert contract address to checksum
            CONTRACT_ADDRESS = web3.utils.toChecksumAddress(CONTRACT_ADDRESS);
            
            // Initialize contract
            contract = new web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS);
            
            // Update UI
            document.getElementById('walletAddress').textContent = `Connected: ${adminAccount}`;
            
            // Load courses
            await loadCourses();
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', function (accounts) {
                window.location.reload();
            });

        } catch (error) {
            console.error('Connection error:', error);
            showStatus('Failed to connect wallet: ' + error.message, 'error');
        }
    } else {
        showStatus('Please install MetaMask', 'error');
    }
}

// Load existing courses
async function loadCourses() {
    try {
        if (!contract) {
            console.log('Initializing contract...');
            contract = new web3.eth.Contract(CONFIG.CONTRACT_ABI, CONFIG.CONTRACT_ADDRESS);
        }

        console.log('Loading courses from blockchain...');
        const result = await contract.methods.getAllCourses().call();
        console.log('Raw blockchain response:', result);

        // Format courses for display
        const courses = [];
        for (let i = 0; i < result.names.length; i++) {
            if (result.active[i]) {
                courses.push({
                    name: result.names[i],
                    availableSeats: parseInt(result.seats[i]),
                    prerequisites: result.prereqs[i] || [],
                    isActive: result.active[i]
                });
            }
        }

        console.log('Formatted courses:', courses);
        displayCourses(courses);
    } catch (error) {
        console.error('Error loading courses:', error);
        showStatus('Failed to load courses', 'error');
    }
}

// Display courses in the UI
function displayCourses(courses) {
    const courseList = document.getElementById('courseList');
    const completedCourseSelect = document.getElementById('completedCourse');
    
    // Clear existing content
    courseList.innerHTML = '';
    completedCourseSelect.innerHTML = '<option value="">Select a course</option>';

    courses.forEach(course => {
        // Display in course list
        const courseDiv = document.createElement('div');
        courseDiv.className = 'course-item';
        courseDiv.innerHTML = `
            <h3>${course.name}</h3>
            <p>Available Seats: ${course.availableSeats}</p>
            <p>Prerequisites: ${course.prerequisites.join(', ') || 'None'}</p>
        `;
        courseList.appendChild(courseDiv);

        // Add to completion dropdown
        const option = document.createElement('option');
        option.value = course.name;
        option.textContent = course.name;
        completedCourseSelect.appendChild(option);
    });
}

// Add new course
async function addCourse() {
    if (!adminAccount || !web3 || !contract) {
        showStatus('Please connect admin wallet first', 'error');
        return;
    }

    const name = document.getElementById('courseName').value;
    const seats = parseInt(document.getElementById('seats').value);
    const prerequisites = document.getElementById('prerequisites').value
        .split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0);

    if (!name || !seats) {
        showStatus('Please fill in all required fields', 'error');
        return;
    }

    try {
        console.log('Adding course with details:', { name, seats, prerequisites });

        // Create transaction
        console.log('Creating transaction...');
        const txn = await contract.methods.addCourse(
            name,
            seats,
            prerequisites
        ).send({
            from: adminAccount,
            gas: 3000000
        });

        console.log('Transaction result:', txn);

        if (txn.status) {
            showStatus('Course added successfully', 'success');
            loadCourses();
            // Clear form
            document.getElementById('courseName').value = '';
            document.getElementById('seats').value = '30';
            document.getElementById('prerequisites').value = '';
        } else {
            showStatus('Transaction failed', 'error');
        }
    } catch (error) {
        console.error('Error adding course:', error);
        showStatus('Failed to add course: ' + error.message, 'error');
    }
}

// Show status messages
function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-section ${type}`;
}

// Event Listeners
document.getElementById('connectWallet').addEventListener('click', connectAdminWallet);
document.getElementById('addCourseBtn').addEventListener('click', addCourse);

// Load courses on page load
document.addEventListener('DOMContentLoaded', () => {
    if (window.ethereum && window.ethereum.selectedAddress) {
        connectAdminWallet();
    }
});

// Add function to mark course as completed
async function markCourseCompleted() {
    if (!adminAccount || !web3 || !contract) {
        showStatus('Please connect admin wallet first', 'error');
        return;
    }

    const studentAddress = document.getElementById('studentAddress').value;
    const courseName = document.getElementById('completedCourse').value;

    try {
        const txn = await contract.methods.completeCourse(
            studentAddress,
            courseName
        ).send({
            from: adminAccount,
            gas: 3000000
        });

        if (txn.status) {
            showStatus('Course marked as completed', 'success');
        } else {
            showStatus('Failed to mark course as completed', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Error marking course as completed: ' + error.message, 'error');
    }
} 