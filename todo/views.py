from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
# FLAW 5 FIX:
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from .models import Task


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
            return render(request, "todo/register.html")

        # FLAW 5 (A07 Identification and Authentication Failures):
        # Passwords have no restrictions and no validation so very weak passwords are allowed.
        # FIX: Use Django password validators. Imports are added at the top of the file.
        #
        # try:
        #     validate_password(password, User(username=username))
        # except ValidationError as error:
        #     for message in error.messages:
        #         messages.error(request, message)
        #     return render(request, "todo/register.html")

        # FLAW 2 (A02 Cryptographic Failures):
        # Passwords are hashed with unsalted MD5 which gives the same hash for identical passwords.
        # FIX: Apply the change in settings.py to PASSWORD_HASHERS so passwords are hashed with
        # django's default PBKDF2 algorithm.
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect("todo:task_list")

    return render(request, "todo/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect("todo:task_list")
        messages.error(request, "Wrong username or password")

    return render(request, "todo/login.html")


def logout_view(request):
    logout(request)
    return redirect("todo:login")


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    return render(request, "todo/task_list.html", {"tasks": tasks})


@login_required
def task_create(request):
    if request.method == "POST":
        Task.objects.create(user=request.user, title=request.POST.get("title"))
        return redirect("todo:task_list")
    return render(request, "todo/task_create.html", {"task": None})


@login_required
def task_edit(request, task_id):
    # FLAW 1 (A01 Broken Access Control):
    # The currently logged-in user can edit other user's tasks by changing the id 
    # in the URL because there is no ownership check when fetching the task.
    task = get_object_or_404(Task, id=task_id)
    # FIX: Add an ownership check so the task can be edited only if it belongs
    # to the currently logged-in user and returns 404 otherwise.
    # task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == "POST":
        task.title = request.POST.get("title")
        task.save()
        return redirect("todo:task_list")
    return render(request, "todo/task_edit.html", {"task": task})


@login_required
def task_delete(request, task_id):
    # FLAW 1 (A01 Broken Access Control):
    # The currently logged-in user can delete other user's tasks by changing the id
    # in the URL because there is no ownership check when fetching the task.
    task = get_object_or_404(Task, id=task_id)
    # FIX: Add an ownership check so the task can be deleted only if it belongs
    # to the currently logged-in user and returns 404 otherwise.
    # task = get_object_or_404(Task, id=task_id, user=request.user)

    task.delete()
    return redirect("todo:task_list")


@login_required
def task_search(request):
    query = request.GET.get("query", "")

    # FLAW 3 (A03 Injection):
    # The query text is added to the end of the raw SQL query so the query can be changed with an injection.
    # For example writing this: x' OR '1'='1' will show every user's tasks.
    with connection.cursor() as cursor:
        sql = "SELECT id, title FROM todo_task WHERE user_id = %s AND title LIKE '%%%s%%'" % (request.user.id, query)
        cursor.execute(sql)
        results = cursor.fetchall()
    # FIX: Do the search with django's ORM which prevents the SQL injection.
    # results = Task.objects.filter(user=request.user, title__icontains=query).values_list("id", "title")
    return render(request, "todo/task_list.html", {"tasks": None, "results": results, "query": query})

