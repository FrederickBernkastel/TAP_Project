"""SQL database Query and Transactions

This module handles queries and transactions to the relevant database.
The entry point to this package is the class DB, which contains the methods
required for queries and transaction with the database.
"""

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
    """
    SQL Alchemy Table object with Table structure to hold information about teachers
    """
    __tablename__ = TEACHERS_TABLE_NAME
    mail = Column(String(320), primary_key=True)
    students = relationship(
        "Student",
        secondary=registration_table,
        back_populates="teachers")
 
class Student(Base):
    """
    SQL Alchemy Table object with Table structure to hold information about students
    """
    __tablename__ = STUDENTS_TABLE_NAME
    mail = Column(String(320), primary_key=True)
    suspended = Column(Boolean,default=False)
    teachers = relationship(
        "Teacher",
        secondary=registration_table,
        back_populates="students")

class DB:
    """
    Contains methods to query and transact with the database
    """
    def __init__(self,app=None):
        """Initializes DB using application configuration
        
        Initializes DB using application configuration, such as the database URI.
        
        If no application configuration is provided, default configurations as
        specified in config.py files will be used instead.
        
        Parameters
        ----------
        app: flask.app.Flask
            Flask application class containing configuration settings
        """
        if app==None:
            from app import app
        
        URI = app.config['SQLALCHEMY_DATABASE_URI']
        self.IS_TEST = app.config['TESTING']
        
        self.engine = create_engine(URI)
        self.DBSession = sessionmaker(bind=self.engine)
         
    
        
    def create_all(self,session):
        """Creates and populates database tables with testing data
        
        Creates and populates database tables with data for testing. If the 
        current application is not configured for testing, this method will do
        nothing.
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        """
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
            
        
        
    def drop_all(self):
        """Drops relevant exisiting database tables
        
        Drops relevant database tables for testing. If the 
        current application is not configured for testing, this method will do
        nothing.
        """
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
    
    
    def format_mail(self,mail):
        """Formats provided mail address
        
        Encapsulate mail by single quotes if necessary, and returns new string,
        to ensure compatibality with database records
        
        Parameters
        ----------
        mail: string
            Email to format
        
        Returns
        -------
        string:
            Formatted Email
        """
        return "'%s'"%(mail) if len(mail)>2 and mail[0]!="'" and mail[-1]!="'" else mail
    
    
    def deformat_mail(self,mail):
        """Deformats provided mail address
        
        De-encapsulates mail by single quotes if neccessary and returns new 
        string
        
        Parameters
        ----------
        mail: string
            Email to deformat
        
        Returns
        -------
        string:
            Deformatted Email
        """
        return mail[1:-1] if len(mail)>2 and mail[0]==mail[-1]=="'" else mail
        
    def is_teacher_exist(self,session, mail):
        """Queries database for existence of teacher's email
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of teacher to query for
            
        Returns
        -------
        bool:
            True if a teacher with the provided email exists
            False otherwise
        """
        mail = self.format_mail(mail)
        teacher = session.query(Teacher).get(mail)
        return isinstance(teacher,Teacher)
    
    
    def is_student_exist(self,session, mail):
        """Queries database for existence of student's email
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of student to query for
            
        Returns
        -------
        bool:
            True if a student with the provided email exists
            False otherwise
        """
        mail = self.format_mail(mail)
        student = session.query(Student).get(mail)
        return isinstance(student,Student)
    
    
    def is_student_active(self,session,mail):
        """Queries database for existence of unsuspended student's email
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of student to query for
            
        Returns
        -------
        bool
            True if a student with the provided email exists and is unsuspended
            False otherwise
        """
        mail = self.format_mail(mail)
        if self.is_student_exist(session,mail):
            return not session.query(Student.suspended).filter_by(mail=mail).first()[0]
        return False
    
    def get_teacher(self,session,mail):
        """Queries database for teacher's information
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of teacher to query for
            
        Returns
        -------
        Teacher:
            Teacher object containing information on the teaceher with the mail
            None if no teacher with the mail exists
        """
        mail = self.format_mail(mail)
        return session.query(Teacher).get(mail)
    
    
    def get_student(self,session,mail):
        """Queries database for student's information
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of student to query for
            
        Returns
        -------
        Teacher:
            Student object containing information on the student with the mail
            None if no student with the mail exists
        """
        mail = self.format_mail(mail)
        return session.query(Student).get(mail)
    
    
    def get_student_mail_by_teacher(self,session, mail,isNotSuspended=False):
        """Queries database for students registered under teacher
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of teacher to query for
        isNotSuspended: bool
            Indicates if suspended students should be excluded
            
        Returns
        -------
        set:
            Set of student emails, as string, registered under the teacher
        """
        mail = self.format_mail(mail)
        query = session.query(Student.mail)
        # Removes suspended students if required
        if isNotSuspended:
            query = query.filter_by(suspended=False)
        values = query.filter(Student.teachers.any(mail=mail)).all()
        return {self.deformat_mail(tup[0]) for tup in values}
    
    
    def get_student_mail_by_teachers(self,session, mail_list):
        """Queries database for students registered under multiple teachers
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail_list: list
            List of String teacher emails to query for
            
        Returns
        -------
        set:
            Set of student emails, as string, registered under the teachers
        """
        mail_list = [self.format_mail(mail) for mail in mail_list]
        query = session.query(Student.mail)
        for mail in mail_list:
            query = query.filter(Student.teachers.any(mail=mail))
        return {self.deformat_mail(tup[0]) for tup in query.all()}
    
    
    def suspend_student(self,session,mail):
        """Updates database by suspending student
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of student to suspend
            
        Returns
        -------
        bool:
            True if transaction successful
            False otherwise
        """
        mail = self.format_mail(mail)
        if self.is_student_exist(session,mail):
            try:
                session.query(Student).filter_by(mail=mail).update({Student.suspended:True})
                return True
            except:
                return False
        return False
    
    
    def get_student_mail_by_notification(self,session,teachermail,notification):
        """Queries database for unsuspended students able to receive notification
        
        Queries database for list of unsuspended students able to receive 
        notification.
        Students are able to receive notification if they are unsuspended and
        either registered under the teacher, or have been tagged in the 
        notification with '@'
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        mail: string
            Email of teacher sending notification
        notification: string
            Contents of notification
            
        Returns
        -------
        set:
            Set of student emails, as string, able to receive notifications
        """
        # Finds referenced students
        notification_student_mails = re.findall(r'@([\S]+@[\S]+)',notification)
        # Remove non-existant and suspended Student mails
        students = {self.deformat_mail(mail) for mail in notification_student_mails if self.is_student_active(session,mail)}
        students |= self.get_student_mail_by_teacher(session,teachermail,isNotSuspended=True)
        return students
        
    # Registers provided student under teacher
    # Returns True if teacher and students exists, False otherwise
    def register_students(self,session,teachermail,studentmail_list):
        """Registers provided students under teacher
        
        Parameters
        ----------
        session: sqlalchemy.orm.session.Session
            SQLAlchemy session class for recording pending transactions with the 
            database
        teachermail: string
            Email of teacher to register students under
        studentmail_list: list
            List of student emails to register under teacher
            
        Returns
        -------
        bool:
            True if transaction successful
            False otherwise
        """
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
        try:
            session.merge(teacher)
            return True
        except:
            return False

