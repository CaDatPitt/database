from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from .controlled_vocab import vocab
from .utilities import *


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
    return render(request, "auth/dashboard.html", context)


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
    return redirect("/")


@login_required
def profile_vw(request):
    context = {
        "title": "View Profile",
        "vocab": vocab,
    }
    
    username = request.GET['user']
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except:
        user = None

    if user:
        # Get formatted user affiliaitions
        affiliations = user.get_affiliations
        bio = get_markdown(user.bio)

        # Add user information to context
        context['person'] = user
        context['affiliations'] = affiliations
        context['bio'] = bio

        return render(request, "core/profile.html", context)
    
    else:
        messages.error(request, "That user does not exist!")
        return redirect("/")


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

    if request.user.is_authenticated:
        messages.error(request, "You are already registered!")
        return redirect("/dashboard/") 

    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        pronouns = request.POST['pronouns']
        title = request.POST['title']
        affiliations = request.POST.getlist('affiliations')
        other_affiliation = request.POST['other_affiliation']
        email = request.POST['email']
        website = request.POST['website']
        bio = request.POST['bio']
        photo_url = request.POST['photo_url']
        password = request.POST['password']
        password_conf = request.POST['password_conf']

        password_valid = check_password(request, password, password_conf)

        User = get_user_model()
        user_exists = check_user_exists(request, User, username, email)
        user = None

        if not user_exists and password_valid:
            affiliation = format_affiliation(affiliations, other_affiliation)
            try:
                user = User.objects.create_user(first_name=first_name,
                                                last_name=last_name,
                                                username=username, email=email, 
                                                pronouns=pronouns, title=title, 
                                                affiliation=affiliation, 
                                                website=website, bio=bio, 
                                                profile_photo_url=photo_url, 
                                                password=password)
            except:
                messages.error(request, "User could not be created. Please try \
                               or submit a help request.")
                
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Account created! Thanks for joining!")
                return redirect("/dashboard/")
        
        if user_exists or user is None or not password_valid:
            context['form'] = {'first_name': first_name, 'last_name': last_name,
                               'username': username, 'email': email, 
                               'pronouns': pronouns, 'title': title, 
                               'affiliations': affiliations, 
                               'other_affiliation': other_affiliation,
                               'website': website, 'bio': bio, 
                               'photo_url': photo_url, 'password': password}            
        
    return render(request, "auth/signup.html", context)
