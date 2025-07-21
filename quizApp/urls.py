from django.urls import path
from . import views

urlpatterns = [
    path("",views.index,name="index"),
    path("login",views.login_view,name="login"),
    path("logout",views.logout_view,name="logout"),
    path("register",views.register,name="register"),
    path("join",views.joinAQuiz,name="joinAQuiz"),
    path("join/<str:roomID>",views.DirectJoin,name="DirectJoin"),
    path("submit/<int:test_id>",views.submitAQuiz,name="submitAQuiz"),
    path("score/<int:testID>/<int:studentID>", views.student_score_detail, name="student_score_detail"),


    
    path("scores",views.scores,name="scores"),
    path("score/<int:testID>",views.score,name="score"),
    path("progresses",views.progresses,name="progresses"),
    path("progress/<int:testID>",views.progress,name="progress"),
    path("createQuiz", views.createQuiz, name="createQuiz"),
    path("add-questions/<int:testID>", views.add_questions_page, name="add_questions_page"),
    path("add-question/<int:testID>", views.add_question, name="add_question"),

]