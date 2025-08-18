from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Used to distinguish between Teacher and Student.
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    USER_TYPES = (
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)

    groups = models.ManyToManyField(
        Group,
        related_name='quizapp_user_set',  # Avoid conflict with default User
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='quizapp_user_permissions',  # Avoid conflict
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )



import string, random

def generate_unique_room_id():
    from .models import Test
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Example: "A9C2XZ"
        if not Test.objects.filter(room_id=room_id).exists():
            return room_id

# Represents a test created by a teacher.
class Test(models.Model):
    teacher = models.ForeignKey(User,on_delete=models.CASCADE,limit_choices_to={'role':'Teacher'})
    title = models.CharField(max_length=100)
    room_id = models.CharField(max_length=20,unique=True,blank=True)
    allowed_students = models.ManyToManyField(User,related_name="assigned_tests",blank=True)
    start_time=models.DateTimeField()
    duration_minutes=models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_id:
            self.room_id = generate_unique_room_id()
        super().save(*args, **kwargs)


    def end_time(self):
        from django.utils import timezone
        return self.start_time + timezone.timedelta(minutes=self.duration_minutes)
    
    def __str__(self):
        return f"{self.title} ({self.room_id})"
    
    def serialize(self):
        return {
            "id":self.id,
            "teacher": {
            "id": self.teacher.id,
            "username": self.teacher.username,
            "email": self.teacher.email,
            "name": self.teacher.get_full_name()
            },
            "room_id":self.room_id,
            "title": self.title,
            "start_time": self.start_time,
            "duration_minutes": self.duration_minutes,
            "total_allowed_students":self.allowed_students.count(),
            "total_students_appeared":StudentTest.objects.filter(test=self).count()
        }

# Linked to a Test. Stores one question and its options. 
class Question(models.Model):
    test = models.ForeignKey(Test,on_delete=models.CASCADE,related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.question_text[:50]}...."
    def serialize(self):
        return {
            "question_text":self.question_text,
            "option_a":self.option_a,
            "option_b":self.option_b,
            "option_c":self.option_c,
            "option_d":self.option_d,
            "correct_option":self.correct_option
        }

# Tracks which student attempted which test and their final score.   
class StudentTest(models.Model):
    student = models.ForeignKey(User,on_delete=models.CASCADE,limit_choices_to={'role':'student'})
    test = models.ForeignKey(Test,on_delete=models.CASCADE)
    score = models.IntegerField()
    rank = models.IntegerField(null=True,blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student','test')
    
    def __str__(self):
        return f"{self.student.username} - {self.test.title} - {self.score}"
    
    def serialize(self):
        all_students_of_test=StudentTest.objects.filter(test=self.test).order_by("-score","submitted_at")
        rank=1
        for student_test in all_students_of_test:
            if student_test.student == self.student:
                break
            rank+=1
        
        return {
            "id1":self.student.id,
            "id":self.test.id,
            "student":{
            "id": self.student.id,
            "username": self.student.username,
            "email": self.student.email,
            "name": self.student.get_full_name()
            },
            "test":self.test.title,
            "score":self.score,
            "total":self.test.questions.count(),
            "rank": rank,
            "submitted_at": self.submitted_at
        }
    

# Stores individual question-wise answers from a student.
class StudentAnswer(models.Model):
    student_test = models.ForeignKey(StudentTest, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], null=True)

    def is_correct(self):
        return self.selected_option == self.question.correct_option

