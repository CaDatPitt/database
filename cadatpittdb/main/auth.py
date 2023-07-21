from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.contrib import messages
from markdown import markdown
from datetime import datetime
import re
from users.models import *
from .controlled_vocab import vocab
from .utilities import *

# Set User model
User = get_user_model()


""" Functions """

def check_password(request, password, password_conf):
    valid = True

    # Check for valid password
    if (len(password) < 8):
        valid = False
        messages.error(request, "Password must be at least 8 characters.")
    if (len(password) > 21):
        valid = False
        messages.error(request, "Password must be less than or equal to 20 characters.")
    # if not re.search("[a-z]", password):
    #     valid = False
    #     messages.error(request, "Password must contain at least 1 lowercase letter.")
    if not re.search("[A-Z]", password):
        valid = False
        messages.error(request, "Password must contain at least 1 uppercase letter.")
    if not re.search("[0-9]", password):
        valid = False
        messages.error(request, "Password must contain at least 1 number.")
    if not re.search("[_@()*&^%#<>,$!]", password):
        valid = False
        messages.error(request, "Password must contain at least 1 special character.")
    if password != password_conf:
        valid = False
        messages.error(request, "Passwords do not match.")
    
    return valid


def check_user_exists(request, User, username, email):
    if User.objects.filter(username=username).exists():
        messages.error(request, "That username already exists in the database!")
    elif User.objects.filter(email=email).exists():
        messages.error(request, "That email already exists in the database!")
    else:
        return False
    return True


def update_account(user=User, first_name=str, last_name=str, username=str, 
                   email=str, password=str):
    try:
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.password = password
        user.save()
        return True
    except:
        return False


def update_profile(user=User, pronouns=str, title=str, affiliation=list, 
                   other_affiliation=str, website=str, bio=str, photo_url=str):
    
    affiliation = format_affiliation(affiliations=affiliation, 
                                     other_affiliations=other_affiliation)

    try:
        user.pronouns = pronouns
        user.title = title
        user.affiliation = affiliation
        user.website = website
        user.bio = bio
        user.profile_photo_url = photo_url
        user.save()
        return True
    except:
        return False
    

def verify_user(request=HttpRequest, user=User):
    return request.user == user
