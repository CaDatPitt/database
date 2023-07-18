from django.contrib.auth import get_user_model
from django.contrib import messages
from datetime import datetime
import re
from .controlled_vocab import vocab
from users.models import *

# Set User model
User = get_user_model()

""" Functions """

def format_affiliation(affiliations=[], other_affiliations=''):
    affiliations += other_affiliations.split('|||')
    affiliation_str = '|||'.join(affiliations)
    return affiliation_str


def get_dataset_collections():
    collections_list = []
    for collection in Collection.objects.all():
        if Dataset.objects.filter(items__collections=collection):
            collections_list.append(collection)
    
    return collections_list


def get_item_datasets(item=Item):
    datasets = Dataset.objects.filter(items=item).all()
    return datasets


def get_user_datasets(user=User):
    datasets = Dataset.objects.filter(creator=user).all()
    return datasets


def get_rights_urls(rights_input=list) -> list:
    rights_urls = []

    for statement, url in vocab['rights'].items():
        if statement in rights_input:
            rights_urls.append(url)

    return rights_urls


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
