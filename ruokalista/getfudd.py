#!/usr/bin/env python3
# Get food list for Unica's restaurants
# Can be filtered by restaurant or meals searched with regex

import urllib3
import sys
import re
from bs4 import BeautifulSoup

# Default base URL
URL = "https://murkinat.appspot.com/"
SEARCH = None
RESTAURANT = None

# Restaurant IDs and their matching string on the website
RESTAURANTS = {
    "assari": "Assarin Ullakko",
    "brygge": "Brygge",
    "delica": "Delica",
    "galilei": "Galilei",
    "dental": "Dental"
}

# Terminal colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Meal:
    def __init__(self, name, price = -1):
        self.name = name
        self.price = price

class Restaurant:
    def __init__(self, name):
        self.name = name
        self.meals = list()

# Print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Remove nbsp and such
def prettify_string(str):
    return str.replace("\xa0", " ").strip()

# Fetch value for command line argument
def get_argument(flag, alternative):
    for ind, arg in enumerate(sys.argv):
        if arg == flag or arg == alternative and alternative is not None:
            return sys.argv[ind + 1]


# Parse HTML representing a single meal
def parse_meals(soup):
    meals = []
    try:
        for meal in soup:
            meal_name = meal.select("td.mealName")[0].text
            meal_name = prettify_string(meal_name)
            meal_prices = meal.select("td.mealPrices span.mealPrice")
            meal_prices = [prettify_string(p.text) for p in meal_prices]
            meal_prices = ", ".join(meal_prices)
            meals.append(Meal(meal_name, meal_prices))
    except:
        eprint("Failed to parse meal")
        return None
    return meals


# Parse HTML representing a restaurant
def parse_restaurant(soup):
    try:
        rest_name = soup.select("h3.restaurantName")[0].text
        rest_name = prettify_string(rest_name)
        rest = Restaurant(rest_name)

        soup_meals = soup.select("table.meals tr.meal")
        meals_objs = parse_meals(soup_meals)
        rest.meals.extend(meals_objs)
    except:
        eprint("Failed to parse restaurant")
        return None
    return rest

if __name__ == "__main__":
    argument_url = get_argument("-u", "--url")
    URL = argument_url if argument_url is not None else URL
    argument_restaurant = get_argument("-r", "--restaurant")
    if argument_restaurant is not None:
        if argument_restaurant not in RESTAURANTS.keys():
            eprint("No such restaurant ID")
            exit()
        RESTAURANT = RESTAURANTS[argument_restaurant]
    argument_search = get_argument("-s", "--search")
    SEARCH = argument_search if argument_search is not None else None

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
-u --url            Override the scraped URL""")
        exit()

    http = urllib3.PoolManager(num_pools=1)
    http_response = http.request("GET", URL)
    http_response_status = http_response.status
    if http_response_status != 200:
        eprint("Received a non-OK HTTP status code: {}".format(http_response_status))
        exit()
    
    content = http_response.data
    soup = BeautifulSoup(content, "html.parser")

    # Find all .restaurant elements
    soup_restaurants = soup.select("div.restaurants > div.restaurant")
    restaurant_objs = [parse_restaurant(r) for r in soup_restaurants]
    restaurant_objs = [r for r in restaurant_objs if r is not None]
    
    # Filter restaurant
    if (RESTAURANT is not None):
        restaurant_objs = [r for r in restaurant_objs if r.name.lower().strip() == RESTAURANT.lower().strip()]
        if len(restaurant_objs) is None:
            eprint("No restaurants found")
            exit()
    
    filtered_meals = None
    # Filter by search word in meals
    if SEARCH is not None:
        SEARCH = SEARCH.lower()
        filtered_restaurants = []
        filtered_meals = []
        for rest in restaurant_objs:
            for meal in rest.meals:
                match = re.search(SEARCH, meal.name, re.I)
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
                print("{}{}{}".format(bcolors.OKGREEN, meal_str, bcolors.ENDC))
            else:
                print(meal_str)
        print("\n")