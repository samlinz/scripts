#!/usr/bin/env python3
# Get food list for Unica's restaurants
# Can be filtered by restaurant or meals searched with regex

import urllib3
import sys
import re
from bs4 import BeautifulSoup
import datetime
import os
import jsonpickle

# Default base URL
URL = "https://murkinat.appspot.com/"

# Print debug data or not
DEBUG = False

_SEARCH = None
_RESTAURANT = None

# Restaurant IDs and their matching string on the website
RESTAURANTS = {
    "assari": "Assarin Ullakko",
    "brygge": "Brygge",
    "delica": "Delica",
    "galilei": "Galilei",
    "dental": "Dental",
}

# Get current day for caching
_CURRENT_DATE = datetime.date.today()
_CACHE_DAYS = 7
_CACHED_RESTAURANTS = None
_HOME_DIR = os.path.expanduser("~")
_CONFIG_DIR = _HOME_DIR + "/.config/ruokalista/"
_FILE_PREFIX = "ruokalista"


class _BCOLORS:
    """Enum for terminal colors in BASH"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Meal:
    def __init__(self, name, price=-1):
        self.name = name
        self.price = price


class Restaurant:
    def __init__(self, name):
        self.name = name
        self.meals = list()


def _check_config_dir():
    """Create configuration directory if it does not exists already"""
    global _CONFIG_DIR
    if not os.path.exists(_CONFIG_DIR):
        os.makedirs(_CONFIG_DIR)


def _read_cache():
    """Read scraped info from cache"""
    global _CACHE_DAYS, _CURRENT_DATE, _CACHED_RESTAURANTS, _CONFIG_DIR, _FILE_PREFIX
    _check_config_dir()
    for file in os.listdir(_CONFIG_DIR):
        file_date_re = re.match(
            _FILE_PREFIX + r"(\d{4})-(\d{2})-(\d{2})", file)
        if file_date_re is not None and len(file_date_re.groups()) == 3:
            re_matches = file_date_re.groups()
            file_date = datetime.date(int(re_matches[0]), int(
                re_matches[1]), int(re_matches[2]))
            if (_CURRENT_DATE - file_date).days > _CACHE_DAYS:
                os.remove(file)
            if _CURRENT_DATE == file_date:
                # Read cache
                with open(_CONFIG_DIR + file, mode="r") as f:
                    try:
                        obj_encoded = f.read()
                        _CACHED_RESTAURANTS = jsonpickle.decode(obj_encoded)
                    except:
                        _eprint("Failed to deserialize object from " + file)
                        _CACHED_RESTAURANTS = None


def _write_cache(obj):
    """Write parsed object to cache"""
    global _CONFIG_DIR, _CURRENT_DATE, _FILE_PREFIX
    _check_config_dir()
    file_path = _CONFIG_DIR + _FILE_PREFIX + str(_CURRENT_DATE)
    if os.path.exists(file_path):
        os.remove(file_path)
    obj_encoded = jsonpickle.encode(obj)
    with open(file_path, "w+") as f:
        f.write(obj_encoded)


def _dprint(str):
    global DEBUG
    if DEBUG:
        print("DEBUG: " + str)


def _eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


def _prettify_string(str):
    """Remove nbsp and such"""
    return str.replace("\xa0", " ").strip()


def _get_argument(flag, alternative):
    """"Fetch value for command line argument"""
    for ind, arg in enumerate(sys.argv):
        if arg == flag or arg == alternative and alternative is not None:
            return sys.argv[ind + 1]


def _parse_meals(soup):
    """Parse HTML representing a single meal"""
    meals = []
    try:
        for meal in soup:
            meal_name = meal.select("td.mealName")[0].text
            meal_name = _prettify_string(meal_name)
            meal_prices = meal.select("td.mealPrices span.mealPrice")
            meal_prices = [_prettify_string(p.text) for p in meal_prices]
            meal_prices = ", ".join(meal_prices)
            meals.append(Meal(meal_name, meal_prices))
    except:
        _eprint("Failed to parse meal")
        return None
    return meals


def _parse_restaurant(soup):
    """Parse HTML representing a restaurant"""
    try:
        rest_name = soup.select("h3.restaurantName")[0].text
        rest_name = _prettify_string(rest_name)
        rest = Restaurant(rest_name)

        soup_meals = soup.select("table.meals tr.meal")
        meals_objs = _parse_meals(soup_meals)
        rest.meals.extend(meals_objs)
    except:
        _eprint("Failed to parse restaurant")
        return None
    return rest


if __name__ == "__main__":
    _dprint("Entering application")

    # Handle arguments
    argument_url = _get_argument("-u", "--url")
    URL = argument_url if argument_url is not None else URL
    argument_restaurant = _get_argument("-r", "--restaurant")
    if argument_restaurant is not None:
        if argument_restaurant not in RESTAURANTS.keys():
            _eprint("No such restaurant ID")
            exit()
        _RESTAURANT = RESTAURANTS[argument_restaurant]
    argument_clear_cache = _get_argument("-c", "--clear-cache")
    argument_search = _get_argument("-s", "--search")
    _SEARCH = argument_search if argument_search is not None else None

    _dprint("Handled arguments")

    # Remove old files and read from cache if available
    if not argument_clear_cache:
        _dprint("Reading cache")
        _read_cache()

    # List restaurants
    if "-l" in sys.argv or "--list" in sys.argv:
        print("ID - Restaurant name")
        print("--------------------")
        for k, v in RESTAURANTS.items():
            print("{} - {}".format(k, v))
        exit()

    # Show help
    if "-h" in sys.argv or "--help" in sys.argv:
        print("""StudentRestaurantScraper

Search for daily meal lists from Turku's student restaurants

Arguments:
-h --help           Display this help
-r --restaurant     Show only specific restaurant
-l --list           List all restaurant IDs
-s --search         Search for a meal with specific word in it
-c --clear-cache    Deletes cache and retrieves new content explicitly
-u --url            Override the scraped URL""")
        exit()

    if _CACHED_RESTAURANTS is None:
        http = urllib3.PoolManager(num_pools=1)
        _dprint("Sending request to " + URL)        
        http_response = http.request("GET", URL)
        http_response_status = http_response.status
        _dprint("Received response")        
        if http_response_status != 200:
            _eprint(
                "Received a non-OK HTTP status code: {}".format(http_response_status))
            exit()

        content = http_response.data
        _dprint("Creating soup")        
        soup = BeautifulSoup(content, "html.parser")

        _dprint("Parsing content")    

        # Find all .restaurant elements
        soup_restaurants = soup.select("div.restaurants > div.restaurant")
        restaurant_objs = [_parse_restaurant(r) for r in soup_restaurants]
        restaurant_objs = [r for r in restaurant_objs if r is not None]

        # Cache file
        _dprint("Caching restaurant information")
        _write_cache(restaurant_objs)
    else:
        restaurant_objs = _CACHED_RESTAURANTS
        _dprint("Restraurant information loaded from cache")

    # Filter restaurant
    if (_RESTAURANT is not None):
        _dprint("Filtering by restaurant")        
        restaurant_objs = [r for r in restaurant_objs if r.name.lower(
        ).strip() == _RESTAURANT.lower().strip()]
        if len(restaurant_objs) is None:
            _eprint("No restaurants found")
            exit()

    filtered_meals = None
    # Filter by search word in meals
    if _SEARCH is not None:
        _dprint("Filtering by word")            
        _SEARCH = _SEARCH.lower()
        filtered_restaurants = []
        filtered_meals = []
        for rest in restaurant_objs:
            for meal in rest.meals:
                match = re.search(_SEARCH, meal.name, re.I)
                if match is not None:
                    filtered_restaurants.append(rest)
                    filtered_meals.append(meal)
        restaurant_objs = filtered_restaurants

    # Output all scraped and filtered data in somewhat pretty format
    for rest in restaurant_objs:
        rest_str = "Restaurant: {}".format(rest.name)
        print(rest_str)
        print("-" * len(rest_str))
        for meal in rest.meals:
            meal_str = "`{}`\n\t{}\n".format(meal.name, meal.price)
            if (filtered_meals is not None and meal in filtered_meals):
                print("{}{}{}".format(_BCOLORS.OKGREEN, meal_str, _BCOLORS.ENDC))
            else:
                print(meal_str)
        print("\n")

    _dprint("Exiting application successfully")
