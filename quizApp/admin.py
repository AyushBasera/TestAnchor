from django.contrib import admin
from .models import User, Test, Question, StudentTest, StudentAnswer

admin.site.register(User)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(StudentTest)
admin.site.register(StudentAnswer)
# Register your models here.
