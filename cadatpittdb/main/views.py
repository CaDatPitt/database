from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .controlled_vocab import vocab


def index_vw(request):
    context = {
        "title": "Home",
    }
    return render(request, "core/index.html", context)


def about_vw(request):
    context = {
        "title": "About",
    }
    return render(request, "core/about.html", context)


def browse_vw(request):
    context = {
        "title": "Browse Datasets",
    }
    return render(request, "core/browse.html", context)


def contact_vw(request):
    context = {
        "title": "Contact Us",
        "vocab": vocab,
    }
    return render(request, "core/contact.html", context)


@login_required
def create_vw(request):
    context = {
        "title": "Create a Dataset",
    }
    return render(request, "core/create.html", context)


@login_required
def dashboard_vw(request):
    context = {
        "title": "About",
    }
    return render(request, "core/dashboard.html", context)


def documentation_vw(request):
    context = {
        "title": "Documentation",
    }
    return render(request, "core/documentation.html", context)


def help_vw(request):
    context = {
        "title": "Help",
    }
    return render(request, "core/help.html", context)


def login_vw(request):
    context = {
        "title": "Log In",
    }
    if request.user.is_authenticated:
        messages.error(request, "You're already logged in!")
        return redirect("/dashboard/") 
    
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/dashboard/")
        else:
            messages.error(request, "You entered invalid login credentials.")

    return render(request, "auth/login.html", context)


@login_required
def logout_vw(request):
    logout(request)
    return redirect("/index/")


@login_required
def retrieve_vw(request):
    context = {
        "title": "Retrieve Data",
    }
    return render(request, "core/retrieve.html", context)


def signup_vw(request):
    context = {
        "title": "Sign Up",
        "vocab": vocab,
    }
    return render(request, "auth/signup.html", context)
