
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, FileResponse
from wsgiref.util import FileWrapper
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
import xlsxwriter
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
    context = {
        "title": "Contact Us",
        "vocab": vocab,
    }

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        inquiry_type = request.POST.get('inquiry_type')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Create message
        message = Message(full_name=full_name, email=email, 
                          inquiry_type=inquiry_type, 
                          subject=subject, message=message)
        message.save()

        # Flash acknowledgement
        messages.success(request, "Thank you for contacting us! We've received\
                         your message and will respond as soon as we can.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    return render(request, "core/contact.html", context)


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
        "show_results": False,
    }

    if request.method == 'POST':
        keywords = request.POST.get("keywords").strip('"').strip("'").strip()

        if keywords:
            found, results = search(keywords)
            context['keywords'] = keywords
            context['found'] = found
            context['results'] = results
            context['show_results'] = True
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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

    # Add user information to context
    context['person'] = user
    context['affiliations'] = affiliations
    context['other_affiliations'] = other_affiliations
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
            
            # Authenticate user
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Account created! Thanks for joining!")
                return redirect("/dashboard/")
        
        # Sign up was unsuccessful
        # Save given form input and return to sign up page
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
        "collections": Collection.objects.filter(has_dataset=1).all().order_by('title'),
        'creators': get_creators(),
        "datasets": Dataset.objects.filter(public=True).all().order_by('title'),
        "tags": Tag.objects.all(),
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

        # Add dataset to context
        context['datasets'] = filter_datasets(context['datasets'])

    return render(request, "core/browse.html", context)


def collection_vw(request):
    context = {
        "title": "View Datasets by Collection",
        "vocab": vocab,
    }

    if request.method == "GET":
        id = request.GET.get('id')
        collection = Collection.objects.filter(collection_id=id).first()

        # Check if the collection doesn't exist
        if not collection:
            messages.error(request, "That collection does not exist!")
            return redirect("/")
        
        # Get datasets associated with collection
        datasets = Dataset.objects.filter(items__collections=collection).distinct()

        # Add objects to context
        context['collection'] = collection
        context['datasets'] = datasets

    return render(request, "core/collection.html", context)


@login_required
def create_vw(request):
    if request.method == "POST":
        # Get data from session
        dataset = request.session.get('dataset')
        filters = request.session.get('filters')
        
        # Get data from form
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        if public == "on":
            public = True
        else:
            public = False

        # Check if request is to save results
        saved_results = request.GET.get("saved_results")
        if saved_results:
            saved_results = True
        else:
            saved_results = False
        
        if not dataset:
            messages.error(request, "No dataset was given. You must first \
                           retrieve data before attempting to create a dataset.")
        if not filters:
            filters = {}

        # Create dataset
        new_dataset = create_dataset(dataset=dataset, title=title, 
                                     description=description, tags=tags, 
                                     filters=filters, creator=request.user, 
                                     public=public, saved_results=saved_results)
        
        # Check if dataset was created
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

        # Add dataset to context
        context['dataset'] = dataset

    return render(request, "core/dataset.html", context)


@login_required
def edit_vw(request):
    context = {
        "title": "Edit Dataset",
        "vocab": vocab,
    }

    # Get dataset from HTTP request
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    if not dataset:
        messages.error(request, "That dataset does not exist!")
        return redirect("/browse/")
    
    # Add dataset to context
    context['dataset'] = dataset

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")
        public = request.POST.get("public")
        if public == "on":
            public = True
        else:
            public = False 
        
        # Verify user can modify dataset
        if not verify_user(request, dataset.creator):
            messages.error(request, 'You do not have permission to directly edit \
                           this dataset. Click the "Edit Dataset" button to \
                           edit a copy of this dataset.')
            return redirect(f"/dataset/?id={ dataset_id }")
        
        # Update dataset
        updated = update_dataset(user=request.user, dataset=dataset, title=title, 
                                 description=description, tags=tags, public=public)
        
        # Check if dataset
        if not updated:
            messages.error(request, "Dataset could not be updated. Please try \
                           again or contact us to report the issue.")
        
    return render(request, "core/edit.html", context)


def exceptions_vw(request):
    if request.method == "GET":
        context = {
            "title": "Exceptions",
            "vocab": vocab,
        }
        return render(request, "core/exceptions.html", context)
    else:
        return HttpResponseNotAllowed(["POST"])


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
        dataset = None
        dataset_df = None

        if request.GET.get("filter"):
            dataset = request.session.get('dataset')
            keywords = request.POST.get("keywords")
            title = request.POST.get("title")
            creator = request.POST.get("creator")
            contributor = request.POST.get("contributor")
            publisher = request.POST.get("publisher")
            depositor = request.POST.get("depositor")
            start_year = request.POST.get("start_year")
            end_year = request.POST.get("end_year")
            language = request.POST.get("language")
            description = request.POST.get("description")
            item_type = request.POST.getlist("item_type")
            subject = request.POST.get("subject")
            coverage = request.POST.get("coverage")
            rights = request.POST.getlist("copyright")

            # Filter dataset
            if isinstance(dataset, list) and len(dataset) > 0:
                dataset, dataset_df = filter_dataset(request=request, 
                                                    dataset=dataset,
                                                    keywords=keywords,
                                                    title=title, 
                                                    creator=creator, 
                                                    contributor=contributor,
                                                    publisher=publisher, 
                                                    depositor=depositor,
                                                    start_year=start_year, 
                                                    end_year=end_year, 
                                                    language=language, 
                                                    description=description,
                                                    item_type=item_type, 
                                                    subject=subject, 
                                                    coverage=coverage, 
                                                    rights=rights)
            
            # Add filters to session
            request.session['filters'] = {
                'keywords': keywords, 'title': title, 'creator': creator,  
                'contributor':contributor, 'publisher': publisher, 
                'depositor': depositor,  'start_year': start_year, 
                'end_year': end_year, 'language': language, 
                'description': description, 'item_type': item_type, 
                'subject': subject, 'coverage': coverage, 'copyright': rights
            }

        else:
            # Get retrieval method from form
            retrieval_method = request.GET.get("retrieval_method")
            item_ids = request.POST.get("item_ids")
            csv_file = request.FILES.get('csv_file')
            collections = request.POST.getlist("collections")
            dataset = None

            # Get dataset
            # List of Identifiers
            if retrieval_method == 'identifiers':
                item_ids = iter(item_ids.splitlines())
                dataset, dataset_df, exceptions = get_dataset(item_ids=item_ids)

                if exceptions:
                    request.session['exceptions'] = exceptions
                    # Do something with them
                    messages.error(request, "Some items were not found in\
                                   the database. Click <a href='/exceptions/' \
                                   target='_blank'>here</a> to view a list of \
                                   item ids that were not processed.", 
                                   extra_tags='safe')
            # File Upload
            elif retrieval_method == 'file':
                if not csv_file.name.endswith('.csv'):
                    messages.error(request,'File is not CSV type.')
                else:
                    try:
                        df = pd.read_csv(csv_file)
                        item_ids = df.iloc[:, 0].values.tolist()
                        dataset, dataset_df, exceptions = get_dataset(item_ids=item_ids)

                        if exceptions:
                            request.session['exceptions'] = exceptions
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
            # By Collections
            elif retrieval_method == 'collections':
                dataset, dataset_df, exceptions = get_dataset(collections=collections)

            else:
                messages.error(request, "You must either paste a list of \
                                item identifiers (each on a separate line) \
                                or upload a CSV file with a list of item \
                                identifiers.")
                
        # Add dataset to session and context
        request.session['dataset'] = dataset
        context['dataset'] = dataset_df

        # Add dataset info to context
        context['num_results'] = dataset_df.shape[0]

        # Toggle to display results
        context['show_results'] = True

    return render(request, "core/retrieve.html", context)


def tag_vw(request):
    context = {
        "title": "View Datasets by Tag",
        "vocab": vocab,
    }

    if request.method == "GET":
        title = request.GET.get('title')
        tag = Tag.objects.filter(title=title).first()

        if not tag:
            messages.error(request, "That tag does not exist!")
            return redirect("/")
        
        context['tag'] = tag  
        context['items'] = Item.objects.filter(tags=tag.tag_id).all()
        context['datasets'] = Dataset.objects.filter(tags=tag.tag_id).all()

    return render(request, "core/tag.html", context)


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
        # Verify that user can modify request
        if not verify_user(request, dataset.creator):
            messages.error(request, 'You do not have permission to directly edit \
                           this dataset. Click the "Edit Dataset" button to \
                           edit a copy of this dataset.')
            return redirect(f"/dataset/?id={ dataset_id }")
        
        # Create item if it's not created
        if not item:
            item = create_item_from_id(item_id=item_id)
            if not item:
                messages.error(request, "Item could not be added. Please try \
                               again or contact us to report the issue.")
                
        # Add item to dataset
        add_item(dataset=dataset, item=item)
    else:
        messages.error(request, "That dataset does not exist!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


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
    #
    dataset_id = request.GET.get('id')
    extension = request.POST.get('file_type')

    # Get dataset from db
    dataset = Dataset.objects.filter(public_id=dataset_id).first()

    # Create df from dataset
    dataset_df = dataset_to_df(dataset)

    # Create temp CSV file for download
    response = None

    with NamedTemporaryFile() as csv_file:
        # Write data to file
        if extension == 'csv':
            dataset_df.to_csv(csv_file.name, index=False, encoding='utf-8')
        else:
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            writer = pd.ExcelWriter(csv_file.name, engine='xlsxwriter')
            dataset_df.to_excel(writer, index=False, encoding='utf-8', 
                                sheet_name='dataset')
            writer.close()

        # Generate filename
        filename = f"{dataset.title.replace(' ', '_')}.{extension}" 

        # Prepare and send file
        response = FileResponse(open(csv_file.name, "rb"), filename=filename)

    return response


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
def remove_tag_vw(request):
    tag_id = request.GET.get('id')
    item_id = request.GET.get('item')
    dataset_id = request.GET.get('dataset') 
    item = dataset = None

    tag = Tag.objects.filter(tag_id=tag_id).first()

    if tag:
        if dataset_id:
            dataset = Dataset.objects.filter(public_id=dataset_id).first()
            removed = remove_tag(tag=tag, dataset=dataset, item=None)

            if not removed:
                messages.error(request, "The tag could not be removed. \
                        Please try again or contact us to report the issue.")
        
        elif item_id:
            item = Item.objects.filter(item_id=item_id).first() 
            removed = remove_tag(tag=tag, dataset=None, item=item)
            
            if not removed:
                messages.error(request, "The tag could not be removed. \
                        Please try again or contact us to report the issue.")
        
        else:
          messages.error(request, "A dataset ID or item ID must be provided.")
    else:
        messages.error(request, "That tag does not exist!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def tag_dataset_vw(request):
    tag = request.POST.get("tags").strip()
    dataset_id = request.GET.get('id')
    dataset = Dataset.objects.filter(public_id=dataset_id).first()
    
    if tag:
        if dataset:
            # Tag dataset
            tagged = add_tags(user=request.user, tags=tag, dataset=dataset, item=None)

            if not tagged:
                messages.error(request, "The dataset could not be tagged. \
                            Please try again or contact us to report the issue.")
        else:
            messages.error(request, "That dataset does not exist!")
    else:
        messages.error(request, "You entered an empty tag!")
    

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def tag_item_vw(request):
    tag = request.POST.get("tags").strip()
    item_id = request.GET.get('id')
    item = Item.objects.filter(item_id=item_id).first()

    if tag:
        # Create item if it doesn't exist in the database
        if not item:
            item = create_item(item_id=item_id, title=None, creator=None,
                            date=None, item_type=None, thumbnail=None,
                                collection_ids=None)
        
        # Tag item
        tagged = add_tags(user=request.user, tags=tag, dataset=None, item=item)

        if not tagged:
            messages.error(request, "The item could not be tagged. \
                        Please try again or contact us to report the issue.")
    else:
        messages.error(request, "You entered an empty tag!")

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
