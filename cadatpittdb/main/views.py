
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from wsgiref.util import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
import mimetypes
from .controlled_vocab import vocab
from .utilities import *
from .datasets import *

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

    if request.method == 'POST':
        dataset = request.POST.get("dataset")
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")

        dataset = create_dataset(dataset=dataset, title=title, 
                                 description=description, tags=tags, 
                                 created_by=request.user, public=public)
        
        return redirect(f"/dataset/?id={dataset.public_id}") 
        
    return render(request, "core/create.html", context)


@login_required
def dashboard_vw(request):
    context = {
        "title": "About",
    }
    return render(request, "auth/dashboard.html", context)


def dataset_vw(request):
    context = {
        "title": "View Dataset",
    }
    if request.method == 'GET':
        id = request.GET['id']
        dataset = Dataset.objects.filter(dataset_id=id).first()
        context['dataset'] = dataset

    return render(request, "core/dataset.html", context)


def documentation_vw(request):
    context = {
        "title": "Documentation",
    }
    return render(request, "core/documentation.html", context)


def download_vw(request):
    context = {
        "title": "Download Dataset",
    }
    newfile = NamedTemporaryFile(suffix='.txt') # change suffix depending on option
    # save your data to newfile.name
    wrapper = FileWrapper(newfile)
    content_type = mimetypes.guess_type(newfile.file.name)
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(newfile.name)
    response['Content-Length'] = os.path.getsize(newfile.name)
    context['file'] = response
    return render(request, "core/download.html", context, response)


def faq_vw(request):
    context = {
        "title": "FAQs",
    }
    return render(request, "core/faq.html", context)


def help_vw(request):
    context = {
        "title": "Help",
    }
    return render(request, "core/help.html", context)


def item_vw(request):
    context = {
        "title": "View Item",
    }
    if request.method == 'GET':
        id = request.GET['id']
        item = Item.objects.filter(item_id=id).first()
        context['item'] = item

    return render(request, "core/item.html", context)


def login_vw(request):
    context = {
        "title": "Log In",
        'use_email': False
    }
    
    if request.user.is_authenticated:
        messages.error(request, "You're already logged in!")
        return redirect("/dashboard/") 
    
    if request.GET.get('email'):
        context['use_email'] = True
    
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        user = None

        # Get user's username if using email
        if context['use_email']:
            User = get_user_model()
            user = User.objects.filter(email=email).first()
            username = user.username

        # Try to authenticate user    
        user = authenticate(request, username=username, password=password)
       
        if user is not None:
            # Log in user
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
        "show_results": False,
        "collection": None,
        "dataset": None,
    }

    if request.method == 'GET':
        context['collections'] = get_collections()

    if request.method == 'POST':
        # Toggle to display results
        context['show_results'] = True
        
        if request.POST.get("filter"):
            dataset = request.POST.get("dataset")

            # Get parameters from form input
            # request, dataset=pd.DataFrame, keywords=str, title=str, 
            keywords = request.POST.get("keywords")
            title = request.POST.get("title")
            creator = request.POST.get("creator")
            contributor = request.POST.get("contributor")
            publisher = request.POST.get("publisher")
            depositor = request.POST.get("depositor")
            start_year = request.POST.get("start_year") # type="number" min="1900" max="2099" step="1" value="2016"
            end_year = request.POST.get("end_year")
            language = request.POST.get("language")
            description = request.POST.get("description")
            item_type = request.POST.getlist("item_type")
            subject = request.POST.get("subject")
            coverage = request.POST.get("coverage")
            copyright = request.POST.getlist("copyright")

            dataset = filter_dataset(keywords=keywords, title=title, 
                                     creator=creator, contributor=contributor,
                                     publisher=publisher, depositor=depositor,
                                     start_year=start_year, end_year=end_year, 
                                     language=language, description=description,
                                     item_type=item_type, subject=subject, 
                                     coverage=coverage, copyright=copyright)
        else:
            # Get form input
            retrieval_method = request.POST.get("retrieval_method")
            item_ids = request.POST.getlist("item_id")
            csv_file = request.FILES.get('csv_file')
            collections = request.POST.getlist("collection")

            # Get dataset
            if retrieval_method == 'by_id':
                if item_ids:
                    item_ids = iter(item_ids.splitlines())
                    dataset = get_dataset(item_ids=item_ids)
                elif csv_file:
                    if not csv_file.name.endswith('.csv'):
                        messages.error(request,'File is not CSV type.')
                        return redirect("/retrieve/") 
                    else:
                        try:
                            df = pd.read_csv(csv_file)
                            item_ids = df.iloc[:, 0].values.tolist()
                            dataset = get_dataset(item_ids=item_ids)
                        except:
                            messages.error(request, f'The file could not be \
                                           uploaded. Please try again.')
                else:
                    messages.error(request, "You must either paste a list of \
                                   item identifiers (each on a separate line) \
                                   or upload a CSV file with a list of item \
                                   identifiers.")
                dataset = get_dataset(item_ids=item_ids)
            else:
                dataset = get_dataset(collections=collections)

        # Add dataset to context
        context['dataset'] = dataset

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
