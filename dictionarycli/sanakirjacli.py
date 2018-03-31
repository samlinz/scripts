#!/usr/bin/env python3

# Sanakirja.org CLI tool
HELP = """Terminal dictionary
Uses Sanakirja.org as a source which in turn is based on Wiktionary

Usage: 
translator <from_language> <to_language> <word> <options>

Options:
-l --list           List available languages
-v --verbose        Print long version
-s --synonymes      Print synonymes for the words
-d --definitions    Print definitions for the words
-n --limit          Limit the number of translations retrieved
-h --help           Display this info
-r --raw            Only print the translations, nothing else
"""


import sys
import bs4 as bs
from urllib.request import urlopen
from urllib.parse import quote_plus

# Languages and their abbreviations
LANGUAGES = {
    "bu":   ("bulgarian", 1),
    "en":   ("english", 3),
    "sp":   ("spanish", 4),
    "esp":  ("esperanto", 5),
    "du":   ("dutch", 23),
    "it":   ("italian", 6),
    "jap":  ("japanese", 24),
    "gr":   ("greek", 7),
    "lat":  ("latin", 8),
    "latv": ("latvian", 9),
    "lit":  ("lithuanian", 10),
    "nor":  ("norwegian", 11),
    "por":  ("portugese", 12),
    "pol":  ("polish", 13),
    "fr":   ("french", 14),
    "swe":  ("swedish", 15),
    "ger":  ("german", 16),
    "fi":   ("finnish", 17),
    "dan":  ("danish", 18),
    "tur":  ("turkish", 20),
    "cze":  ("czech", 19),
    "hun":  ("hungarian", 21),
    "rus":  ("russian", 22),
    "es":   ("estonian", 2),
}

# Query URL
URL = "http://www.sanakirja.org/search.php?q=@Word&l=@Lang1&l2=@Lang2"


# Return True if argument is present in short or long form
def __get_argument_pos(arguments, short, long):
    for ind, argument in enumerate(arguments):
        argument = str(argument)
        if not argument.startswith("-"):
            continue
        if argument.startswith("--"):
            argument = argument[2:]
            return True if long == argument else -1
        argument = argument[1:]
        if (short in list(argument)):
            return ind
    return -1

def __get_argument(arguments, short, long):
    return __get_argument_pos(arguments, short, long) >= 0

# Print error and exit
def __pexit(msg):
    print(str(msg))
    exit()


# Application entry point
if __name__ == "__main__":
    # Read CL arguments
    args = sys.argv[1:]

    PARAM_VERBOSE =     __get_argument(args, "v", "verbose")
    PARAM_LIMIT =       __get_argument(args, "n", "limit")
    PARAM_SYNONYMES =   __get_argument(args, "s", "synonymes")
    PARAM_DEFINITIONS = __get_argument(args, "d", "definitions")
    PARAM_LANGUAGES =   __get_argument(args, "l", "list")
    PARAM_HELP =        __get_argument(args, "h", "help")
    PARAM_RAW =         __get_argument(args, "r", "raw")

    if PARAM_LIMIT:
        try:
            PARAM_LIMIT_NUMBER = int(args[__get_argument_pos(args, "n", "limit") + 1])
        except Exception:
            __pexit("Limit is missing")

    if PARAM_HELP:
        __pexit(HELP)

    if PARAM_LANGUAGES:
        print("Available languages:")
        print("Short\tLong\n")
        for k, v in LANGUAGES.items():
            print("{}\t{}".format(k, v))
        exit()

    # Extract non-flag arguments
    __args = [a for a in args if not a.startswith("-")]

    if len(__args) < 3:
        __pexit("Missing some required arguments")

    PARAM_FROM_LANG = __args[0]
    PARAM_TO_LANG   = __args[1]
    PARAM_WORD      = __args[2]

    if PARAM_FROM_LANG == PARAM_TO_LANG:
        __pexit("Languages cannot be the same")

    # Validate languages
    all_langs = list(LANGUAGES.keys()) + [first for first, second in list(LANGUAGES.values())]
    if PARAM_FROM_LANG not in all_langs:
        __pexit("FROM language is invalid")
    if PARAM_TO_LANG not in all_langs:
        __pexit("TO language is invalid")

    FROM_LANG_INDEX = LANGUAGES[PARAM_FROM_LANG][1]
    TO_LANG_INDEX   = LANGUAGES[PARAM_TO_LANG][1]
    FROM_LANG_NAME  = LANGUAGES[PARAM_FROM_LANG][0]
    TO_LANG_NAME    = LANGUAGES[PARAM_TO_LANG][0]

    # Validate word
    if not len(PARAM_WORD) > 0:
        __pexit("Invalid word")

    # Do HTTP query
    __request_url = URL.replace("@Lang1", str(FROM_LANG_INDEX)).replace("@Lang2", str(TO_LANG_INDEX)).replace("@Word", quote_plus(PARAM_WORD))
    try:
        __page_content = urlopen(__request_url)
    except IOError:
        __pexit("Timeout")
    
    # Create HTML soup
    soup = bs.BeautifulSoup(__page_content, "html.parser")
    
    elem_translations = soup.select(".content > table.translations tr[class^=sk] > td > a")
    if len(elem_translations) == 0:
        __pexit("No translations found for `{}` from `{}` to `{}`".format(PARAM_WORD, FROM_LANG_NAME, TO_LANG_NAME))
    
    translations = [t.text.strip() for t in elem_translations]
    if PARAM_LIMIT:
        translations = translations[0:PARAM_LIMIT_NUMBER]

    # Print translations
    if not PARAM_RAW:
        print("Translations:")
    if PARAM_VERBOSE:
        for i, t in enumerate(translations):
            print("{}:\t{}".format(i, t))
    else:
        print(", ".join(translations))

    if PARAM_RAW:
        exit()
    
    # Print synonymes if needed
    if PARAM_SYNONYMES:
        elem_synonymes = soup.select(".content > .lists > .synonyms > ul > li > a")
        synonymes = [t.text.strip() for t in elem_synonymes]
        if len(synonymes) > 0:
            print("\nSynonymes:")
            if PARAM_VERBOSE:
                for i, s in enumerate(synonymes):
                    print("{}:\t{}".format(i, s))
            else:
                print(", ".join(synonymes))
    
    # Print definitions if needed
    if PARAM_DEFINITIONS:
        elem_definitions = soup.select(".content > .definitions > ol > li")
        definitions = [t.text.strip() for t in elem_definitions]
        if len(definitions) > 0:
            print("\nDefinitions:")
            if PARAM_VERBOSE:
                for i, d in enumerate(definitions):
                    print("{}:\t{}".format(i, d))
            else:
                for d in definitions:
                    print(d)