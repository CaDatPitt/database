
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from wsgiref.util import FileWrapper
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
import mimetypes
from .auth import *
from .controlled_vocab import vocab
from .utilities import *
from .datasets import *


""" Static Pages """

def index_vw(request):
    if request.method == "GET":
        context = {
            "title": "Home",
            "vocab": vocab,
            "datasets": Dataset.objects.filter(public=True).all().order_by('-last_modified')[:4],
        }
        return render(request, "core/index.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


def about_vw(request):
    if request.method == "GET":
        context = {
            "title": "About",
            "vocab": vocab,
        }
        return render(request, "core/about.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


def contact_vw(request):
    if request.method == "GET":
        context = {
            "title": "Contact Us",
            "vocab": vocab,
        }
        return render(request, "core/contact.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


def documentation_vw(request):
    if request.method == "GET":
        context = {
            "title": "Documentation",
            "vocab": vocab,
        }
        return render(request, "core/documentation.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


def faq_vw(request):
    if request.method == "GET":
        context = {
            "title": "FAQs",
            "vocab": vocab,
        }
        return render(request, "core/faq.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


def help_vw(request):
    if request.method == "GET":
        context = {
            "title": "Help",
            "vocab": vocab,
        }
        return render(request, "core/help.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])
    

def search_vw(request):
    context = {
        "title": "Search",
        "vocab": vocab,
    }
    return render(request, "core/search.html", context)



""" Auth Pages """

@login_required
def dashboard_vw(request):
    if request.method == "GET":
        context = {
            "title": "Dashboard",
            "vocab": vocab,
        }
        return render(request, "auth/dashboard.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


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
    
    if request.method == "POST":
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

    User = get_user_model()
    username = request.GET.get('user')

    user = User.objects.get(username=username)
    if not user:
        messages.error(request, "That user does not exist!")
        return redirect("/")
        
    if request.method == "POST":
        pronouns = request.POST.get('pronouns')
        title = request.POST.get('title')
        affiliation = request.POST.getlist('affiliation')
        other_affiliation = request.POST.get('other_affiliation')
        website = request.POST.get('website')
        bio = request.POST.get('bio')
        photo_url = request.POST.get('photo_url')

        # Update profile data
        updated = update_profile(user=request.user, pronouns=pronouns, 
                                 title=title, affiliation=affiliation, 
                                 other_affiliation=other_affiliation,
                                 website=website, bio=bio, photo_url=photo_url)

        if not updated:
            messages.error(request, "Your profile could not be updated. Please \
                           try again or contact us to report the issue.")
            
    # Get formatted user affiliaitions
    affiliations, other_affiliations = user.get_affiliations()
    bio = get_markdown(user.bio)

    # Add user information to context
    context['person'] = user
    context['affiliations'] = affiliations
    context['other_affiliations'] = other_affiliations
    context['bio'] = bio
    context['datasets'] = get_user_datasets(user)
    
    return render(request, "auth/profile.html", context)


def signup_vw(request):
    context = {
        "title": "Sign Up",
        "vocab": vocab,
    }

    if request.user.is_authenticated:
        messages.error(request, "You are already registered!")
        return redirect("/dashboard/") 

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        pronouns = request.POST.get('pronouns')
        title = request.POST.get('title')
        affiliation = request.POST.getlist('affiliation')
        other_affiliation = request.POST.get('other_affiliation')
        website = request.POST.get('website')
        bio = request.POST.get('bio')
        photo_url = request.POST.get('photo_url')
        password = request.POST.get('password')
        password_conf = request.POST.get('password_conf')

        # Validate password
        password_valid = check_password(request, password, password_conf)

        # Check if user already exists
        User = get_user_model()
        user_exists = check_user_exists(request, User, username, email)
        user = None

        if not user_exists and password_valid:
            # Format affiliations
            affiliation = format_affiliation(affiliation, other_affiliation)

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
                               again or contact us to report the issue.")
                
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Account created! Thanks for joining!")
                return redirect("/dashboard/")
        
        if user_exists or user is None or not password_valid:
            context['form'] = {'first_name': first_name, 'last_name': last_name,
                               'username': username, 'email': email, 
                               'pronouns': pronouns, 'title': title, 
                               'affiliations': affiliation, 
                               'other_affiliation': other_affiliation,
                               'website': website, 'bio': bio, 
                               'photo_url': photo_url, 'password': password}            
        
    return render(request, "auth/signup.html", context)


@login_required
def update_account(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password_conf = request.POST['password_conf']

        # Validate password
        password_valid = check_password(request, password, password_conf)

        if password_valid:
            # Update account information
            updated = update_account(user=request.user, first_name=first_name, 
                                  last_name=last_name, username=username, 
                                  email=email, password=password)
            
            # Check if account was updated and flash appropriate message
            if updated:
                messages.success(request, "Account updated successfully!")
            else:
                messages.error(request, "Account could not be updated. Please \
                               try again or contact us to report the issue.")
            
            return redirect("/dashboard/")

    else:
        return HttpResponseNotAllowed(["GET"])


""" Dynamic Pages """

def browse_vw(request):
    context = {
        "title": "Browse Datasets",
        "vocab": vocab,
        "datasets": Dataset.objects.filter(public=True).all(),
        'creators': get_creators()
    }

    if request.method == "POST":
        keywords = request.POST.get("keywords")
        title = request.POST.get("title")
        creator = request.POST.get("creator")
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
    if request.method == "POST":
        # Get data from form
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        if public == "on":
            public = True
        else:
            public = False

        # Get data from session
        dataset = request.session.get('dataset')
        filters = request.session.get('filters')
        
        if not dataset:
            messages.error(request, "No dataset was given. You must first \
                           retrieve data before attempting to create a dataset.")
        if not filters:
            filters = {}

        # Create dataset
        new_dataset = create_dataset(dataset=dataset, title=title, 
                                     description=description, tags=tags, 
                                     filters=filters, creator=request.user, 
                                     public=public)
        
        if new_dataset:
            # Remove session variables
            del request.session['dataset']
            if filters:
                del request.session['filters']
            request.session.modified = True

            return redirect(f"/dataset/?id={ new_dataset.public_id }")
        else:
            # Send request again using info about dataset?
            messages.error(request, "Dataset could not be created. Please try \
                               again or contact us to report the issue.")
            return redirect("/retrieve/")
        


def dataset_vw(request):
    context = {
        "title": "View Dataset",
        "vocab": vocab,
    }

    if request.method == "GET":
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

    if not dataset:
        messages.error(request, "That dataset does not exist!")
        return redirect("/browse/")
 
    context['dataset'] = dataset

    if request.method == "POST": 
        # Verify user can modify dataset
        if not verify_user(request, dataset.creator):
            messages.error(request, 'You do not have permission to directly edit \
                           this dataset. Click the "Edit Dataset" button to \
                           edit a copy of this dataset.')
            return redirect(f"/dataset/?id={ dataset_id }")
        
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        if public == "on":
            public = True
        else:
            public = False
        
        # Update dataset
        updated = update_dataset(user=request.user, dataset=dataset, title=title, 
                                 description=description, tags=tags, public=public)
        
        if not updated:
            messages.error(request, "Dataset could not be updated. Please try \
                           again or contact us to report the issue.")
        
    return render(request, "core/edit.html", context)


def item_vw(request):
    context = {
        "title": "View Item",
        "vocab": vocab
    }
    if request.method == "GET":
        item_id = request.GET.get('id')
        item = Item.objects.filter(item_id=item_id).first()

        if not item:
            messages.error(request, "That item does not exist!")
            return redirect("/")
            
        context['item'] = item
        context['datasets'] = get_item_datasets(item=item)

    return render(request, "core/item.html", context)


@login_required
def retrieve_vw(request):
    context = {
        "title": "Retrieve Data",
        "vocab": vocab,
        "show_results": False,
        "collections": Collection.objects.all(),
        "rights": vocab['rights']
    }

    if request.method == "POST":      
        if request.POST.get("filter"):
            # Get filters from form
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

            # Filter dataset
            dataset, dataset_df = filter_dataset(keywords=keywords, title=title, 
                                     creator=creator, contributor=contributor,
                                     publisher=publisher, depositor=depositor,
                                     start_year=start_year, end_year=end_year, 
                                     language=language, description=description,
                                     item_type=item_type, subject=subject, 
                                     coverage=coverage, copyright=copyright)
            
            # Add filters to session
            request.session['filters'] = {
                'keywords': keywords, 'title': title, 'creator': creator,  
                'contributor':contributor, 'publisher': publisher, 
                'depositor': depositor,  'start_year': start_year, 
                'end_year': end_year, 'language': language, 
                'description': description, 'item_type': item_type, 
                'subject': subject, 'coverage': coverage, 'copyright': copyright
            }

        else:
            # Get retrieval method from form
            retrieval_method = request.GET.get("retrieval_method")
            item_ids = request.POST.get("item_ids")
            csv_file = request.FILES.get('csv_file')
            collections = request.POST.getlist("collections")
            dataset = None

            # Get dataset
            if retrieval_method == 'identifiers':
                item_ids = iter(item_ids.splitlines())
                dataset, dataset_df, exceptions = get_dataset(item_ids=item_ids)
            elif retrieval_method == 'file':
                if not csv_file.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type.')
                else:
                    try:
                        df = pd.read_csv(csv_file)
                        item_ids = df.iloc[:, 0].values.tolist()
                        dataset, dataset_df, exceptions = get_dataset(item_ids=item_ids)

                        if exceptions:
                            # Do something with them
                            messages.error(request, "Values in the first column\
                                            of the input file were not found in\
                                            the database. Click here to view a \
                                           list of the values.")
                    except:
                        # No error is being return when no results are returned
                        messages.error(request, f'The file could not be \
                                       uploaded. Please try again or contact \
                                       us to report the issue.')
            elif retrieval_method == 'collections':
                dataset, dataset_df, exceptions = get_dataset(collections=collections)
            else:
                messages.error(request, "You must either paste a list of \
                                item identifiers (each on a separate line) \
                                or upload a CSV file with a list of item \
                                identifiers.")
                
            if dataset:
                # Add dataset to session and context
                request.session['dataset'] = dataset
                context['dataset'] = dataset_df

                # Add dataset info to context
                context['num_results'] = dataset_df.shape[0]

                # Toggle to display results
                context['show_results'] = True

    return render(request, "core/retrieve.html", context)


""" Action Views """

@login_required
def add_item_vw(request):
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()
    dataset_id = request.GET.get('dataset')
    dataset = None

    if dataset_id != None:
        dataset = Dataset.objects.filter(public_id=dataset_id).first()
    else:
        dataset_title = request.POST.get('dataset')
        dataset = Dataset.objects.filter(title=dataset_title).first()

    if dataset:
        if not verify_user(request, dataset.creator):
            messages.error(request, 'You do not have permission to directly edit \
                           this dataset. Click the "Edit Dataset" button to \
                           edit a copy of this dataset.')
            return redirect(f"/dataset/?id={ dataset_id }")
        
        if not item:
            item = create_item_from_id(item_id=item_id)
            if not item:
                messages.error(request, "Item could not be added. Please try \
                               again or contact us to report the issue.")
        add_item(dataset=dataset, item=item)
    else:
        messages.error(request, "That dataset does not exist!")

    return redirect(f"/item/?id={ item.item_id }")


@login_required
def copy_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()
    title = request.POST.get('title')

    if not dataset:
        messages.error(request, "That dataset does not exist!")
    
    elif title == dataset.title: # check for all names?
        messages.error(request, "You must give your copy of this dataset a unique name.")

    else:
        new_dataset = copy_dataset(user=request.user, dataset=dataset, title=title)

        if new_dataset:
            return redirect(f"/edit/?id={ new_dataset.public_id }")
        else:
            messages.error(request, "The dataset could not be copied. \
                        Please try again or contact us to report the issue.")
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_dataset_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()  

    if dataset:
        # Verify user has permission to delete dataset
        if not verify_user(request, dataset.creator):
            messages.error(request, 'You do not have permission to directly edit \
                           this dataset. Click the "Edit Dataset" button to \
                           edit a copy of this dataset.')
            return redirect(f"/dataset/?id={ dataset_id }")
        
        # Delete dataset
        deleted = delete_dataset(dataset.public_id)

        if not deleted:
            messages.error(request, "The dataset could not be deleted. \
                           Please try again or contact us to report the issue.")
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return redirect("/dashboard/")


@login_required
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


@login_required
def pin_dataset_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if dataset:

        pinned = pin_dataset(user=request.user, dataset=dataset)
        
        if not pinned:
            messages.error(request, "The dataset could not be pinned. \
                           Please try again or contact us to report the issue.")
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def pin_item_vw(request):
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()

    if not item:
        item = create_item(item_id=item_id, title=None, creator=None,
                           date=None, item_type=None, thumbnail=None,
                           collection_ids=None)
        
    pinned = pin_item(user=request.user, item=item)

    if not pinned:
        messages.error(request, "The item could not be pinned. \
                        Please try again or contact us to report the issue.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    

@login_required
def remove_item_vw(request):
    item_id = request.GET.get('item')
    item = Item.objects.filter(item_id=item_id).first() 
    dataset_id = request.GET.get('dataset') 
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if item:
        if dataset:
            if not verify_user(request, dataset.creator):
                messages.error(request, 'You do not have permission to directly \
                               edit this dataset. Click the "Edit Dataset" \
                               button to edit a copy of this dataset.')
                return redirect(f"/dataset/?id={ dataset_id }")
            
            # Remove item from dataset
            remove_item(dataset=dataset, item=item)
        else:
            messages.error(request, "That dataset does not exist!")
    else:
        messages.error(request, "That item does not exist!")

    return redirect(f"/dataset/?id={ dataset_id }")


@login_required
def tag_dataset_vw(request):
    tags = request.POST.get("tags")
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if dataset:
        add_tags(user=request.user, tags=tags, dataset=dataset, item=None)
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def tag_item_vw(request):
    tags = request.POST.get("tags")
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()

    if not item:
        item = create_item(item_id=item_id, title=None, creator=None,
                           date=None, item_type=None, thumbnail=None,
                           collection_ids=None)
        
    tagged = add_tags(user=request.user, tags=tags, dataset=None, item=item)

    if not tagged:
        messages.error(request, "The item could not be tagged. \
                       Please try again or contact us to report the issue.")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def unpin_dataset_vw(request):
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if dataset:
        unpin_dataset(user=request.user, dataset=dataset)
    else:
        messages.error(request, "That dataset does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def unpin_item_vw(request):
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()

    if item:
        unpin_item(user=request.user, item=item)
    else:
        messages.error(request, "That item does not exist!")
        return redirect("/")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
