#################################
# Name:
# Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key

STATE_CACHE_FILENAME = "state_cache.json"
PARK_CACHE_FILENAME = "park_cache.json"
NEAR_CACHE_FILENAME = "near_cache.json"

NEAR_CACHE_DICT = {}
STATE_CACHE_DICT = {}
PARK_CACHE_DICT = {}


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        information = "{} ({}): {} {}".format(
            self.name, self.category, self.address, self.zipcode)
        return information


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    global STATE_CACHE_DICT
    if not STATE_CACHE_DICT:
        print("Fetching States!")
        state_name_dict = {}
        url = "https://www.nps.gov/index.htm"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        mydivs = soup.find_all(
            "ul", class_="dropdown-menu SearchBar-keywordSearch")[0].find_all('a')

        for i in range(len(mydivs)):
            state_name_dict[mydivs[i].getText(
            ).lower()] = "https://www.nps.gov" + mydivs[i]['href']

        STATE_CACHE_DICT = state_name_dict
        save_cache(STATE_CACHE_DICT, STATE_CACHE_FILENAME)
        return STATE_CACHE_DICT
    else:
        print("Using cache!")
        return STATE_CACHE_DICT


def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''
    response = requests.get(site_url)
    soup = BeautifulSoup(response.text, "html.parser")
    name = soup.find('a', class_="Hero-title").getText()
    category = soup.find('span', class_="Hero-designation").getText()
    address = soup.find('span', itemprop="addressLocality").getText()
    state = soup.find('span', itemprop="addressRegion").getText()
    zipcode = soup.find('span', itemprop="postalCode").getText()
    telephone = soup.find('span', itemprop="telephone").getText()
    state_address = address + ", " + state

    ins = NationalSite(
        category=category, name=name, address=state_address,
        zipcode=zipcode.strip(),
        phone=telephone[1:])
    return ins


def cache_to_obj(dict_ls):
    '''Turn the cache dict into NationalSite object.

    Parameters
    ----------
    dict_ls: list
        a list of dictionaries from the cache

    Returns
    -------
    ins_ls
        a list of NationalSite objects 
    '''
    ins_ls = []
    for dict in dict_ls:
        ins_ls.append(
            NationalSite(
                dict["category"],
                dict["name"],
                dict["address"],
                dict["zipcode"],
                dict["phone"]))
    return ins_ls


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''

    if state_url in PARK_CACHE_DICT.keys():
        print("Using cache")
        national_site_ins = cache_to_obj(PARK_CACHE_DICT[state_url])
        return national_site_ins
    else:
        print("Fetching Parks!")
        response = requests.get(state_url)
        soup = BeautifulSoup(response.text, "html.parser")
        base_url = "https://www.nps.gov"
        national_site_ls = []
        national_site_ins = []
        for tmp in soup.find_all("li", class_="clearfix")[0:-1]:
            url = base_url + tmp.find("h3").find('a')['href']
            national_site_ls.append(get_site_instance(url).__dict__)
            national_site_ins.append(get_site_instance(url))
        PARK_CACHE_DICT[state_url] = national_site_ls
        save_cache(PARK_CACHE_DICT, PARK_CACHE_FILENAME)
        return national_site_ins


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    near_key = site_object.info()
    if near_key in NEAR_CACHE_DICT.keys():
        print("Using cache")
        return NEAR_CACHE_DICT[near_key]
    else:
        print("Fetching near places")
        url = "https://www.mapquestapi.com/search/v2/radius?origin ={}\
        &radius={}&maxMatches={}&ambiguities={}\
        &outFormat={}&key={}".format(site_object.address, 10, 10, "ignore", "json", secrets.API_KEY)
        places = requests.get(url).json()
        NEAR_CACHE_DICT[near_key] = places
        save_cache(NEAR_CACHE_DICT, NEAR_CACHE_FILENAME)
        return NEAR_CACHE_DICT[near_key]


def open_cache(cache_filename):
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict, filename):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(filename, "w")
    fw.write(dumped_json_cache)
    fw.close()


if __name__ == "__main__":

    state_url = "https://www.nps.gov/state/mi/index.htm"
    STATE_CACHE_DICT = open_cache(STATE_CACHE_FILENAME)
    PARK_CACHE_DICT = open_cache(PARK_CACHE_FILENAME)
    NEAR_CACHE_DICT = open_cache(NEAR_CACHE_FILENAME)
    state_url_dict = build_state_url_dict()
    outerLoop = True
    while outerLoop:
        state_name = input(
            "Enter a state name (e.g. Michigan, michigan) or exit: ").lower()
        if state_name == "exit":
            break
        if state_name not in state_url_dict:
            print("wrong name")
            print("[Error] Enter proper state name")
            continue

        state_url = state_url_dict[state_name]
        park_ls = get_sites_for_state(state_url)

        print("---------------------")
        print("List of national sites in {}".format(state_name))
        print("---------------------")
        for i, park in enumerate(park_ls):
            print("[{}] {}".format(i+1, park.info()))

        while True:
            number = input(
                "Choosethe number for detail search or exit or back: ")

            if number == "back":
                break
            if number == "exit":
                outerLoop = False
                break
            if int(number) > len(park_ls):
                print("[Error] Invalid input")
                continue

            near_places = get_nearby_places(park_ls[int(number)-1])[
                "searchResults"]

            for i in range(len(near_places)):
                tmp = near_places[i]["fields"]
                name = "no name" if not tmp["name"] else tmp["name"]
                address = "no address" if not tmp["address"] else tmp["address"]
                category = "no category" if not tmp["group_sic_code_name"] else tmp["group_sic_code_name"]
                city = "no city" if not tmp["city"] else tmp["city"]
                print("- {} ({}): {}, {}".format(name, category, address, city))
