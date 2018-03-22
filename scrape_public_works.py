import requests
import json
import bs4
from bs4 import BeautifulSoup
import sys
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

CACHE_FNAME = "works_scrape_cache.json"

# Caching setup
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

# Make the request and cache the new data
def make_request_using_cache(url):
    if url in CACHE_DICTION.keys():
        print("Getting cached data...")
        return CACHE_DICTION[url]
    else:
        print("Making a request for new data...")
        response = requests.get(url)
        CACHE_DICTION[url] = response.text
        dumped_json_cache = json.dumps(CACHE_DICTION, indent=4)
        file_open = open(CACHE_FNAME,"w")
        file_open.write(dumped_json_cache)
        file_open.close()
        return CACHE_DICTION[url]

# Visit one page and grab urls for Works
def get_page_data(page_num):
    url = "https://deepblue.lib.umich.edu/data/catalog?locale=en&page={}&sort=system_create_dtsi+asc".format(page_num)
    result = make_request_using_cache(url)
    soup = BeautifulSoup(result, "html.parser")
    work_listings = soup.find("div", id="search-results").find_all("li")
    url_endings = []
    for work in work_listings:
        url_endings.append(work.find("h2").find("a")["href"])
    return url_endings

def create_work_dictionary(work_link):
    url = "https://deepblue.lib.umich.edu" + work_link
    response = make_request_using_cache(url)
    page_html = BeautifulSoup(response, "html.parser")
    work_html = page_html.find(class_="table table-striped generic_work attributes")
    work_dict = {}
    work_dict["Title"] = work_html.find("thead").find("th").text[7:]
    work_dict["url"] = url

    # Date coverage
    if work_html.find("tbody").find(class_="attribute date_coverage") != None:
        work_dict["Date coverage"] = work_html.find("tbody").find(class_="attribute date_coverage").string
    else:
        work_dict["Date coverage"] = None

    # Citation to related material
    if work_html.find("tbody").find(class_="attribute isReferencedBy") != None:
        work_dict["Citation to related material"] = work_html.find("tbody").find(class_="attribute isReferencedBy").string
    else:
        work_dict["Citation to related material"] = None

    # Keywords
    keyword_result = work_html.find("tbody").find_all(class_="attribute keyword")
    if len(keyword_result) != 0:
        keywords = []
        if len(keyword_result) > 1:
            for keyword in keyword_result:
                keywords.append(keyword.text)
        else:
            keywords.append(keyword_result[0].text)
        work_dict["Keywords"] = keywords
    else:
        work_dict["Keywords"] = None
    return work_dict

    # Will add other fields in the future

page_num = 0
all_work_links = []
for page in range(11): # I hardcoded this because of the infinite paging issue on DBD :P
    page_num += 1
    work_links = get_page_data(page_num)
    all_work_links += work_links

dictionary_of_works = {}
for link in all_work_links:
    if "collection" not in link:
        unique_identifier = link.split("/")[-1][0:8]
        dictionary_of_works[unique_identifier] = create_work_dictionary(link)

file_open = open("dbd_public_metadata.json", "w")
file_open.write(json.dumps(dictionary_of_works, indent=4))
file_open.close()
