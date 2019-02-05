"""Unit test of application API

This module contains unit tests for application API
Unit tests are executed using a local sqlite in the base directory
"""
import os
import unittest
import sys
import json

sys.path.append("..")
 
from app import app

# Sets config for app so that db can load the new config
TEST_DB = 'test.db'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(app.config['BASE_DIR'], TEST_DB)

from app import db
db = db.DB(app)

class BasicTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################
 
    # executed prior to each test
    def setUp(self):
        self.app = app.test_client()
        self.session = db.DBSession()
        db.drop_all()
        db.create_all(self.session)
        self.session.commit()
        
 
 
    # executed after each test
    def tearDown(self):
        db.drop_all()
        self.session.close()
 
 
###############
#### tests ####
###############

    # Test registration API
    def test_register(self):
        # Common cases
        # Test valid registration of single student
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "students":["student_agnes@example.com"]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,204,"Registration API POST Failed")
        
        # Test valid registration of multiple students
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "students":[
                        "student_agnes@example.com",
                        "studenthon@example.com"
                        ]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,204,"Registration API POST Failed")
        
        # Test invalid JSON format
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "students":"teacherken@gmail.com",
                "teacher":[
                        "student_agnes@example.com",
                        "studenthon@example.com"
                        ]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        res = self.app.post('/api/register')
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "students":[]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        
        # Test non-existent teacher/student mail
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"studentmiche@example.com",
                "students":[
                        "student_agnes@example.com",
                        "studenthon@example.com"
                        ]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 404,"Non-existent teacher accepted")
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "students":["teacherbob@mail.edu.sg"]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 404,"Non-existent student accepted")
        
        # Edge cases
        # Test large list of students
        res = self.app.post(
            '/api/register',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "students":["studenthon@example.com"] * 1024
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 204,"Registration API POST Failed")
        
        
    # Test get common students API
    def test_get_common_students(self):
        # Common cases
        # Test retrieval of single student under single teacher
        res = self.app.get('/api/commonstudents?teacher=teacherken%40gmail.com')
        students = res.json['students']
        self.assertEqual(res.status_code,200,"Unable to fetch students from existing teacher")
        self.assertTrue("studentjon@example.com" in students,"Existing student not detected under existing teacher")
        self.assertTrue(len(students)==1,"Duplicate or extra students detected under existing teacher")
        
        # Test retrieval of multiple students under single teacher
        res = self.app.get('/api/commonstudents?teacher=teacherkatherine%40yahoo.com')
        students = res.json['students']
        self.assertEqual(res.status_code,200,"Unable to fetch students from existing teacher")
        self.assertTrue("studentjon@example.com" in students,"Existing student not detected under existing teacher")
        self.assertTrue("studenthon@example.com" in students,"Existing student not detected under existing teacher")
        self.assertTrue(len(students)==2,"Duplicate or extra students detected under existing teacher")
        
        # Test retrieval of student under multiple teachers
        res = self.app.get('/api/commonstudents?teacher=teacherken%40gmail.com&teacher=teacherkatherine%40yahoo.com')
        students = res.json['students']
        self.assertEqual(res.status_code,200,"Unable to fetch students from existing teacher")
        self.assertTrue("studentjon@example.com" in students,"Existing student not detected under existing teacher")
        self.assertTrue(len(students)==1,"Duplicate or extra students detected under existing teacher")
        
        # Test invalid teacher mail
        res = self.app.get('/api/commonstudents?teacher=studentjon%40example.com')
        students = res.json['students']
        self.assertEqual(res.status_code,200,"Unable to fetch students from non-existent teacher")
        self.assertTrue(len(students)==0,"Students retrieved for non-existent teacher")
        
        # Test missing teacher mail
        res = self.app.get('/api/commonstudents')
        self.assertEqual(res.status_code, 400,"Missing parameter not rejected")
        
    # Test suspension API
    def test_suspend(self):
        # Common cases
        # Test suspension of valid student
        res = self.app.post(
            '/api/suspend',
            data=json.dumps({
                "student":"studentjon@example.com"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,204,"Suspend API failed to suspend valid student")
        
        # Test invalid JSON format
        res = self.app.post(
            '/api/suspend',
            data=json.dumps({
                "student":[
                        "studentjon@example.com",
                        "studenthon@example.com"
                        ]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,400,"Invalid JSON not rejected")
        res = self.app.post(
            '/api/suspend',
            data=json.dumps({
                "student":""
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,400,"Invalid JSON not rejected")
        res = self.app.post(
            '/api/suspend',
            data=json.dumps({
                "teacher":"studentjon@example.com"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,400,"Invalid JSON not rejected")
        
        # Test suspension of invalid student
        res = self.app.post(
            '/api/suspend',
            data=json.dumps({
                "student":"teacherken@gmail.com"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,404,"Suspend API suspended invalid student")
        
    # Test student notification API
    def test_retrieve_for_notifications(self):
        # Common cases
        # Test retrieval of student under teacher with no notication references
        res = self.app.post(
            '/api/retrievefornotifications',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "notification":"Hello"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,200,"Failed to retrieve students from existing teacher")
        students = res.json['students']
        self.assertTrue("studentjon@example.com" in students,"Failed to retrieve correct student from existing teacher")
        self.assertTrue(len(students)==1,"Duplicate or extra students detected under existing teacher")
        
        # Test retrieval of students under teacher with notification references
        res = self.app.post(
            '/api/retrievefornotifications',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "notification":"Hello @student_agnes@example.com @studentmiche@example.com @teacherbob@mail.edu.sg"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,200,"Failed to retrieve students with notification")
        students = res.json['students']
        self.assertTrue("studentjon@example.com" in students,"Failed to retrieve correct student from existing teacher")
        self.assertTrue("student_agnes@example.com" in students,"Failed to retrieve correct student from notification reference")
        self.assertTrue("studentmiche@example.com" in students,"Failed to retrieve correct student from notification reference")
        self.assertTrue(len(students)==3,"Duplicate or extra students detected under existing teacher")
        
        # Test invalid JSON format
        res = self.app.post(
            '/api/retrievefornotifications',
            data=json.dumps({
                "teacher":"teacherken@gmail.com",
                "notification":[
                        "student_agnes@example.com",
                        "studenthon@example.com"
                        ]
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        res = self.app.post('/api/retrievefornotifications')
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        res = self.app.post(
            '/api/retrievefornotifications',
            data=json.dumps({
                "teacher":None,
                "notification":"Hello"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400,"Invalid JSON not rejected")
        
        # Test non-existant teacher
        res = self.app.post(
            '/api/retrievefornotifications',
            data=json.dumps({
                "teacher":"studentmiche@example.com",
                "notification":"Hello"
                }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code,404,"Failed to reject non-existent teacher")
        

 
 
if __name__ == "__main__":
    unittest.main()