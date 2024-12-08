let userAccount = null;
let web3 = null;
let contract = null;

// Connect to MetaMask
async function connectWallet() {
    console.log('Connecting wallet...');
    
    if (typeof window.ethereum !== 'undefined') {
        try {
            const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
            userAccount = accounts[0];
            console.log('Connected to account:', userAccount);

            // Initialize Web3
            web3 = new Web3(window.ethereum);
            
            // Initialize contract
            contract = new web3.eth.Contract(CONFIG.CONTRACT_ABI, CONFIG.CONTRACT_ADDRESS);
            
            document.getElementById('walletAddress').textContent = `Connected: ${userAccount}`;
            
            // Load courses after connection
            await loadCourses();

        } catch (error) {
            console.error('Connection error:', error);
            showStatus('Failed to connect wallet: ' + error.message, 'error');
        }
    } else {
        showStatus('Please install MetaMask', 'error');
    }
}

// Load available courses
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
    const courseSelect = document.getElementById('courseSelect');
    
    courseList.innerHTML = '';
    courseSelect.innerHTML = '<option value="">Select a course</option>';

    if (!courses || courses.length === 0) {
        const noCoursesDiv = document.createElement('div');
        noCoursesDiv.textContent = 'No courses available';
        courseList.appendChild(noCoursesDiv);
        return;
    }

    courses.forEach(course => {
        // Display in course list
        const courseDiv = document.createElement('div');
        courseDiv.className = 'course-item';
        courseDiv.innerHTML = `
            <h3>${course.name}</h3>
            <p>Available Seats: ${course.availableSeats}</p>
            <p class="prerequisites">Prerequisites: ${course.prerequisites.length > 0 ? 
                '<ul>' + course.prerequisites.map(p => `<li>${p}</li>`).join('') + '</ul>' 
                : 'None'}</p>
        `;
        courseList.appendChild(courseDiv);

        // Add to dropdown
        const option = document.createElement('option');
        option.value = course.name;
        option.textContent = `${course.name} (${course.availableSeats} seats${
            course.prerequisites.length > 0 ? 
            ` - Prerequisites: ${course.prerequisites.join(', ')}` : 
            ''})`;
        courseSelect.appendChild(option);
    });
}

// Enroll in a course
async function enrollInCourse() {
    if (!userAccount) {
        showStatus('Please connect your wallet first', 'error');
        return;
    }

    const courseName = document.getElementById('courseSelect').value;
    if (!courseName) {
        showStatus('Please select a course', 'error');
        return;
    }

    try {
        // Check prerequisites first
        const hasPrereqs = await contract.methods.hasCompletedPrerequisites(userAccount, courseName).call();
        if (!hasPrereqs) {
            showStatus('You have not completed the prerequisites for this course', 'error');
            return;
        }

        // If prerequisites met, try to enroll
        const txn = await contract.methods.enroll(courseName).send({
            from: userAccount,
            gas: 3000000
        });

        if (txn.status) {
            showStatus('Successfully enrolled in course', 'success');
            loadCourses();
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Enrollment failed: ' + error.message, 'error');
    }
}

// Show status messages
function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-section ${type}`;
}

// Event Listeners
document.getElementById('connectWallet').addEventListener('click', connectWallet);
document.getElementById('enrollButton').addEventListener('click', enrollInCourse); 