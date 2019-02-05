"""Application APIs
"""

from flask import Flask, Response, request, jsonify
from app import db, errors

# Constants defintion
room_info_dic = {"1.101":{"type":"office","occupant":"Angry Bird","capacity":1},
                 "1.102":{"type":"classroom","occupant":"Drama Llama","capacity":30},
                "1.103":{"type":"classroom","occupant":"Awkward Seal","capacity":15},
                "1.201":{"type":"classroom","occupant":None,"capacity":15}}

app = Flask(__name__,instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

@app.route("/api/register",methods=['POST'])
def api_register():
    """Registers students under a teacher
    
    Endpoint:
        POST /api/register
    Headers: Content-Type:
        application/json
    Success response status:
        HTTP 204
    Request body example:
        {
            "teacher": "teacherken@gmail.com"
            "students":
            [
            "studentjon@example.com",
            "studenthon@example.com"
        }
    """
    # Load latest app config into db
    database = db.DB(app)
    
    # Check input format
    content = request.json
    if content==None:
        raise errors.InvalidUsage("Missing JSON, provide teacher mail and list of students under 'teacher' and 'students' respectively",status_code = 400)
    try:
        teacher = content['teacher']
        students= content['students']
    except KeyError:
        raise errors.InvalidUsage("Invalid JSON format, provide teacher mail and list of students under 'teacher' and 'students' respectively",status_code = 400)
    
    if teacher==None or students==None or len(teacher)<1 or len(students)<1:
        raise errors.InvalidUsage('Invalid JSON format, provide non-empty teacher mail and list of students',status_code = 400)
    if type(students)!=list:
        raise errors.InvalidUsage("Invalid JSON format, provide list of students under 'students'",status_code = 400)
    
    # Query and update db
    session = database.DBSession()
    if database.register_students(session,teacher,students):
        # Transaction completed successfully
        session.commit()
        session.close()
        return Response(status=204)
    else:
        # Return status code 404 = Not found, when teacher / students is not found in db
        session.rollback()
        session.close()
        raise errors.InvalidUsage('Provided mail(s) not found in database',status_code = 404)
        
@app.route("/api/commonstudents",methods=['GET'])
def api_get_common_students():
    """Retrieves students commonly registered to a list of teachers
    
    Endpoint:
        GET /api/commonstudents
    Success response status:
        HTTP 200
    Request example 1:
        GET /api/commonstudents?teacher=teacherken%40example.com
    Success response body 1:
        {
            "students" :
            [
                "commonstudent1@gmail.com",
                "commonstudent2@gmail.com",
                "student_only_under_teacher_ken@gmail.com"
            ]
        }
    Request example 2:
        GET /api/commonstudents?teacher=teacherken%40example.com&teacher=teacherjoe%40example.com
    Success response body 2:
        {
            "students" :
            [
                "commonstudent1@gmail.com",
                "commonstudent2@gmail.com"
            ]
        }
    """
    
    # Load latest app config into db
    database = db.DB(app)
    
    # Check input format
    try:
        teachers = dict(request.args)['teacher']
    except KeyError:
        raise errors.InvalidUsage("Invalid parameter format, provide teacher mail(s) under 'teacher'",status_code = 400)
    
    # Query db
    session = database.DBSession()
    students = database.get_student_mail_by_teachers(session,teachers) # set
    session.close()
    return jsonify({
        "students":list(students)
    })

@app.route("/api/suspend",methods=['POST'])
def api_suspend():
    """Suspends a specified student
    
    Endpoint: 
        POST /api/suspend
    Headers: 
        Content-Type: application/json
    Success response status: 
        HTTP 204
    Request body example:
        {
            "student" : "studentmary@gmail.com"
        }
    """
    # Load latest app config into db
    database = db.DB(app)
    
    # Check input format
    content = request.json
    if content==None:
        raise errors.InvalidUsage("Missing JSON, provide student mail under 'student'",status_code = 400)
    try:
        student = content['student']
    except KeyError:
        raise errors.InvalidUsage("Invalid JSON format, provide student mail under 'student'",status_code = 400)
    
    if student==None or len(student)<1:
        raise errors.InvalidUsage('Invalid JSON format, provide non-empty student mail',status_code = 400)
    if type(student)!=str:
        raise errors.InvalidUsage("Invalid JSON format, provide student mail under 'students' as a string",status_code = 400)
        
    # Query and update db
    session = database.DBSession()
    if database.suspend_student(session,student):
        session.commit()
        session.close()
        return Response(status=204)
    else:
        # Return status code 404 = Not found, when student is not found in db
        session.rollback()
        session.close()
        raise errors.InvalidUsage('Provided mail(s) not found in database',status_code = 404)
    
@app.route("/api/retrievefornotifications",methods=['POST'])
def api_retrieve_for_notifications():
    """Retrieve a list of students who can receive a given notification.
    
    Endpoint: 
        POST /api/retrievefornotifications
    Headers: 
        Content-Type: application/json
    Success response status: 
        HTTP 200
    Request body example 1:
        {
            "teacher": "teacherken@example.com",
            "notification": "Hello students! @studentagnes@example.com @studentmiche@example.com"
        }
    Success response body 1:
        {
            "recipients":
            [
                "studentbob@example.com",
                "studentagnes@example.com",
                "studentmiche@example.com"
            ]
        }
    """
    # Load latest app config into db
    database = db.DB(app)
    
    # Check input format
    content = request.json
    if content==None:
        raise errors.InvalidUsage("Missing JSON, provide teacher mail under 'teacher' and message under 'notification'",status_code = 400)
    try:
        teacher = content['teacher']
        notification = content['notification']
    except KeyError:
        raise errors.InvalidUsage("Invalid JSON format, provide teacher mail under 'teacher' and message under 'notification'",status_code = 400)
    
    if teacher == None or len(teacher)<1 or type(teacher)!=str:
        raise errors.InvalidUsage("Invalid JSON format, provide teacher mail under 'teacher' string",status_code = 400)
    if notification == None or type(notification) != str:
        raise errors.InvalidUsage("Invalid JSON format, provide message under 'notification' as string",status_code = 400)
        
    # Query db
    session = database.DBSession()
    if not database.is_teacher_exist(session,teacher):
        raise errors.InvalidUsage("Provided teacher mail not found in database",status_code=404)
    students = database.get_student_mail_by_notification(session,teacher,notification)
    session.close()
    return jsonify({
        "students":list(students)
    })

@app.errorhandler(errors.InvalidUsage)
def handle_invalid_usage(error):
    """Handles error with an appropriate HTTP code and JSON response
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

