import argparse
import logging
import time
import grequests
import requests
import json
from bs4 import BeautifulSoup
import pymysql
import scraper_reviews as sr

CONFIG = 'config.json'
SQL_ARCH = "fill_db.sql"
ALL_PAGES = 'All'
ALL_CATEGORIES = 'All'
CATEGORY_URL_ATTR = "href"
TAG_URL_ATTR = "href"
REVIEWS_DELIM = "|"
REVIEWS_PREFIX = " reviews"
CATEGORY_CONTAINER_CLASS = "styles_headingLink__3ESdh"
PAGINATION_ATTR = "data-pagination-button-last-link"
BUSINESS_CARD_ATTR = "data-business-unit-card-link"
SCORE_PREFIX = "TrustScore "
CONFIG_ARG = "--conf"


class Category:
    def __init__(self, cat_id, name, url):
        """ A Class holding category name and url as scraped from website"""
        self.id = cat_id
        self.name = name
        self.url = url


class Business:
    def __init__(self, url, score, name, category, reviews):
        """
        A class holding the business details from its card i the category page.
        :param url: url of the actual business page in the site
        :param score: the rank of the business according to the website ranking system
        :param name: business name
        :param category: the main category it belongs to (not the sub category)
        :param reviews: number of reviews given by users
        """
        self.url = url
        self.score = score
        self.name = name
        self.category = category
        self.reviews = reviews

    def __str__(self):
        """ define the printing format of the business"""
        return f"Name: {self.name} | category: {self.category} | score: {self.score} | url: {self.url}"


def load_configuration():
    """ load the json configuration file"""
    with open(CONFIG) as f:
        return json.load(f)


def get_logger():
    """
    Set a logger and return it after set up. The logger will log to a file and to the stdout.
    :return: logger: the logging object for logging to log file and console.
    """
    # create log
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    # create file handler and set level according to configuration. Writing mode is 'w' instead of 'a'
    # so there is no need to delete log file each run.
    fh = logging.FileHandler(CFG["Log"]["Log_File"], mode="w")
    ch = logging.StreamHandler()
    fh.setLevel(CFG["Log"]["File_Log_Level"])
    ch.setLevel(CFG["Log"]["Console_Log_Level"])
    # create formatter
    formatter = logging.Formatter(CFG["Log"]["Log_Format"])
    # add formatter to the handlers handler
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add handlers to log
    log.addHandler(ch)
    log.addHandler(fh)
    return log


CFG = load_configuration()


def read_cli():
    """ CLI for different arguments that override the arguments in the config file."""
    parser = argparse.ArgumentParser(description='TrustPilot Scraper')
    parser.add_argument("-c", type=str, help="Category name to parse or 'All'")
    parser.add_argument("-p", type=int, help="Number of category pages to scrape or 'All.")
    parser.add_argument("-lf", type=str, help="Log level for log file (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
                                              "default: INFO")
    parser.add_argument("-lc", type=str, help="Log level for log to console (DEBUG, INFO, WARNING, ERROR, CRITICAL). "
                                              "default: INFO")
    parser.add_argument("-user", type=str, help="DB user name. default: root.")
    parser.add_argument("-pwd", type=str, help="DB user password. No Default!.")
    parser.add_argument("-hst", type=str, help="DB host. default: localhost")
    parser.add_argument("-cd", type=str, choices={"Y", "N"},
                        help="Drop DB and create again before start scraping (Y/N). default: 'N'")

    args = parser.parse_args()
    if args.c:
        CFG['Site']['Category'] = args.c
    if args.p:
        CFG['Site']['Pages'] = args.p
    if args.lf:
        CFG['Log']["File_Log_Level"] = args.lf
    if args.lc:
        CFG['Log']["Console_Log_Level"] = args.lc
    if args.user:
        CFG['DB']['User'] = args.user
    if args.pwd:
        CFG['DB']['Password'] = args.pwd
    if args.hst:
        CFG['DB']['Host'] = args.hst
    if args.cd:
        CFG['DB']['Create_db'] = args.cd


# Read arguments from CLI
read_cli()

logger = get_logger()


# connect to DB
def connect_db():
    """
    Create connection to DB. Loading connection parameters from config.
    :return: conn, cursor
    """
    try:
        conn = pymysql.connect(host=CFG["DB"]["Host"],
                               user=CFG["DB"]["User"],
                               password=CFG["DB"]["Password"])
        return conn, conn.cursor()
    except pymysql.err.OperationalError:
        logger.critical(f"Can not connect to {CFG['DB']['DB_Name']}. user or password may be incorrect.")
        exit()


connection, cursor = connect_db()


def drop_db_with_create():
    """ Drop the DB and create again according to CLI argument. default value is 'N' in config file."""
    if CFG['DB']['Create_db'] == "Y":
        create_db = True
    else:
        create_db = False
    if create_db:
        with open(CFG['DB']['Create_db_file']) as f:
            queries = "".join(f.readlines())
            queries = queries.split(";")
            for query in queries:
                query = query.replace('\n', "")
                if len(query) > 0:
                    query = query + ';'
                    exec_query(query)


def extract_categories(response):
    """
    extract the categories list of urls and modify every url to be absolute
    :param response: response from the website categories page
    :return: categories_lst: the list of  category object containing category name and absolute url.
    """
    logger.info(f"Extracting {CFG['Site']['Category']} category.")
    # Create BeautifulSoup object to parse the html page in the response from the website.
    soup = BeautifulSoup(response.text, CFG['Parser']['BS_Parser_Name'])
    # Find the lower container tag that hold the relevant data, filtered by its class
    container_lst = soup.find_all("a", class_=CATEGORY_CONTAINER_CLASS,
                                  href=lambda x: str(x).startswith(CFG['Site']['Categories_Page']))
    # get only the category defined in the configuration
    if CFG['Site']['Category'] != ALL_CATEGORIES:
        container_lst = [a for a in container_lst if a.h2.text == CFG['Site']['Category']]
    categories_lst = []
    for index, a in enumerate(container_lst, 1):
        category_url = a[CATEGORY_URL_ATTR]
        category_name = a.h2.text
        url = CFG['Site']['Domain'] + category_url + CFG['Site']['Filters']
        categories_lst.append(Category(index, category_name, url))
    return categories_lst


def db_cat_insert(category):
    query = f'INSERT INTO Category (name, url) VALUES ("{category.name}", "{category.url}");'
    exec_query(query)


def dump_close_category():
    """ write to the data file the json closing of the category """
    with open(CFG['Json']['File'], 'a') as f:
        f.write('}}')


def dump_to_file(business_lst):
    """ write to the data file the businesses of the category as dictionary"""
    business_dict = dict()
    if len(business_lst) == 0:
        dump_close_category()
        return
    for business in business_lst:
        business_dict.update({business.name: {"name": business.name,
                                              "url": business.url,
                                              "score": business.score,
                                              "review": business.reviews}})
    with open(CFG['Json']['File'], 'a') as f:
        json.dump(business_dict, f, indent=8)


def get_num_of_pages(response, category):
    """
    return the number of pages in the category according to the filters applied on the for all categories.
    the number is the number of pages exists for the category after filtered. the number of how many pages
    to scrape defined in the configuration file.
    """
    soup = BeautifulSoup(response.text, CFG['Parser']['BS_Parser_Name'])
    try:
        num_of_pages = soup.find("a", {PAGINATION_ATTR: "true"}).text
    except AttributeError:
        logger.warning(f"Can not find pagination for {category.name} at {category.url}. setting number to default.")
        if CFG['Site']['Pages'] == ALL_PAGES:
            num_of_pages = CFG['Site']['DEFAULT_NUM_PAGES']
        else:
            num_of_pages = CFG['Site']['Pages']
    return int(num_of_pages)


def businesses_cards(responses, category):
    """ build the business objects according to the business cards in the category pages. """
    category_businesses = []
    for response in responses:
        try:
            soup = BeautifulSoup(response.text, CFG['Parser']['BS_Parser_Name'])
            tags_lst = soup.find_all("a", {BUSINESS_CARD_ATTR: "true"})
        except AttributeError:
            logger.warning(f"Request for {category.name}: page:{category.url[category.url.rfind('=') + 1:]}:"
                           f" Page might be offline.")
            continue
        for tag in tags_lst:
            url = CFG['Site']['Domain'] + tag[TAG_URL_ATTR]
            b_category = category.name
            b_name = tag.text[:tag.text.find(SCORE_PREFIX)]
            reviews = tag.text[tag.text.rfind(REVIEWS_DELIM) + 1:]
            try:
                reviews = int(reviews.replace(REVIEWS_PREFIX, "").replace(",", ""))
            except ValueError:
                logger.warning(f"Business {b_name} has no score (might be 0.0). skipping...")
                continue

            if reviews < CFG['Site']['Min_Reviews_Num']:
                continue
            score = tag.text[tag.text.find(SCORE_PREFIX):tag.text.rfind(REVIEWS_DELIM)]
            score = score.replace(SCORE_PREFIX, "")
            logger.debug(f"scraped {b_name}|{category.name}|{score}|{url}")
            try:
                score = float(score)
            except ValueError:
                logger.warning(f"Business {b_name} has no score (might be 0.0). skipping...")
                continue

            category_businesses.append(Business(url, score, b_name, b_category, reviews))
    return category_businesses


def get_businesses_cards_from_url(category_pages_urls, category):
    """
    send a batch requests for scraping category pages in parallel. the responses are used to
    create a Business object for each business in the category.
    """
    # Build the requests list by listing all movies urls
    request_list = [grequests.get(url, timeout=10) for url in category_pages_urls]
    # Execute the listed requests using map
    responses = grequests.map(request_list)
    businesses_cards_lst = businesses_cards(responses, category)
    return businesses_cards_lst


def db_businesses_insert(category, business_lst):
    """ Insert the businesses of the category to the DB """
    if len(business_lst) == 0:
        return
    for business in business_lst:
        business.name = business.name.replace('"', "'")
        query = f'INSERT INTO Business (category_id, name, url, score, reviews) VALUES ({category.id}, ' \
                f'"{business.name}", "{business.url}", {business.score}, {business.reviews});'
        exec_query(query)


def scrape_and_insert_pages(num_of_pages, category, initial_response):
    """
    scrape pages of businesses in the category async and insert them to DB when done.
    :param num_of_pages: number of pages to scrape. defined in the configuration file.
                         if 'All' - the nuber is taken from the first page pagination
    :param category: the category its pages we currently scrape. used for building the Business object
    :param initial_response: used for determine the number of pages from the category fist page
    """
    # hold the business cards from the category pages
    category_businesses = []
    # List of url's to scrape async
    category_pages_urls = []
    page_num = 1
    while page_num < (num_of_pages + 1):
        # get the business cards from the current category pages
        category_businesses += businesses_cards([initial_response], category)
        page_num += 1
        # Create the url of the next page of the category
        category.url = category.url[:category.url.rfind("=") + 1] + str(page_num)
        category_pages_urls.append(category.url)
        # send a batch of category pages to be scraped async
        if page_num % CFG['Requests']['Batch_Size'] == 0 or page_num == num_of_pages:
            category_businesses += get_businesses_cards_from_url(category_pages_urls, category)
            category_pages_urls = []
            logger.info(f"Scraped {page_num} pages from {category.name}")
    db_businesses_insert(category, category_businesses)


def get_businesses_from_categories(categories):
    """ get the businesses cards for each category pages as defined in configuration, and insert to the DB."""
    logger.info("Getting businesses from categories")
    # writing the opening tag for the json data file
    with open(CFG['Json']['File'], 'w') as f:
        f.write("[")
    i = 0
    while i < len(categories):
        category = categories[i]
        logger.info(f"Start scraping {category.name} at {category.url}")
        # get the number of pages from the first page by parsing pagination
        response = requests.get(category.url)
        if CFG['Site']['Pages'] == ALL_PAGES:
            num_of_pages = get_num_of_pages(response, category)
        else:
            num_of_pages = CFG['Site']['Pages']
        # write the category to DB
        db_cat_insert(category)
        # Use the id of the category as assigned by DB
        query = f'SELECT category_id FROM Category WHERE name = "{category.name}";'
        category_id = exec_query(query)[0][0]
        category.id = category_id
        # scrape category pages
        scrape_and_insert_pages(num_of_pages, category, response)
        logger.info(f"Request for {category.name}: Finished successfully.")
        i += 1


def keep_sql(query):
    """ Keep queries except of SELECT to sql file for reconstruct DB if needed. """
    if not query.lower().startswith("select"):
        query = query + '\n'
        if not query.startswith("DROP DATABASE"):
            with open(SQL_ARCH, 'ab') as f:
                f.write(query.encode('utf8'))
        else:
            with open(SQL_ARCH, 'wb') as f:
                f.write(query.encode('utf8'))


def exec_query(query):
    """ Execute single query. Return results if any."""
    keep_sql(query)
    if not query.lower().startswith("drop database") and not query.lower().startswith("create database") and \
            not query.lower().startswith("use"):
        cursor.execute(f'USE {CFG["DB"]["DB_Name"]};')
    cursor.execute(query)
    if not query.lower().startswith("select"):
        connection.commit()
    fetched = cursor.fetchall()
    return fetched


def main():
    start_time = time.time()
    logger.info("Starting...")
    # Drop DB and create again according to config and CLI argument if exists.
    drop_db_with_create()
    # Website categories main page.
    url = f"{CFG['Site']['Domain']}{CFG['Site']['Categories_Page']}"
    try:
        response = requests.get(url)
    except Exception:
        logger.critical(f"Can not connect to {CFG['Site']['Domain']}{CFG['Site']['Categories_Page']}")
        return
    # get the categories list from the categories page of the website.
    categories_links = extract_categories(response)
    # scrape businesses from the categories in the list and write them to the DB.
    get_businesses_from_categories(categories_links)
    end_time = time.time()
    logger.info(f"Running Time: for scraping category:{CFG['Site']['Category']}, pages:{CFG['Site']['Pages']} "
                f"took: {end_time - start_time} seconds")

    # sr.read_from_json()
    connection.close()


if __name__ == "__main__":
    main()
