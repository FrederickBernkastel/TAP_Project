import re
from sqlalchemy import Column, Table, ForeignKey, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import exc


Base = declarative_base()
TEACHERS_TABLE_NAME = 'teachers'
STUDENTS_TABLE_NAME = 'students'
REGISTRATIONS_TABLE_NAME = 'registrations'
registration_table = Table(REGISTRATIONS_TABLE_NAME, Base.metadata,
    Column('teachermail', String(320), ForeignKey('teachers.mail'),primary_key=True),
    Column('studentmail', String(320), ForeignKey('students.mail'),primary_key=True)
)

class Teacher(Base):
    __tablename__ = TEACHERS_TABLE_NAME
    mail = Column(String(320), primary_key=True)
    students = relationship(
        "Student",
        secondary=registration_table,
        back_populates="teachers")
 
class Student(Base):
    __tablename__ = STUDENTS_TABLE_NAME
    mail = Column(String(320), primary_key=True)
    suspended = Column(Boolean,default=False)
    teachers = relationship(
        "Teacher",
        secondary=registration_table,
        back_populates="students")

class DB:
    def __init__(self,app=None):
        if app==None:
            from app import app
        
        URI = app.config['SQLALCHEMY_DATABASE_URI']
        self.IS_TEST = app.config['TESTING']
        
        self.engine = create_engine(URI)
        self.DBSession = sessionmaker(bind=self.engine)
         
    
        
    # Creates entries in table for testing
    def create_all(self,session):
        if not self.IS_TEST:
            return
        
        # Database Entries
        teacher_mails = ["'teacherken@gmail.com'","'teacherkatherine@yahoo.com'","'teacherbob@mail.edu.sg'"]
        student_mails = ["'studentjon@example.com'","'studenthon@example.com'", "'student_agnes@example.com'" ,"'studentmiche@example.com'"]
        registrations = [(0,0),(1,0),(1,1)] # Each tuple contains the registration of teacher to student via (teacher index, student index)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        Base.metadata.bind = self.engine
        
        # Populate tables
        teachers = [Teacher(mail=mail) for mail in teacher_mails]
        students = [Student(mail=mail) for mail in student_mails]
        for teacher_idx, student_idx in registrations:
            teachers[teacher_idx].students.append(students[student_idx])
            
        for teacher in teachers:
            session.add(teacher)
        for student in students:
            session.add(student)
            
        
        
    # Drop entries in table for testing
    def drop_all(self):
        if not self.IS_TEST:
            return
        try:
            registration_table.drop(self.engine)
        except exc.OperationalError:
            pass
        try:
            Teacher.__table__.drop(self.engine)
        except exc.OperationalError:
            pass
        try:
            Student.__table__.drop(self.engine)
        except exc.OperationalError:
            pass
    
    # Encapsulate mail by single quotes if necessary, and returns new string
    def format_mail(self,mail):
        return "'%s'"%(mail) if len(mail)>2 and mail[0]!="'" and mail[-1]!="'" else mail
    
    # De-encapsulates mail by single quotes if neccessary and returns new string
    def deformat_mail(self,mail):
        return mail[1:-1] if len(mail)>2 and mail[0]==mail[-1]=="'" else mail
        
    # Checks database for existence of teacher by email
    def is_teacher_exist(self,session, mail):
        mail = self.format_mail(mail)
        teacher = session.query(Teacher).get(mail)
        return isinstance(teacher,Teacher)
    
    # Checks database for existence of teacher by email
    def is_student_exist(self,session, mail):
        mail = self.format_mail(mail)
        student = session.query(Student).get(mail)
        return isinstance(student,Student)
    
    # Checks database if student exists and is not suspended
    def is_student_active(self,session,mail):
        mail = self.format_mail(mail)
        if self.is_student_exist(session,mail):
            return not session.query(Student.suspended).filter_by(mail=mail).first()[0]
        return False
    
    # Returns Teacher object if in db, else None
    def get_teacher(self,session,mail):
        mail = self.format_mail(mail)
        return session.query(Teacher).get(mail)
    
    # Returns Student object if in db, else None
    def get_student(self,session,mail):
        mail = self.format_mail(mail)
        return session.query(Student).get(mail)
    
    # Returns mail of Students registered to teacher as set
    def get_student_mail_by_teacher(self,session, mail,isNotSuspended=False):
        mail = self.format_mail(mail)
        query = session.query(Student.mail)
        # Removes suspended students if required
        if isNotSuspended:
            query = query.filter_by(suspended=False)
        values = query.filter(Student.teachers.any(mail=mail)).all()
        return {self.deformat_mail(tup[0]) for tup in values}
    
    # Returns mail of Students registered to teachers as set
    def get_student_mail_by_teachers(self,session, mail_list):
        mail_list = [self.format_mail(mail) for mail in mail_list]
        query = session.query(Student.mail)
        for mail in mail_list:
            query = query.filter(Student.teachers.any(mail=mail))
        return {self.deformat_mail(tup[0]) for tup in query.all()}
    
    # Suspends a student by setting "suspended" col to True
    # Returns True if student is recorded as suspended, else False if Student not in db
    def suspend_student(self,session,mail):
        mail = self.format_mail(mail)
        if self.is_student_exist(session,mail):
            session.query(Student).filter_by(mail=mail).update({Student.suspended:True})
            return True
        return False
    
    # Returns list of students who are able to receive notifications
    def get_student_mail_by_notification(self,session,teachermail,notification):
        # Finds referenced students
        notification_student_mails = re.findall(r'@([\S]+@[\S]+)',notification)
        # Remove non-existant and suspended Student mails
        students = {self.deformat_mail(mail) for mail in notification_student_mails if self.is_student_active(session,mail)}
        students |= self.get_student_mail_by_teacher(session,teachermail,isNotSuspended=True)
        return students
        
    # Registers provided student under teacher
    # Returns True if teacher and students exists, False otherwise
    def register_students(self,session,teachermail,studentmail_list):
        teachermail = self.format_mail(teachermail)
        studentmail_list = [self.format_mail(studentmail) for studentmail in studentmail_list]
        
        # Check if teacher exists
        if not self.is_teacher_exist(session,teachermail):
            return False
        # Check if students exist
        for studentmail in studentmail_list:
            if not self.is_student_exist(session,studentmail):
                return False
        
        teacher = self.get_teacher(session,teachermail)
        
        # Add teacher-student relationship if student exists, and relationship does not yet exist
        for studentmail in studentmail_list:
            if self.is_student_exist(session,studentmail):
                student = self.get_student(session,studentmail)
                if student not in teacher.students:
                    teacher.students.append(student)
        session.merge(teacher)
        return True

