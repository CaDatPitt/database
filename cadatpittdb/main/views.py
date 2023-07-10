
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.http import HttpResponseRedirect
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


""" Static Pages """

def index_vw(request):
    context = {
        "title": "Home",
        "vocab": vocab,
        "datasets": Dataset.objects.all().order_by('-last_modified')[:4],
    }
    return render(request, "core/index.html", context)


def about_vw(request):
    context = {
        "title": "About",
        "vocab": vocab,
    }
    return render(request, "core/about.html", context)


def contact_vw(request):
    context = {
        "title": "Contact Us",
        "vocab": vocab,
    }
    return render(request, "core/contact.html", context)


def documentation_vw(request):
    context = {
        "title": "Documentation",
        "vocab": vocab,
    }
    return render(request, "core/documentation.html", context)


def faq_vw(request):
    context = {
        "title": "FAQs",
        "vocab": vocab,
    }
    return render(request, "core/faq.html", context)


def help_vw(request):
    context = {
        "title": "Help",
        "vocab": vocab,
    }
    return render(request, "core/help.html", context)


""" Auth Pages """

@login_required
def dashboard_vw(request):
    context = {
        "title": "About",
        "vocab": vocab,
    }
    return render(request, "auth/dashboard.html", context)


def login_vw(request):
    context = {
        "title": "Log In",
        "vocab": vocab,
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


""" Dynamic Pages """

def browse_vw(request):
    context = {
        "title": "Browse Datasets",
        "vocab": vocab,
        "datasets": Dataset.objects.all(),
        'creators': get_creators()
    }

    if request.method == 'POST':
        keywords = request.POST.get("keywords")
        title = request.POST.get("title")
        created_by = request.POST.get("created_by")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        min_num_items = request.POST.get("min_num_items")   
        max_num_items = request.POST.get("max_num_items")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        context['datasets'] = filter_datasets(context['datasets'])

    return render(request, "core/browse.html", context)


@login_required
def create_vw(request):
    context = {
        "title": "Create a Dataset",
        "vocab": vocab,
    }

    if request.method == 'POST':
        public_id = request.GET.get("id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        
        if public_id == "new":
            dataset = create_dataset(dataset=dataset, title=title, 
                                    description=description, tags=tags, 
                                    created_by=request.user, public=public)
        else:
            dataset = Dataset.objects.filter(public_id=public_id).first()
            update_dataset(dataset, title=title, description=description,
                           tags=tags,)
        
    return render(request, "core/create.html", context)


def dataset_vw(request):
    context = {
        "title": "View Dataset",
        "vocab": vocab,
    }
    if request.method == 'GET':
        dataset_id = request.GET.get('id')
        dataset = Dataset.objects.filter(public_id=dataset_id).first()
        context['dataset'] = dataset

    return render(request, "core/dataset.html", context)


@login_required
def edit_vw(request):
    context = {
        "title": "Edit Dataset",
        "vocab": vocab,
    }
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first() 
    context['dataset'] = dataset

    if request.method == 'POST':
        # public_id = request.GET.get("id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        
        
        # if public_id == "new":
        #     dataset = create_dataset(dataset=dataset, title=title, 
        #                             description=description, tags=tags, 
        #                             created_by=request.user, public=public)
        # else:
        #     dataset = Dataset.objects.filter(public_id=public_id).first()
        #     update_dataset(dataset, title=title, description=description,
        #                    tags=tags,)
        
    return render(request, "core/edit.html", context)


def item_vw(request):
    context = {
        "title": "View Item",
        "vocab": vocab,
        "user": request.user
    }
    if request.method == 'GET':
        item_id = request.GET.get('id')
        item = Item.objects.filter(item_id=item_id).first()

        if not item:
            messages.error(request, "That item does not exist!")
            return redirect("/")
            
        context['item'] = item
        context['datasets'] = get_item_datasets(item=item)

    return render(request, "core/item.html", context)


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
        context['datasets'] = get_user_datasets(user)

        return render(request, "core/profile.html", context)
    
    else:
        messages.error(request, "That user does not exist!")
        return redirect("/")


@login_required
def retrieve_vw(request):
    context = {
        "title": "Retrieve Data",
        "vocab": vocab,
        "show_results": False,
        "collections": Collection.objects.all(),
        "dataset": pd.DataFrame(),
        "rights": vocab['rights']
    }

    if request.method == 'POST':      
        if request.POST.get("filter"):
            # dataset = request.POST.get("dataset")

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
            retrieval_method = request.GET.get("retrieval_method")
            item_ids = request.POST.get("item_ids")
            csv_file = request.FILES.get('csv_file')
            collections = request.POST.getlist("collections")
            dataset = None

            # Get dataset
            if retrieval_method == 'identifiers':
                item_ids = iter(item_ids.splitlines())
                dataset, exceptions = get_dataset(item_ids=item_ids)
            elif retrieval_method == 'file':
                if not csv_file.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type.')
                else:
                    try:
                        df = pd.read_csv(csv_file)
                        item_ids = df.iloc[:, 0].values.tolist()
                        dataset, exceptions = get_dataset(item_ids=item_ids)

                        if exceptions:
                            # Do something with them
                            messages.error(request, "Values in the first column\
                                            of the input file were not found in\
                                            the database. Click here to view a \
                                           list of the values.")
                    except:
                        # No error is being return when no results are returned
                        messages.error(request, f'The file could not be \
                                        uploaded. Please try again.')
            elif retrieval_method == 'collections':
                dataset, exceptions = get_dataset(collections=collections)
            else:
                messages.error(request, "You must either paste a list of \
                                item identifiers (each on a separate line) \
                                or upload a CSV file with a list of item \
                                identifiers.")
                
            if not dataset.empty:
                # Add dataset to context
                context['dataset'] = dataset
                context['num_results'] = dataset.shape[0]

                # Toggle to display results
                context['show_results'] = True

    return render(request, "core/retrieve.html", context)


""" Action Views """

def add_item_vw(request):
    item_id = request.GET.get('item')
    item = Item.objects.filter(item_id=item_id).first()

    try:
        dataset_id = request.GET.get('dataset')
    except:
        dataset_id = request.POST.get('dataset')

    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if dataset:
        if not item:
            item = create_item(item_id=item_id, title=None, creator=None,
                               date=None, item_type=None, thumbnail=None,
                               collection_ids=None)
            if item:
                add_item(dataset=dataset, item=item)
            else:
                messages.error(request, "Item could not be added. Please try again.")
    else:
        messages.error(request, "That dataset does not exist!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def copy_vw(request):
    user = request.user
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if not dataset:
        messages.error(request, "That dataset does not exist!")

    new_dataset = copy_dataset(user=user, dataset=dataset)

    if new_dataset:
        context = {
            "title": "Edit Dataset",
            "vocab": vocab,
            "dataset": dataset 
        }

        return redirect(f"/edit/?id={ new_dataset.public_id }")
    else:
        messages.error(request, "The dataset could not be copied. \
                       Please try again or contact us to report the issue.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def delete_dataset_vw(request):
    dataset_id = request.GET.get('id')
    print(dataset_id)
    dataset = Dataset.objects.filter(public_id=dataset_id).first()  

    if dataset:
        delete_dataset(dataset)
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return redirect("/dashboard/")


def download_vw(request):
    context = {
        "title": "Download Dataset",
        "vocab": vocab,
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


def pin_dataset_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()
    user = request.user

    if dataset:
        pin_dataset(user=user, dataset=dataset)
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def pin_item_vw(request):
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()
    user = request.user

    if item:
        pin_item(user=user, item=item)
    else:
        messages.error(request, "That item does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    

def remove_item_vw(request):
    item_id = request.GET.get('item')
    dataset_id = request.GET.get('dataset')
    item = Item.objects.filter(item_id=item_id).first()  
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    remove_item(dataset=dataset, item=item)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def tag_item_vw(request):
    tags = request.POST.get("tags")
    user_id = request.GET.get('user')
    user = User.objects.filter(user_id=user_id).first()
    item_id = request.GET.get('item')
    item = Item.objects.filter(item_id=item_id).first()

    if item:
        add_tags(user=user, tags=tags, dataset=None, item=item)
    else:
        messages.error(request, "That item does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def unpin_dataset_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()
    user = request.user

    if dataset:
        unpin_dataset(user=user, dataset=dataset)
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def unpin_item_vw(request):
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()
    user = request.user

    if item:
        pin_item(user=user, item=item)
    else:
        messages.error(request, "That item does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
