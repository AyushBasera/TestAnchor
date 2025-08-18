from django.shortcuts import render,HttpResponse,HttpResponseRedirect,get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate,login,logout,get_user_model
from .models import User,Test,StudentTest,StudentAnswer,Question
from django.utils import timezone
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "quizApp/login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "quizApp/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def register(request):
    if request.method == "POST":

        # Ensure password matches confirmation

        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        user_type = request.POST.get("user_type")
        if password != confirmation:
            return render(request, "quizApp/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )
            user.save()
        except IntegrityError:
            return render(request, "quizApp/register.html", {
                "message": "Email address already taken."
            })

        login(request,user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "quizApp/register.html")
    

def index(request):

    if request.user.is_authenticated and request.user.user_type=="Teacher": 
        return render(request, "quizApp/index.html",{
            "students":User.objects.filter(user_type="Student")
        })
    if request.user.is_authenticated:
        return render(request,"quizApp/index.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))
    
@csrf_exempt
def joinAQuiz(request):
    if request.method == "POST":
        roomID = request.POST["roomID"]
        return HttpResponseRedirect(reverse("DirectJoin", kwargs={"roomID": roomID}))
    if request.user.user_type=="Student":
        return render(request, 'quizApp/index.html')
    return render(request,'quizApp/index.html',{
        "students":User.objects.filter(user_type="Student"),
        "join_error": "Only students can join quizzes."
    })


@csrf_exempt
def DirectJoin(request, roomID):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if request.user.user_type != "Student":
        return render(request, 'quizApp/index.html', {
            "students":User.objects.filter(user_type="Student"),
            "join_error": "Only students can join quizzes."
        })

    try:
        test = Test.objects.get(room_id=roomID)
    except Test.DoesNotExist:
        return render(request, 'quizApp/index.html', {
            "join_error": "No quiz found with that Room ID."
        })
    if test.allowed_students.exists() and request.user not in test.allowed_students.all():
        return render(request, 'quizApp/index.html', {
            "join_error": "You are not allowed to join this quiz."
        })


    if test.questions.count() == 0:
        return render(request, 'quizApp/index.html', {
            "join_error": "This quiz has no questions yet."
        })

    now = timezone.now()
    start = test.start_time
    end = test.start_time + timezone.timedelta(minutes=test.duration_minutes)

    if not (start <= now < end):
        return render(request, 'quizApp/index.html', {
            "join_error": "The quiz is not active right now."
        })

    remaining_seconds = int((end - now).total_seconds())

    return render(request, 'quizApp/quiz.html', {
        "test": test,
        "questions": test.questions.all(),
        "remaining_seconds": remaining_seconds
    })


    

def submitAQuiz(request,test_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            if request.user.user_type=='Student':
                test=get_object_or_404(Test,pk=test_id)

                # check if already submitted
                if StudentTest.objects.filter(student=request.user,test=test).exists():
                    return JsonResponse({"error":"Test already submitted."}, status=400)
                
                # create StudentTest
                student_test = StudentTest.objects.create(
                    student=request.user,
                    test=test,
                    score = 0 
                )
                total_score=0
                for question in test.questions.all():
                    selected_option=request.POST.get(f'q{question.id}')
                    StudentAnswer.objects.create(
                        student_test=student_test,
                        question=question,
                        selected_option=selected_option
                    )
                    if selected_option == question.correct_option:
                        total_score+=1
                
                # save score
                student_test.score=total_score
                student_test.save()
                return render(request, 'quizApp/score.html', {
                    "score": total_score,
                    "total": test.questions.count(),
                    "test": test
                })

            else:
                return JsonResponse({"error": "User should be a Student."}, status=400)
        else:
            return HttpResponseRedirect('login')
    else:
        return JsonResponse({"error": "POST request required."}, status=400)

User = get_user_model()

def student_score_detail(request, testID, studentID):
    if not request.user.is_authenticated or request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    test = get_object_or_404(Test, pk=testID)

    # Check that this test belongs to the current teacher
    if test.teacher != request.user:
        return JsonResponse({'error': 'Forbidden: You do not own this test.'}, status=403)

    student = get_object_or_404(User, pk=studentID)
    student_test = get_object_or_404(StudentTest, student=student, test=test)

    return render(request, 'quizApp/score.html', {
        "score": student_test.score,
        "total": test.questions.count(),
        "test": test.serialize()
    })

def scores(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.user.user_type != 'Student':
        return JsonResponse({'error': 'Only students can access this view.'}, status=403)

    if request.method == 'GET':
        quizes = StudentTest.objects.filter(student=request.user).order_by("-submitted_at")
        return JsonResponse([quiz.serialize() for quiz in quizes], safe=False)

    return JsonResponse({'error': 'GET request required.'}, status=400)


def score(request, testID):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.user.user_type != 'Student':
        return JsonResponse({'error': 'Only students can access this view.'}, status=403)

    if request.method == 'GET':
        test = get_object_or_404(Test, pk=testID)
        try:
            student_test = StudentTest.objects.get(student=request.user, test=test)
        except StudentTest.DoesNotExist:
            return JsonResponse({'error': 'No submission found for this test.'}, status=404)

        score = student_test.score
        total = test.questions.count()

        return render(request, 'quizApp/score.html', {
            "score": score,
            "total": total,
            "test": test.serialize(),
            "questions":[
                {
                    **question.serialize(),
                    # 'next' will give us the first occurence otherwise NULL
                    "selected_option":next(
                        (answer.selected_option 
                         for answer in student_test.answers.all() 
                         if answer.question_id == question.id),
                         # answer is a StudentAnswer object
                         # answer.question is a foreign key to Question object
                         # answer.question_id is a django shortcut for id of that Question object
                        None
                    )
                }
                for question in test.questions.all()
            ]
        })

    return JsonResponse({'error': 'GET request required.'}, status=400)


def progresses(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Only teachers can access this view.'}, status=403)

    if request.method == 'GET':
        tests = Test.objects.filter(teacher=request.user).order_by('-created_at')
        return JsonResponse([test.serialize() for test in tests], safe=False)

    return JsonResponse({'error': 'GET request required.'}, status=400)


def progress(request, testID):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Only teachers can access this view.'}, status=403)

    if request.method == 'GET':
        test = get_object_or_404(Test, pk=testID)

        # Ensure the test belongs to the teacher
        if test.teacher != request.user:
            return JsonResponse({'error': 'You are not the creator of this test.'}, status=403)

        students = StudentTest.objects.filter(test=test).order_by('-score', 'submitted_at')
        return JsonResponse([student.serialize() for student in students], safe=False)

    return JsonResponse({'error': 'GET request required.'}, status=400)




@csrf_exempt
def createQuiz(request):
    if not request.user.is_authenticated or request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == "POST":
        title = request.POST.get("title")
        start_time = request.POST.get("start_time")
        duration = request.POST.get("duration_minutes")
        allowed_student_ids = request.POST.getlist("allowed_students[]")  # <- Important

        if not all([title, start_time, duration]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        try:
            start_dt = timezone.datetime.fromisoformat(start_time)
            start_dt = timezone.make_aware(start_dt)
        except:
            return JsonResponse({'error': 'Invalid date format.'}, status=400)

        try:
            test = Test.objects.create(
                teacher=request.user,
                title=title,
                start_time=start_dt,
                duration_minutes=int(duration)
            )

            if allowed_student_ids:
                test.allowed_students.set(allowed_student_ids)

            return JsonResponse({'success': True, 'test_id': test.id})
        except IntegrityError:
            return JsonResponse({'error': 'Room ID must be unique'}, status=400)

    return JsonResponse({'error': 'POST method required'}, status=405)




def add_questions_page(request, testID):
    if not request.user.is_authenticated or request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    test = get_object_or_404(Test, pk=testID)

    if test.teacher != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    return render(request, "quizApp/add_questions.html", {
        "test": test
    })


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def add_question(request, testID):
    if not request.user.is_authenticated or request.user.user_type != 'Teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == "POST":
        test = get_object_or_404(Test, pk=testID)

        if test.teacher != request.user:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        question_text = request.POST.get("question_text")
        option_a = request.POST.get("option_a")
        option_b = request.POST.get("option_b")
        option_c = request.POST.get("option_c")
        option_d = request.POST.get("option_d")
        correct_option = request.POST.get("correct_option")

        if not all([question_text, option_a, option_b, option_c, option_d, correct_option]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        q = Question.objects.create(
            test=test,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option
        )

        return JsonResponse({'success': True, 'question': question_text})
    
    return JsonResponse({'error': 'POST method required'}, status=405)
