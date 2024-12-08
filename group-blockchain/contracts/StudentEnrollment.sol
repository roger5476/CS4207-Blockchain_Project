// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StudentEnrollment {
    struct Course {
        string name;
        uint availableSeats;
        string[] prerequisites;
        bool isActive;
    }

    struct Student {
        bool exists;
        string[] completedCourses;
    }

    mapping(string => Course) public courses;
    mapping(address => Student) public students;
    mapping(address => mapping(string => bool)) public enrollmentStatus;
    
    // Lock mechanism for race condition prevention
    mapping(string => bool) private courseLocks;
    
    modifier noReentrancy(string memory _courseName) {
        require(!courseLocks[_courseName], "Transaction in progress");
        courseLocks[_courseName] = true;
        _;
        courseLocks[_courseName] = false;
    }

    event CourseAdded(string name, uint seats, string[] prerequisites);
    event CourseAddError(string reason);

    // Add this at the top of the contract to track course names
    string[] private courseNames;

    // Add mapping for completed courses
    mapping(address => string[]) public completedCourses;
    
    // Add event for course completion
    event CourseCompleted(address student, string courseName);

    function addCourse(
        string memory _name,
        uint _availableSeats,
        string[] memory _prerequisites
    ) public {
        require(!courses[_name].isActive, "Course already exists");
        
        // Add course
        courses[_name] = Course(_name, _availableSeats, _prerequisites, true);
        courseNames.push(_name);
        
        // Debug event
        emit CourseAdded(_name, _availableSeats, _prerequisites);
    }

    function hasCompletedPrerequisites(
        address _student, 
        string memory _courseName
    ) public view returns (bool) {
        string[] memory prerequisites = courses[_courseName].prerequisites;
        
        // If no prerequisites, return true
        if (prerequisites.length == 0) return true;
        
        // Check each prerequisite
        for (uint i = 0; i < prerequisites.length; i++) {
            bool found = false;
            // Check against completed courses
            for (uint j = 0; j < completedCourses[_student].length; j++) {
                if (keccak256(bytes(prerequisites[i])) == keccak256(bytes(completedCourses[_student][j]))) {
                    found = true;
                    break;
                }
            }
            if (!found) return false;  // If any prerequisite not found, return false
        }
        return true;  // All prerequisites found
    }

    function enroll(string memory _courseName) public noReentrancy(_courseName) {
        require(courses[_courseName].isActive, "Course does not exist");
        require(courses[_courseName].availableSeats > 0, "No seats available");
        require(!enrollmentStatus[msg.sender][_courseName], "Already enrolled");
        require(hasCompletedPrerequisites(msg.sender, _courseName), "Prerequisites not met");

        enrollmentStatus[msg.sender][_courseName] = true;
        courses[_courseName].availableSeats--;
    }

    function completeCourse(address _student, string memory _courseName) public {
        require(enrollmentStatus[_student][_courseName], "Not enrolled in this course");
        
        // Add to completed courses
        completedCourses[_student].push(_courseName);
        
        emit CourseCompleted(_student, _courseName);
    }

    function getCourseDetails(string memory _courseName) 
        public 
        view 
        returns (
            string memory name,
            uint availableSeats,
            string[] memory prerequisites,
            bool isActive
        ) 
    {
        Course memory course = courses[_courseName];
        return (
            course.name,
            course.availableSeats,
            course.prerequisites,
            course.isActive
        );
    }

    function getAllCourses() public view returns (
        string[] memory names,
        uint[] memory seats,
        string[][] memory prereqs,
        bool[] memory active
    ) {
        // First count active courses
        uint count = 0;
        for (uint i = 0; i < courseNames.length; i++) {
            if (courses[courseNames[i]].isActive) {
                count++;
            }
        }

        // Initialize arrays with the correct size
        names = new string[](count);
        seats = new uint[](count);
        prereqs = new string[][](count);
        active = new bool[](count);

        // Fill arrays
        uint index = 0;
        for (uint i = 0; i < courseNames.length; i++) {
            string memory name = courseNames[i];
            if (courses[name].isActive) {
                names[index] = name;
                seats[index] = courses[name].availableSeats;
                prereqs[index] = courses[name].prerequisites;
                active[index] = true;
                index++;
            }
        }

        return (names, seats, prereqs, active);
    }
}
