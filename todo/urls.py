from django.urls import path

from . import views

app_name = "todo"
urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("add/", views.task_create, name="task_create"),
    path("search/", views.task_search, name="task_search"),
    path("<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("<int:task_id>/delete/", views.task_delete, name="task_delete"),
]