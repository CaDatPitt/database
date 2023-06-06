from django.shortcuts import render


def index(request):
    context = {
        "title": "Home",
    }
    return render(request, "index.html", context)


def about(request):
    context = {
        "title": "About",
    }
    return render(request, "about.html", context)


def browse(request):
    context = {
        "title": "Browse Collections",
    }
    return render(request, "browse.html", context)


def create(request):
    context = {
        "title": "Create a Collection",
    }
    return render(request, "create.html", context)


def dashboard(request):
    context = {
        "title": "About",
    }
    return render(request, "dashboard.html", context)


def documentation(request):
    context = {
        "title": "Documentation",
    }
    return render(request, "documentation.html", context)


def help(request):
    context = {
        "title": "Help",
    }
    return render(request, "help.html", context)


def login(request):
    context = {
        "title": "Log In",
    }
    return render(request, "login.html", context)


def search(request):
    context = {
        "title": "Search",
    }
    return render(request, "search.html", context)


def signup(request):
    context = {
        "title": "Sign Up",
    }
    return render(request, "signup.html", context)
