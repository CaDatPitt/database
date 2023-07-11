from django.contrib.auth import get_user_model
from django.contrib import messages
from markdown import markdown
from datetime import datetime
import re
from .controlled_vocab import vocab
from users.models import *

# Set User model
User = get_user_model()

""" Functions """

def format_affiliation(affiliations=[], other_affiliation=''):
    affiliation_str = '|||'.join(affiliations)
    affiliation_str += other_affiliation
    return affiliation_str


def get_user_datasets(user=User):
    datasets = Dataset.objects.filter(creator=user).all()
    return datasets


def get_item_datasets(item=Item):
    datasets = Dataset.objects.filter(items=item).all()
    return datasets


def get_markdown(input=str) -> str:
    if input:
        text = input
        # Ensure hyperlink prefix
        # pattern for Markdown hyperlink
        pattern = r'\[[^!?\s]*\]\([^!?\s]*\)'
        
        for match in re.finditer(pattern, text):
            hyperlink = match[0]
            # Check if hyperlink is not prefixed
            if re.match(r'\[[^!?\s]*\]\([^http][^!?\s]*', hyperlink) or \
                re.match(r'\[[^!?\s]*\]\([^www.][^!?\s]*', hyperlink) or \
                re.match(r'\[[^!?\s]*\]\([^\\][^!?\s]*', hyperlink):
                prefixed_hyperlink = hyperlink.replace("(", "(//")
                text = text.replace(hyperlink, prefixed_hyperlink)

        # Strip enclosing paragraph marks, <p> ... </p>, which markdown() forces
        text = re.sub("(^<P>|</P>$)", "", markdown(text), flags=re.IGNORECASE)

        # Add target
        text = text.replace("<a href", "<a target='_blank' href")

        return text
    return input


def get_rights(rights_input=list) -> list:
    rights = []

    for statement, url in vocab['rights'].items():
        if statement in rights_input:
            rights.append(url)

    return rights


def get_creators():
    User = get_user_model()
    users = Dataset.objects.all().values_list('creator', flat=True)
    user_list = []
    
    for user in users:
        user_list.append(user)
    creators = User.objects.filter(user_id__in=user_list).all()

    return creators


def now():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
