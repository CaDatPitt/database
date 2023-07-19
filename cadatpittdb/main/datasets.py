from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import HttpRequest
from django.db.models import Q
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from eldar import Query
from datetime import datetime
from uuid import uuid4
import pandas as pd
import re
import os
import tempfile
from .decode import decode_values
from .controlled_vocab import vocab
from .utilities import get_rights_urls, now
from users.models import *
from .metadata_reader import *


""" OAI Functions """

# Set URL for OAI requests
URL = 'https://digital.library.pitt.edu/oai2'


User = get_user_model()


def reformat_data(data=dict):
    reformatted_data = {}
    
    for field in data:
        if field == 'collection':
            collections = [item[0] for item in data[field]]
            reformatted_data[field] = collections
        elif isinstance(data[field], list):
            reformatted_data[field] = "|||".join(data[field])
        else:
            reformatted_data[field] = data[field]
    
    return reformatted_data


def reformat_for_download(data=dict):
    reformatted_data = {}
    
    for field in data:
        reformatted_data[field] = "|||".join(data[field])
    
    return reformatted_data


def process_record(record, download=False):
    # Map record data
    data = record[1].getMap()

    # Append record data to dataset list
    if download:
        # Return reformmatted data
        return reformat_for_download(data)
    else:
        # Store item ID as a string instead of a list
        data['item_id'] = data['item_id'][0]

        # Get collection IDs 
        collection_ids = record[0].setSpec()
        data['collection'] = []

        # Use Collection IDs to retrieve collection objects from db
        for collection_id in collection_ids:
            id = collection_id.replace("pitt_", "pitt:")
            collection = Collection.objects.filter(collection_id=id).first()
            
            # Append collection title and URL to list
            if collection:
                data['collection'].append((collection.title, 
                                            collection.get_urls()[0]))
        
        return data


def get_collections():
    sets = []
    url_prefix = "https://digital.library.pitt.edu/islandora/object/"

    registry = MetadataRegistry()
    reader = oai_dc_reader
    registry.registerReader('oai_dc', reader)
    client = Client(URL, registry)
    results = client.listSets()

    for set in results:
        id = set[0]
        title = set[1]
        url = url_prefix + title.replace('_', ':')
        sets.append({'id': id, 'title': title, 'url': url})

    return sets


def get_dataset(metadata_prefix='oai_dc', item_ids=[], collections=[],
                download=False):
    
    # pyoai objects
    registry = MetadataRegistry()
    reader = pitt_oai_dc_reader
    registry.registerReader(metadata_prefix, reader)
    client = Client(URL, registry)
    dataset = []
    exceptions = []

    # Build dataset from list of item IDs
    if item_ids:
        for item_id in item_ids:
            id = item_id.replace("pitt:", "pitt_")
            # Try to get item record from OAI-PMH
            try:
                # Get record object
                record = client.getRecord(metadataPrefix=metadata_prefix,
                                            identifier=id)
                
                # Get data from record object
                if download:
                    data = process_record(record, download=True)
                else:
                    data = process_record(record)
                    
                # Append data to dataset list
                dataset.append(data)

            # Add exception message to list
            except:
                exceptions.append("'%s'" % item_id)
    
    # Get item records by collection/set(s)
    else:
        # Reformat and combine list of collection IDs
        sets = ":".join(collections).replace("pitt:", "pitt_")
        flag = False
        
        # Try to get item records from OAI-PMH
        records = []
        try:
            records = client.listRecords(metadataPrefix=metadata_prefix,
                                set=sets)
        # If retrieval not succesful, set records to empty list
        except:
            flag = True
            
        
        # Get data from record objects
        for record in records:
            try:
                # Process data
                data = process_record(record)
                
                # Append data to dataset lit
                dataset.append(data)
            except:
                exceptions.append("'%s'" % record['item_id'][0])

    # Create DataFrame from list of dictionaries (dataset)
    dataset_df = pd.DataFrame.from_dict(dataset)
    
    if download:
        return dataset_df
    else:
        # Decode encoded columns
        dataset_df = decode_values(dataset_df)

        return dataset, dataset_df, exceptions, flag


def get_item(metadata_prefix="oai_dc", item_id=str):
    registry = MetadataRegistry()
    reader = pitt_oai_dc_reader
    if metadata_prefix == 'mods':
        pass
    registry.registerReader(metadata_prefix, reader)
    client = Client(URL, registry)
    item_id = item_id.replace("pitt:", "pitt_")

    try:
        record = client.getRecord(metadataPrefix=metadata_prefix, 
                                    identifier=item_id)
        collection_ids = record[0].setSpec()
        data = record[1].getMap()
        item_record = reformat_data(data)
        item_record['collection'] = collection_ids
        return item_record
    except:
        return None


""" Dataset Functions """

def copy_dataset(user=User, dataset=Dataset, title=str):
    items = dataset.items.all()

    try:
        # Create copy of given dataset
        dataset.pk = None
        dataset.public_id = str(uuid4())
        dataset.title = title
        dataset.creator = user
        dataset.date_created = datetime.now()
        dataset.last_modified = datetime.now()
        dataset._state.adding = True
        dataset.save() 

        # Associate items with dataset
        for item in items:
            add_item(dataset=dataset, item=item)

        return dataset
    except:
        return None


def create_dataset(dataset=dict, title=str, description=str, tags=list,
                   filters=dict, creator=User, public=bool, saved_results=bool):
    try:
        new_dataset = Dataset(title=title, description=description, 
                                filters=filters, creator=creator, public=public,
                                saved_results=saved_results)
        new_dataset.save()
    except:
        return None
    
    # Add items and log exceptions
    exceptions = []
    for record in dataset:
        item = reformat_data(record)
        try:
            # Create item if it doesn't already exist
            cur_item = Item.objects.filter(item_id=item['item_id']).first()
            if not cur_item:
                cur_item = create_item(item_id=item['item_id'],
                                       title=item['title'],
                                       creator=item['creator'],
                                       date=item['date'],
                                       item_type=item['type'],
                                       thumbnail=item['thumbnail'],
                                       collections=item['collection'])
                
            # Save items to dataset
            add_item(new_dataset, cur_item)
        except:
            # Do something with exceptions?
            exceptions.append(item)

    # Add tags
    if tags:
        add_tags(user=creator, tags=tags, dataset=new_dataset, item=None)

    # Update collections
    for collection in Collection.objects.all():
        if Dataset.objects.filter(items__collections=collection):
            collection.has_dataset = 1
        else:
            collection.has_dataset = 0
        collection.save()

    return new_dataset


def dataset_to_df(dataset=Dataset):
    item_ids = list(dataset.items.values_list('item_id', flat=True))
    dataset = get_dataset(item_ids=item_ids, download=True)
    return pd.DataFrame.from_dict(dataset)


def filter_field(x, keywords='', other_field='', start_year='', end_year=''):
    if keywords:
        eldar = Query(keywords, match_word=False)
        for field in x:
            if field:
                result = []
                if isinstance(field[0], list):
                    result = eldar.filter(field[0])
                else:
                    result = eldar.filter(field)
                if len(result) > 0:
                    return True
        return False
    if other_field:
        if x:
            eldar = Query(other_field, match_word=False)
            result = eldar.filter(x)
            if len(result) > 0:
                return True
        return False
    if start_year:
        for date in x: 
            if int(date[:4]) < int(start_year): # change this to look for years in value using regex
                return False
        return True
    if end_year:
        for date in x:
            if int(date[:4]) > int(end_year):
                return False
        return True


def filter_dataset(request=HttpRequest, dataset=list, keywords=str, title=str, 
                   creator=str, contributor=str, publisher=str, depositor=str, 
                   start_year=str, end_year=str, language=str, description=str, 
                   item_type=str, subject=str, coverage=str, rights=list):
    filtered_dataset_df = pd.DataFrame.from_dict(dataset)
    filters = {}

    if title:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['title'].apply(filter_field, 
                                                   other_field=title)
                ]
            )
            filters['title'] = title
        except:
            messages.error(request, "'Title' filter could not be applied. \
                           Make sure that your expression is correct.")
    if creator:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['creator'].apply(filter_field, 
                                                     other_field=creator)
                ]
            )
            filters['creator'] = creator
        except:
            messages.error(request, "'Creator' filter could not be applied. \
                           Make sure that your expression is correct.")
    if contributor:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['contributor'].apply(filter_field, 
                                                         other_field=contributor)
                ]
            )
            filters['contributor'] = contributor
        except:
            messages.error(request, "'Contributor' filter could not be applied. \
                           Make sure that your expression is correct.")
    if publisher:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['publisher'].apply(filter_field, 
                                                       other_field=publisher)
                ]
            )
            filters['publisher'] = publisher
        except:
            messages.error(request, "'Publisher' filter could not be applied. \
                           Make sure that your expression is correct.")
    if depositor:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['depositor'].apply(filter_field,
                                                       other_field=depositor)
                ]
            )
            filters['depositor'] = depositor
        except:
            messages.error(request, "'Depositor' filter could not be applied. \
                           Make sure that your expression is correct.")
    if start_year:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['date'].apply(filter_field, 
                                                  start_year=start_year)
                ]
            )
            filters['start_year'] = int(start_year)
        except:
            messages.error(request, "'Start Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if end_year:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['date'].apply(filter_field, 
                                                end_year=end_year)
                ]
            )
            filters['end_year'] = int(end_year)
        except:
            messages.error(request, "'End Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if language:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['language'].apply(filter_field,
                                                      other_field=language)
                ]
            )
            filters['language'] = language
        except:
            messages.error(request, "'Language' filter could not be applied. \
                           Make sure that your expression is correct.")
    if description:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['description'].apply(filter_field, 
                                                         other_field=description)
                ]
            )
            filters['description'] = description
        except:
            messages.error(request, "'Description' filter could not be applied.\
                            Make sure that your expression is correct.")
    if item_type:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['item_type'].apply(filter_field,
                                                       other_field=item_type)
                ]
            )
            filters['item_type'] = item_type
        except:
            messages.error(request, "'Type' filter could not be applied.\
                            Make sure that your expression is correct.")
    if subject:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['subject'].apply(filter_field,
                                                     other_field=subject)
                ]
            )
            filters['subject'] = subject
        except:
            messages.error(request, "'Subject' filter could not be applied. \
                           Make sure that your expression is correct.")
    if coverage:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df['coverage'].apply(filter_field,
                                                      other_field=coverage)
                ]
            )
            filters['coverage'] = coverage
        except:
            messages.error(request, "'Coverage' filter could not be applied. \
                           Make sure that your expression is correct.")
    if rights:
        rights_str = " OR ".join(rights)
        # Might need to update to search for URL using regex
        filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
            filtered_dataset_df.rights.apply(filter_field,
                                                      other_field=rights_str)
            ])
        filters['rights'] = rights
    if keywords:
        try:
            filtered_dataset_df = pd.DataFrame(filtered_dataset_df[
                filtered_dataset_df.apply(filter_field, keywords=keywords, axis=1)
                ])
            filters['keywords'] = keywords
        except:
            messages.error(request, "'Keywords' filter could not be applied.\
                            Make sure that your expression is correct.")

    return filtered_dataset_df, filtered_dataset_df.to_dict('records')


def filter_datasets(request, keywords=str, title=str, creator=str, 
                    description=str, tags=list, min_num_items=int, 
                    max_num_items=int, start_date=str, end_date=str):
    results = Dataset.objects.all()

    # add search parameters to dictionary, then update dataset
    if title:
        try:
            query = Query(title)
        except:
            messages.error(request, "'Title' filter could not be applied. \
                           Make sure that your expression is correct.")
    if creator:
        try:
            query = Query(creator)
        except:
            messages.error(request, "'Creator' filter could not be applied. \
                           Make sure that your expression is correct.")
    if description:
        try:
            query = Query(description)
        except:
            messages.error(request, "'Description' filter could not be applied.\
                            Make sure that your expression is correct.")
    if tags:
        try:
            query = Query(tags)
        except:
            messages.error(request, "'Type' filter could not be applied.\
                            Make sure that your expression is correct.")
    if min_num_items:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            query = Query(min_num_items)
        except:
            messages.error(request, "'Start Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if max_num_items:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            query = Query(max_num_items)
        except:
            messages.error(request, "'End Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if start_date:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            query = Query(start_date)
        except:
            messages.error(request, "'Start Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if end_date:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            query = Query(end_date)
        except:
            messages.error(request, "'End Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if keywords:
        try:
            query = Query(keywords)
        except:
            messages.error(request, "'Keywords' filter could not be applied.\
                            Make sure that your expression is correct.")

    return results


def delete_dataset(dataset_id=str):
    try:
        deleted = Dataset.objects.filter(public_id=dataset_id).delete()
        if deleted:
            return True
        else:
            return False
    except:
        return False


def pin_dataset(user=User, dataset=Dataset):
    try:
        dataset.pinned_by.add(user)
        dataset.save()
        return True
    except:
        return False
    
    
def unpin_dataset(user=User, dataset=Dataset):
    try:
        dataset.pinned_by.remove(user)
        return True
    except:
        return False


""" Item Functions """

def add_item(dataset=Dataset, item=Item):
    try:
        dataset.items.add(item)
        return True
    except:
        return False    


def create_item(item_id=str, title=str, creator=str, date=str, item_type=str, 
                thumbnail=str, collections=list):
    
    try:
        new_item = Item(item_id=item_id, title=title, creator=creator, date=date,
                        type=item_type, thumbnail=thumbnail)
        new_item.save()

        # Associate collection(s) with item
        for title in collections:
            collection = Collection.objects.filter(title=title).first()
            new_item.collections.add(collection)
        
        return new_item
    except:
        return None  


def create_item_from_id(item_id=str):
    # Get item record data
    try:
        item_record = get_item(item_id=item_id)
        title = item_record['title']
        creator = item_record['creator']
        date = item_record['date']
        item_type = item_record['type']
        thumbnail = item_record['thumbnail']
        collection_ids = item_record['collection']
    except:
        return None
    
    # Create new item in database
    new_item = Item(item_id=item_id, title=title, creator=creator, date=date,
                    type=item_type, thumbnail=thumbnail)
    new_item.save()

    # Associate collection(s) with item
    for id in collection_ids:
        collection_id = id.replace('_', ':')
        collection = Collection.objects.filter(collection_id=collection_id).first()
        new_item.collections.add(collection)

    return new_item


def pin_item(user=User, item=Item):
    try:
        item.pinned_by.add(user)
        item.save()
        return True
    except:
        return False


def remove_item(dataset=Dataset, item=Item):
    try:
        dataset.items.remove(item)
        dataset.save()
        return True
    except:
        return False


def unpin_item(user=User, item=Item):
    try:
        item.pinned_by.remove(user)
        return True
    except:
        return False


""" Tag Functions """

def add_tags(user=User, tags=str, dataset=Dataset, item=Item):
    tag_list = tags.split("|||")
    exceptions = []

    for tag in tag_list:
        cur_tag = Tag.objects.filter(title=tag).first()
        
        # Create tag if doesn't already exist
        if not cur_tag:
            try:
                cur_tag = Tag(title=tag)
                cur_tag.save()
            except:
                exceptions.append(tag)
                continue

        try:
            # Associate tag with user
            cur_tag.creator.add(user.user_id)
            
            # Associate tag with dataset or item
            if dataset:
                dataset.tags.add(cur_tag)
                dataset.save()
            if item:
                item.tags.add(cur_tag)
                item.save()
        except:
            exceptions.append(tag)
    if len(tag_list) == len(exceptions):
        return False
    return True


def remove_tag(tag=str, dataset=Dataset, item=Item):
    # Associate tag with dataset or item
    try:
        if dataset:
            dataset.tags.remove(tag)
            dataset.save()
        else:
            item.tags.remove(tag)
            item.save()
        return True
    except:
        return False


def update_dataset(user=User, dataset=Dataset, title=str, description=str, 
                   tags=str, public=bool):
    try:
        dataset.title = title
        dataset.description = description
        dataset.public = public
        dataset.save()
        add_tags(user=user, tags=tags, dataset=dataset, item=None)
        return True
    except:
        return False


def search(keywords):
    found = False

    # Search Collections
    collections = Collection.objects.filter(Q(collection_id__icontains=keywords) |
                                            Q(title__icontains=keywords)).distinct()
    if collections: found = True

    # Search Datasets
    datasets = Dataset.objects.filter(Q(title__icontains=keywords) |
                                      Q(description__icontains=keywords)).distinct()
    if datasets: found = True

    # Search Items
    items = Item.objects.filter(Q(item_id__icontains=keywords) |
                                Q(title__icontains=keywords) |
                                Q(creator__icontains=keywords)).distinct()
    if items: found = True

    # Search Pages
    pages = Page.objects.filter(Q(title__icontains=keywords) |
                                Q(content__icontains=keywords)).distinct()
    if pages: found = True

    # Search Tags
    tags = Tag.objects.filter(Q(title__icontains=keywords)).distinct()
    if tags: found = True

    # Search Users
    users = User.objects.filter(Q(first_name__icontains=keywords) | 
                                Q(last_name__icontains=keywords) |
                                Q(title__icontains=keywords) |
                                Q(bio__icontains=keywords)).distinct()
    if users: found = True
    
    # Add results to dict
    results = {
        'collections': collections,
        'datasets': datasets,
        'items': items,
        'pages': pages,
        'tags': tags,
        'users': users
    }

    return found, results
