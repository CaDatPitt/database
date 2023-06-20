from django.contrib import messages
import re


def check_password(request, password, password_conf):
    valid = True

    # Check for valid password
    if (len(password) < 8):
        valid = False
        messages.error(request, "Password must be at least 8 characters.")
    if (len(password) > 21):
        valid = False
        messages.error(request, "Password must be less than or equal to 20 characters.")
    if not re.search("[a-z]", password):
        valid = False
        messages.error(request, "Password must contain at least 1 lowercase alphabet.")
    if not re.search("[A-Z]", password):
        valid = False
        messages.error(request, "Password must contain at least 1 uppercase alphabet.")
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


def format_affiliation(affiliations=[], other_affiliation=''):
    if other_affiliation:
    # process other_affiliation?
        affiliations.append(other_affiliation)

    affiliation_str = '|'.join(affiliations)
    
    return affiliation_str
