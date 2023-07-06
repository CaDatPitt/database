from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cadatpittdb.settings')
django.setup()
from users.models import Collection

MAP = {
    'title': {'selector':['td[class=\"views-field views-field-php\"] > strong']},
    'url': {'selector': ['td[class=\"views-field views-field-php\"] > a']},
    'pid': {'selector': ['td[class=\"views-field views-field-PID\"]']},
    'sites': {'selector': ['td[class=\"views-field views-field-php-2\"]']},
}

# Set dictionary for collections sites
SITES = {
    'Digital': {
        'alias': 'ULS Digital Collections',
        'base_url': 'https://digital.library.pitt.edu',
        'search_url': 'https://digital.library.pitt.edu/islandora/search/dc.title%3A%28*%29'
        },
    'DocuPitt': {
        'alias': 'Documenting Pitt',
        'base_url': 'https://historicpittsburgh.org',
        'search_url': 'https://documenting.pitt.edu/islandora/search/catch_all_fields_mt%3A%28*%29'
        },
        
    'HistPitt': {
        'alias': 'Historic Pittsburgh',
        'base_url': 'https://documenting.pitt.edu',
        'search_url': 'https://historicpittsburgh.org/islandora/search/catch_all_fields_mt%3A%28*%29'
        },
    }

def extract_collections_data():
    """
    Parses, extracts, and processes data from HTML to populate a dictionary wit
    collections data.

    Parameters
    ----------
    None

    Returns
    -------
    collections_data: dict
        a dictionary of matching field values for collections data
    """
    # Set page with collections data
    url = 'https://gamera.library.pitt.edu/collections_list'
    
    # Send a GET request to fetch the raw HTML content
    html_content = requests.get(url).text
    
    # Parse the HTML content for the web page in a BS object
    soup = BeautifulSoup(html_content, 'lxml')
    records = soup.find_all('tr')
    
    # Extract collection data from the page to populate the dictionary, one field at a time
    collections_data = []
    
    for record in records[1:]:
        record_data = {}
        for field in MAP.keys():
            selectors = MAP[field]['selector']
            field_data = np.nan
            
            for selector in selectors:
                results = record.select(selector)
                
                for result in results:
                    if field == 'url':
                        field_data = results[0]['href']
                    elif field =='sites':
                        result_data = result.text.strip()
                        results_list = result_data.split(', ')
                        field_data_list = []
                        for site in results_list:
                            if site in SITES.keys():
                                field_data_list.append(site)
                        if field_data_list:
                            field_data = "|||".join(field_data_list)
                    else:
                        field_data = result.text.strip()

            record_data[field] = field_data
        collections_data.append(record_data)
                                                               
    return collections_data


def generate_urls(df):
    for i, row in df.iterrows():
        url = row['url']
        sites = row['sites']
        url_list = []
        if pd.isna(url) and not pd.isna(sites):
            title = row['title'].replace(" ", "%5C%20")
            if '[' in title:
                title = title.split("%5C%20[", 1)[0]
            for site in sites.split('|||'):
                search_url = SITES[site]['search_url'].replace('*', title)
                url_list.append(search_url)
        elif not pd.isna(sites):
            for site in sites.split('|||'):
                site_url = SITES[site]['base_url'] + row['url']
                url_list.append(site_url)
        df.at[i, 'url'] = "|||".join(url_list)

    return df


def create_df(collections_data):
    df = pd.DataFrame.from_dict(collections_data)
    df = generate_urls(df)
    return df


def filter_collections(df):
    df.dropna(subset=['url', 'sites'], inplace=True)
    return df


def add_collections(df):
    for i, row in df.iterrows():
        if not Collection.objects.filter(collection_id=row['pid']).exists():
            new_collection = Collection(collection_id=row['pid'],
                                        title=row['title'],
                                        url=row['url'],
                                        sites=row['sites'])
            new_collection.save()


def write_collections_data(df):
    collections_data_csv = open("collections_data.csv", 'w', encoding='utf-8',
                                newline='')
    collections_data_csv.write(df.to_csv(index=False))
    collections_data_csv.close()


if __name__ == "__main__":
    collections_data = extract_collections_data()
    collections_data_df = create_df(collections_data)
    collections_data_df = filter_collections(collections_data_df)
    add_collections(collections_data_df)
