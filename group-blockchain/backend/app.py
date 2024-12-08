from flask import Flask, request, jsonify
from utils.enrollment_system import EnrollmentSystem
from config.settings import GANACHE_URL, CONTRACT_ADDRESS, CONTRACT_ABI, ADMIN_ADDRESS, ADMIN_PRIVATE_KEY
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

enrollment_system = EnrollmentSystem(
    GANACHE_URL, 
    CONTRACT_ADDRESS, 
    CONTRACT_ABI,
    ADMIN_ADDRESS,
    ADMIN_PRIVATE_KEY
)

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all available courses"""
    try:
        courses = enrollment_system.get_all_courses()  # This will get courses from blockchain
        return jsonify({
            "success": True, 
            "courses": courses
        })
    except Exception as e:
        print(f"Error getting courses: {str(e)}")  # Debug log
        return jsonify({
            "success": False, 
            "error": str(e)
        })

@app.route('/api/enroll', methods=['POST'])
def enroll_student():
    """Enroll a student in a course"""
    try:
        data = request.json
        result = enrollment_system.enroll(
            student_id=data['student_id'],
            course_code=data['course_code'],
            student_address=data['student_address'],
            private_key=data['private_key']
        )
        return jsonify({"success": True, "message": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/prerequisites/<course_code>', methods=['GET'])
def check_prerequisites(course_code):
    """Check prerequisites for a course"""
    try:
        if course_code in enrollment_system.modules:
            prerequisites = enrollment_system.modules[course_code]["prerequisites"]
            return jsonify({
                "success": True,
                "prerequisites": prerequisites
            })
        return jsonify({"success": False, "error": "Course not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Admin routes
@app.route('/api/admin/add_course', methods=['POST'])
def add_course():
    """Admin endpoint to add a new course"""
    try:
        data = request.json
        print("Received data:", data)
        
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400
            
        result = enrollment_system.add_course(
            name=data['name'],
            available_seats=data['available_seats'],
            prerequisites=data['prerequisites']
        )
        return jsonify({"success": True, "message": result})
    except Exception as e:
        print(f"Error in add_course: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/courses', methods=['GET'])
def get_admin_courses():
    """Admin endpoint to view all courses"""
    try:
        courses = enrollment_system.get_all_courses()
        return jsonify({"success": True, "courses": courses})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# The URLs will be:
# Admin Add Course: http://localhost:5000/api/admin/add_course
# Admin View Courses: http://localhost:5000/api/admin/courses

if __name__ == '__main__':
    app.run(debug=True, port=5000)
