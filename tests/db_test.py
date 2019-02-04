import os
import unittest
import sys

sys.path.append("..")
 
from app import app

# Sets config for app so that db can load the new config
TEST_DB = 'test.db'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(app.config['BASE_DIR'], TEST_DB)

#from app import db
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
    
    # Tests formatting/deformatting of mail addresses
    def test_mail_formatting(self):
        # Common cases
        # Test mail formatting
        self.assertEqual(db.format_mail("abc@DEF.GHI.com"),"'abc@DEF.GHI.com'","format_mail failed to encapsulate mail address in quotes")
        self.assertEqual(db.format_mail("'abc@DEF.GHI.com'"),"'abc@DEF.GHI.com'","format_mail failed to avoid encapsulating quoted mail address in quotes")
        
        # Test mail deformatting
        self.assertEqual(db.deformat_mail("'abc@DEF.GHI.com'"),"abc@DEF.GHI.com","deformat_mail failed to remove quotes from common case mail address")
        self.assertEqual(db.deformat_mail("abc@DEF.GHI.com"),"abc@DEF.GHI.com","deformat_mail failed to avoid modifying unquoted mail address")
        
        # Edge cases
        self.assertEqual(db.format_mail(""),"","format_mail failed to format empty mail address")
        self.assertEqual(db.deformat_mail(""),"","deformat_mail failed to deformat empty mail address")
    
    # Tests search for mail addresses
    def test_mail_existence(self):
        session = self.session
        # Common cases
        # Tests search for student mail
        self.assertTrue(db.is_student_exist(session,"studentjon@example.com"),"Unable to detect existing student")
        self.assertTrue(db.is_student_exist(session,"'studentjon@example.com'"),"Unable to detect existing student")
        self.assertFalse(db.is_student_exist(session,"'studentjon@example.com"),"Falsely detected non-existant student")
        
        # Tests search for teacher mail
        self.assertTrue(db.is_teacher_exist(session,"'teacherkatherine@yahoo.com'"),"Unable to detect existing teacher")
        self.assertTrue(db.is_teacher_exist(session,"teacherkatherine@yahoo.com"),"Unable to detect existing teacher")
        self.assertFalse(db.is_teacher_exist(session,"'teacherkatherine@yahoo.com"),"Falsely detected non-existant teacher")
        
    # Tests fetching of specified student / teacher
    def test_get_person(self):
        session = self.session
        # Common cases
        # Test fetching of students
        student = db.get_student(session,"student_agnes@example.com")
        self.assertIsNotNone(student,"Unable to fetch existing student")
        self.assertEqual(student.mail,"'student_agnes@example.com'","Fetched wrong student")
        student = db.get_student(session,"teacherkatherine@yahoo.com")
        self.assertIsNone(student,"Fetched student when there should be none")
        
        # Test fetching of teachers
        teacher = db.get_teacher(session,"'teacherkatherine@yahoo.com'")
        self.assertIsNotNone(teacher,"Unable to fetch existing teacher")
        self.assertEqual(teacher.mail,"'teacherkatherine@yahoo.com'","Fetched wrong teacher")
        teacher = db.get_teacher(session,"student_agnes@example.com")
        self.assertIsNone(teacher,"Fetched teacher when there should be none")
        
    # Test fetching of student under a single teacher
    def test_get_student_mail_by_teacher(self):
        session = self.session
        # Common cases
        # Test presence of student(s) under 1 teacher
        mail_list = db.get_student_mail_by_teacher(session,"teacherkatherine@yahoo.com")
        for mail in ["studentjon@example.com","studenthon@example.com"]:
            self.assertTrue(mail in mail_list,"Unable to fetch student %s under teacher teacherkatherine@yahoo.com"%(mail))
        mail_list = db.get_student_mail_by_teacher(session,"'teacherken@gmail.com'")
        self.assertTrue("studentjon@example.com" in mail_list,"Unable to fetch student studentjon@example.com under teacher teacherken@gmail.com")
        
        # Test absence of student(s) under 1 teacher
        mail_list = db.get_student_mail_by_teacher(session,"studentjon@example.com")
        self.assertTrue(len(mail_list)<1,"Fetched students when there should be none")
        mail_list = db.get_student_mail_by_teacher(session,"teacherbob@mail.edu.sg")
        self.assertTrue(len(mail_list)<1,"Fetched students when there should be none")
        
    # Test fetching of student under teachers
    def test_get_student_mail_by_teachers(self):
        session = self.session
        # Common cases
        # Test presence of student(s) under 1 teacher
        mail_list = db.get_student_mail_by_teachers(session,["teacherkatherine@yahoo.com"])
        for mail in ["studentjon@example.com","studenthon@example.com"]:
            self.assertTrue(mail in mail_list,"Unable to fetch student %s under teacher teacherkatherine@yahoo.com"%(mail))
        mail_list = db.get_student_mail_by_teachers(session,["'teacherken@gmail.com'"])
        self.assertTrue("studentjon@example.com" in mail_list,"Unable to fetch student studentjon@example.com under teacher teacherken@gmail.com")
        
        # Test absence of student(s) under 1 teacher
        mail_list = db.get_student_mail_by_teachers(session,["studentjon@example.com"])
        self.assertTrue(len(mail_list)<1,"Fetched students when there should be none")
        mail_list = db.get_student_mail_by_teachers(session,["teacherbob@mail.edu.sg"])
        self.assertTrue(len(mail_list)<1,"Fetched students when there should be none")
        
        # Test fetching of student(s) under multiple teachers
        mail_list = db.get_student_mail_by_teachers(session,["teacherkatherine@yahoo.com","'teacherken@gmail.com'"])
        self.assertTrue("studentjon@example.com" in mail_list,"Unable to fetch student studentjon@example.com under teachers teacherkatherine@yahoo.com and teacherken@gmail.com")
    
    # Test suspension of student    
    def test_suspend_student(self):
        session = self.session
        # Common cases
        # Test changing of suspended value for existing unsuspended student
        self.assertFalse(db.get_student(session,"studentmiche@example.com").suspended,"Unexpected value for 'suspended' for the entry studentmiche@example.com")
        self.assertTrue(db.suspend_student(session,"'studentmiche@example.com'"),"suspend_student did not return expected value 'True'")
        session.commit()
        self.assertTrue(db.get_student(session,"studentmiche@example.com").suspended,"'suspended' value unchanged for the entry studentmiche@example.com")
        
        # Test changing of suspended value for existing suspended student
        self.assertTrue(db.suspend_student(session,"studentmiche@example.com"),"suspend_student did not return expected value 'True'")
        session.commit()
        self.assertTrue(db.get_student(session,"studentmiche@example.com").suspended,"'suspended' value unchanged for the entry studentmiche@example.com")
        
        # Test changing of suspended value for non-existant student
        self.assertFalse(db.suspend_student(session,"teacherbob@mail.edu.sg"),"suspend_student did not return expected value 'True'")
        
    # Tests checking of active student
    def test_is_student_active(self):
        session = self.session
        # Common cases
        # Test function on existing, and non-existing, unsuspended students
        self.assertTrue(db.is_student_active(session,"student_agnes@example.com"),"Existing student falsely detected as inactive")
        self.assertFalse(db.is_student_active(session,"teacherkatherine@yahoo.com"),"Non-Existent student detected as active")
        
        # Test function on suspended students
        self.assertTrue(db.suspend_student(session,"student_agnes@example.com"),"suspend_student did not return expected value 'True'")
        session.commit()
        self.assertFalse(db.is_student_active(session,"student_agnes@example.com"),"Existing suspended student falsely detected as active")
        
        
    # Test retrieval of student mail through notification
    def test_get_student_mail_by_notification(self):
        session = self.session
        # Common cases
        # Test retrieval of student with non-referencing message
        mail_list = db.get_student_mail_by_notification(session,"teacherkatherine@yahoo.com","Hello students! Generic notification")
        for mail in ["studentjon@example.com","studenthon@example.com"]:
            self.assertTrue(mail in mail_list, "Unable to fetch student %s under teacherkatherine@yahoo.com"%(mail))
        self.assertTrue(len(mail_list)==2,"Duplicate or wrong student amongst output")
        
        # Test retrieval of student with message referencing non-existant student
        mail_list = db.get_student_mail_by_notification(session,"teacherkatherine@yahoo.com","Hello students! Generic notification @teacherbob@mail.edu.sg")
        self.assertFalse("teacherbob@mail.edu.sg" in mail_list,"Unregistered student falsely returned")
        
        # Test retrieval of student with referencing messaage
        mail_list = db.get_student_mail_by_notification(session,"teacherkatherine@yahoo.com","Hello students! @student_agnes@example.com @studentmiche@example.com @teacherbob@mail.edu.sg")
        for mail in ["studentjon@example.com","studenthon@example.com","student_agnes@example.com","studentmiche@example.com"]:
            self.assertTrue(mail in mail_list, "Unable to fetch student %s under teacherkatherine@yahoo.com"%(mail))
        self.assertTrue(len(mail_list)==4,"Duplicate or wrong student amongst output")
        
        # Test retrieval of student with referencing message who are not suspended
        self.assertTrue(db.suspend_student(session,"studentjon@example.com"),"Failed to suspend studentjon@example.com")
        self.assertTrue(db.suspend_student(session,"student_agnes@example.com"),"Failed to suspend student_agnes@example.com")
        session.commit()
        mail_list = db.get_student_mail_by_notification(session,"teacherkatherine@yahoo.com","Hello students! @student_agnes@example.com @studentmiche@example.com @teacherbob@mail.edu.sg")
        for mail in ["studenthon@example.com","studentmiche@example.com"]:
            self.assertTrue(mail in mail_list, "Unable to fetch student %s under teacherkatherine@yahoo.com after suspending non-related students"%(mail))
        for mail in ["studentjon@example.com","student_agnes@example.com"]:
            self.assertFalse(mail in mail_list, "Incorrectly fetched suspended student %s under teacherkatherine@yahoo.com"%(mail))
        self.assertTrue(len(mail_list)==2,"Duplicate or wrong student amongst output")
            
    
    # Test student registration to teacher
    def test_register_students(self):
        session = self.session
        # Common cases
        # Test registration of single students
        teacher = db.get_teacher(session,"teacherbob@mail.edu.sg")
        teacher_students_list = [student.mail for student in teacher.students]   
        self.assertFalse("'studentjon@example.com'" in teacher_students_list,"Unexpected pre-existing relationship")
        self.assertTrue(db.register_students(session,"teacherbob@mail.edu.sg",["studentjon@example.com"]),"Failed to register existing teacher")
        session.commit()
        teacher_students_list = [student.mail for student in teacher.students]        
        self.assertTrue("'studentjon@example.com'" in teacher_students_list,"Single student failed to register")
        
        # Test registration of multiple students
        self.assertFalse("'studenthon@example.com'" in teacher_students_list,"Unexpected pre-existing relationship")
        self.assertFalse("'studentmiche@example.com'" in teacher_students_list,"Unexpected pre-existing relationship")
        self.assertTrue(db.register_students(session,"'teacherbob@mail.edu.sg'",["'studenthon@example.com'","studentmiche@example.com"]),"Failed to register existing teacher")
        session.commit()
        teacher_students_list = [student.mail for student in teacher.students]        
        self.assertTrue("'studentjon@example.com'" in teacher_students_list,"Single student failed to register")
        
        # Test registration of non-existing teacher to non-existing students
        self.assertFalse(db.register_students(session,"'studenthon@example.com'",["'teacherbob@mail.edu.sg'"]),"Registered non-existant teacher")
        
        

 
 
if __name__ == "__main__":
    unittest.main()