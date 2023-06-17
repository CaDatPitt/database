from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index_vw),
    path("about/", views.about_vw),
    path("browse/", views.browse_vw),
    path("contact/", views.contact_vw),
    path("create/", views.create_vw),
    path("dashboard/", views.dashboard_vw),
    path("documentation/", views.documentation_vw),
    path("help/", views.help_vw),
    path("login/", views.login_vw),
    path("login/", views.logout_vw),
    path("retrieve/", views.retrieve_vw),
    path("signup/", views.signup_vw),
    path("about/", views.about_vw),
]
