from django.urls import path
from .views import (
    admin_dashboard, dashboard, history, home, new_prediction, prediction_delete,
    profile, result, user_add, user_delete, user_detail, user_edit, user_list,
    user_set_password,
)

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("predict/", new_prediction, name="predict"),
    path("result/<int:pk>/", result, name="result"),
    path("history/", history, name="history"),
    path("profile/", profile, name="profile"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),

    # In-app user management (staff only)
    path("admin-dashboard/users/", user_list, name="user_list"),
    path("admin-dashboard/users/add/", user_add, name="user_add"),
    path("admin-dashboard/users/<int:pk>/", user_detail, name="user_detail"),
    path("admin-dashboard/users/<int:pk>/edit/", user_edit, name="user_edit"),
    path("admin-dashboard/users/<int:pk>/password/", user_set_password, name="user_set_password"),
    path("admin-dashboard/users/<int:pk>/delete/", user_delete, name="user_delete"),
    path("admin-dashboard/predictions/<int:pk>/delete/", prediction_delete, name="prediction_delete"),
]
