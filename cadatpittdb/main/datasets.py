from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import HttpRequest
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
from .utilities import get_rights, now
from users.models import *
from .metadata_reader import *


""" OAI Functions """

# Set URL for OAI requests
URL = 'https://digital.library.pitt.edu/oai2'


User = get_user_model()


def reformat_data(data):
    reformatted_data = {}
    
    for field in data:
        reformatted_data[field] = "|||".join(data[field])
    
    return reformatted_data


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


def get_dataset(metadata_prefix='oai_dc', item_ids=[], collections=[]):
    registry = MetadataRegistry()
    reader = pitt_oai_dc_reader
    if metadata_prefix == 'mods':
        pass
    registry.registerReader(metadata_prefix, reader)
    client = Client(URL, registry)
    dataset = []
    exceptions = []

    if item_ids:
        for id in item_ids:
            try:
                record = client.getRecord(metadataPrefix=metadata_prefix,
                                            identifier=id)
                data = record[1].getMap()
                data['item_id'] = data['item_id'][0]
                data['collection'] = []
                collection_ids = record[0].setSpec()
                for collection_id in collection_ids:
                    id = collection_id.replace("pitt_", "pitt:")
                    collection = Collection.objects.filter(collection_id=id).first()
                    if collection:
                        data['collection'].append((collection.title, 
                                                collection.get_urls()[0]))
                dataset.append(data)
            except:
                exceptions.append(id)
    else:
        records = None
        if collections:
            sets = ":".join(collections).replace("pitt:", "pitt_")
            try:
                records = client.listRecords(metadataPrefix=metadata_prefix,
                                    set=sets)
            except:
                records = []
        else:
            records = client.listRecords(metadataPrefix=metadata_prefix)

        for record in records:
            try:
                data = record[1].getMap()
                data['item_id'] = data['item_id'][0]
                data['collection'] = []
                collection_ids = record[0].setSpec()
                for collection_id in collection_ids:
                    id = collection_id.replace("pitt_", "pitt:")
                    collection = Collection.objects.filter(collection_id=id).first()
                    if collection:
                        data['collection'].append((collection.title, 
                                                collection.get_urls()[0]))
                dataset.append(data)
            except:
                exceptions.append(id)

    dataset_df = pd.DataFrame.from_dict(dataset)
    
    # decode encoded columns
    dataset_df = decode_values(dataset_df)

    return dataset, dataset_df, exceptions


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


""" Other Functions """

def add_item(dataset=Dataset, item=Item):
    try:
        dataset.items.add(item)
        return True
    except:
        return False


def add_tags(user=User, tags=str, dataset=Dataset, item=Item):
    tag_list = tags.split("|||")

    for tag in tag_list:
        cur_tag = Tag.objects.filter(text=tag).first()
        
        # Create tag if doesn't already exist
        if not cur_tag:
            try:
                cur_tag = Tag(text=tag)
                cur_tag.save()
            except:
                pass

        # Associate tag with user
        cur_tag.creator.add(user.user_id)
        
        # Associate tag with dataset or item
        if dataset:
            dataset.tags.add(cur_tag)
        else:
            item.tags.add(cur_tag)


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
    

def create_item(item_id=str, title=str, creator=str, date=str, item_type=str, 
                thumbnail=str, collection_ids=list):
    
    # try:
    new_item = Item(item_id=item_id, title=title, creator=creator, date=date,
                    type=item_type, thumbnail=thumbnail)
    new_item.save()

    # Associate collection(s) with item
    for id in collection_ids:
        collection_id = id[0].replace('_', ':')
        collection = Collection.objects.filter(collection_id=collection_id)
        new_item.collections.add(collection)
    
    return new_item
    # except:
    #     return None


def create_item_from_id(item_id=str):
    # try:
    print("item_id", item_id)
    item_record = get_item(item_id=item_id)
    title = item_record['title']
    creator = item_record['creator']
    date = item_record['date']
    item_type = item_record['type']
    thumbnail = item_record['thumbnail']
    collection_ids = item_record['collection']
    # except:
    #     return None

    new_item = Item(item_id=item_id, title=title, creator=creator, date=date,
                    type=item_type, thumbnail=thumbnail)
    new_item.save()

    # Associate collection(s) with item
    for id in collection_ids:
        collection_id = id.replace('_', ':')
        collection = Collection.objects.filter(collection_id=collection_id)
        new_item.collections.add(collection)

    return new_item


def create_dataset(dataset=dict, title=str, description=str, tags=list,
                   filters=dict, creator=str, public=bool):
    dataset_df = pd.DataFrame.from_dict(dataset)
    try:
        new_dataset = Dataset(title=title, description=description,
                              filters=filters, creator=creator, public=public)
        new_dataset.save()
    except:
        return None

    """
    Traceback (most recent call last):
    File test.py", line 15, in <module>
        create_dataset(dataset=dataset, title="Test Dataset",
    File "\main\datasets.py", line 154, in create_dataset
        for index, item in dataset:
    ValueError: too many values to unpack (expected 2)
    """
    
    # Add items
    for index, item in dataset_df:
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
                                       collection_ids=item['collection'])
                
            # Save items to dataset
            add_item(new_dataset, cur_item)
        except:
            # Do something with exceptions?
            pass

    # Add tags
    add_tags(tags=tags, dataset=new_dataset)

    return new_dataset


def filter_dataset(request=HttpRequest, dataset=pd.DataFrame, keywords=str, title=str, 
                   creator=str, contributor=str, publisher=str, depositor=str, 
                   start_year=str, end_year=str, language=str, description=str, 
                   item_type=str, subject=str, coverage=str, rights=list):
    filtered_dataset = dataset
    filters = {}

    if title:
        try:
            query = Query(title)
            filtered_dataset = filtered_dataset[filtered_dataset.title.apply(query)]
            filters['title'] = title
        except:
            messages.error(request, "'Title' filter could not be applied. \
                           Make sure that your expression is correct.")
    if creator:
        try:
            query = Query(creator)
            filtered_dataset = filtered_dataset[filtered_dataset.creator.apply(query)]
            filters['creator'] = creator
        except:
            messages.error(request, "'Creator' filter could not be applied. \
                           Make sure that your expression is correct.")
    if contributor:
        try:
            query = Query(contributor)
            filtered_dataset = filtered_dataset[filtered_dataset.contributor.apply(query)]
            filters['contributor'] = contributor
        except:
            messages.error(request, "'Contributor' filter could not be applied. \
                           Make sure that your expression is correct.")
    if publisher:
        try:
            query = Query(publisher)
            filtered_dataset = filtered_dataset[filtered_dataset.publisher.apply(query)]
            filters['publisher'] = publisher
        except:
            messages.error(request, "'Publisher' filter could not be applied. \
                           Make sure that your expression is correct.")
    if depositor:
        try:
            query = Query(depositor)
            filtered_dataset = filtered_dataset[filtered_dataset.depositor.apply(query)]
            filters['depositor'] = depositor
        except:
            messages.error(request, "'Depositor' filter could not be applied. \
                           Make sure that your expression is correct.")
    if start_year:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            filtered_dataset = filtered_dataset[
                filtered_dataset['date'][:4].astype(int) >= start_year
                ]
            filters['start_year'] = start_year
        except:
            messages.error(request, "'Start Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if end_year:
        # TO DO: Update to use lamba expression and name function for try/except
        try:
            filtered_dataset = filtered_dataset[
                filtered_dataset['date'][:4].astype(int) <= end_year
                ]
            filters['end_year'] = end_year
        except:
            messages.error(request, "'End Date' filter could not be applied.\
                           This is likely an issue with the data.")
    if language:
        try:
            query = Query(language)
            filtered_dataset = filtered_dataset[filtered_dataset.language.apply(query)]
            filters['language'] = language
        except:
            messages.error(request, "'Language' filter could not be applied. \
                           Make sure that your expression is correct.")
    if description:
        try:
            query = Query(description)
            filtered_dataset = filtered_dataset[filtered_dataset.description.apply(query)]
            filters['description'] = description
        except:
            messages.error(request, "'Description' filter could not be applied.\
                            Make sure that your expression is correct.")
    if item_type:
        try:
            query = Query(item_type)
            filtered_dataset = filtered_dataset[filtered_dataset.type.apply(query)]
            filters['item_type'] = item_type
        except:
            messages.error(request, "'Type' filter could not be applied.\
                            Make sure that your expression is correct.")
    if subject:
        try:
            query = Query(subject)
            filtered_dataset = filtered_dataset[filtered_dataset.subject.apply(query)]
            filters['subject'] = subject
        except:
            messages.error(request, "'Subject' filter could not be applied. \
                           Make sure that your expression is correct.")
    if coverage:
        try:
            query = Query(coverage)
            filtered_dataset = filtered_dataset[filtered_dataset.coverage.apply(query)]
            filters['coverage'] = coverage
        except:
            messages.error(request, "'Coverage' filter could not be applied. \
                           Make sure that your expression is correct.")
    if rights:
        rights_urls = get_rights(rights)
        # Might need to update to search for URL using regex
        filtered_dataset = filtered_dataset[
            filtered_dataset.rights.apply(lambda x: x.split('|||')[-1]).\
                isin(rights_urls)
            ]
        filters['rights'] = rights
    if keywords:
        try:
            query = Query(keywords)
            keyword_dataset = filtered_dataset[filtered_dataset.apply(query).any(1)]
            filtered_dataset = pd.concat([keyword_dataset, filtered_dataset])
            filters['keywords'] = keywords
        except:
            messages.error(request, "'Keywords' filter could not be applied.\
                            Make sure that your expression is correct.")

    return filtered_dataset


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


def delete_dataset(dataset=Dataset):
    try:
        dataset.delete()
        return True
    except:
        return False


def download_dataset(request, dataset):
    tmp = tempfile.NamedTemporaryFile(delete=False, prefix="dataset",
                                      suffix=now())
    with open(tmp.name, 'w') as f:
        tmp.write(dataset.to_csv(index=False))
    tmp.close()
    os.unlink(tmp.name)


def pin_dataset(user=User, dataset=Dataset):
    try:
        dataset.pinned_by.add(user)
        return True
    except:
        return False


def pin_item(user=User, item=Item):
    try:
        item.pinned_by.add(user)
        return True
    except:
        return False


def remove_item(dataset=Dataset, item=Item):
    try:
        item.datasets.remove(dataset)
        return True
    except:
        return False


def remove_tag(tag=str, dataset=Dataset, item=Item):
    # Associate tag with dataset or item
    try:
        if dataset:
            dataset.tags.remove(tag)
        else:
            item.tags.remove(tag)
        return True
    except:
        return False
    

# def tag_dataset(dataset=Dataset, tag=Tag):
#     try:
#         dataset.tags.add(tag)
#         return True
#     except:
#         return False
    

# def tag_item(item=Item, tag=Tag):
#     try:
#         item.tags.add(tag)
#         return True
#     except:
#         return False


def unpin_dataset(user=User, dataset=Dataset):
    try:
        dataset.pinned_by.remove(user)
        return True
    except:
        return False


def unpin_item(user=User, item=Item):
    try:
        item.pinned_by.remove(user)
        return True
    except:
        return False


def update_dataset(user=User, dataset=Dataset, title=str, description=str, 
                   tags=str, public=bool):
    # try:
    dataset.title = title
    dataset.description = description
    dataset.public = public
    dataset.save()
    add_tags(user=user, dataset=dataset, tags=tags)
    return True
    # except:
    #     return False

