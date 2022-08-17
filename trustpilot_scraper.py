import time
import grequests
import requests
from bs4 import BeautifulSoup
import scraper_reviews as sr

import tp_config    
import tp_db
import tp_logger

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


CFG = tp_config.CFG

logger = tp_logger.get_logger()


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


def scrape_pages(num_of_pages, category, initial_response):
    """
    scrape pages of businesses in the category async and insert them to DB when done.
    :param num_of_pages: number of pages to scrape. defined in the configuration file.
                         if 'All' - the nuber is taken from the first page pagination
    :param category: the category its pages we currently scrape. used for building the Business object
    :param initial_response: used for determine the number of pages from the category fist page
    :return category business from scraping
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
    return category_businesses




def scrape_category(category):
    """ get the businesses cards for each category pages as defined in configuration, and insert to the DB."""
    logger.info("Getting businesses from categories")
    logger.info(f"Start scraping {category.name} at {category.url}")
    # get the number of pages from the first page by parsing pagination
    response = requests.get(category.url)
    if CFG['Site']['Pages'] == ALL_PAGES:
        num_of_pages = get_num_of_pages(response, category)
    else:
        num_of_pages = CFG['Site']['Pages']

    return num_of_pages, response

def insert_category_to_db(category):
    """write the category to DB"""
    tp_db.db_cat_insert(category)
    # Use the id of the category as assigned by DB
    query = f'SELECT category_id FROM Category WHERE name = "{category.name}";'
    category_id = tp_db.exec_query(query)[0][0]
    category.id = category_id
    return category


def main():
    start_time = time.time()
    logger.info("Starting...")
    # Drop DB and create again according to config and CLI argument if exists.
    tp_db.drop_db_with_create()
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
    i = 0
    while i < len(categories_links):
        num_of_pages, response = scrape_category(categories_links[i])
        category = insert_category_to_db(categories_links[i])
        category_businesses = scrape_pages(num_of_pages, category, response)
        tp_db.db_businesses_insert(category, category_businesses)
        logger.info(f"Request for {category.name}: Finished successfully.")

        i += 1
    end_time = time.time()
    logger.info(f"Running Time: for scraping category:{CFG['Site']['Category']}, pages:{CFG['Site']['Pages']} "
                f"took: {end_time - start_time} seconds")

    sr.main(CFG, logger)

    tp_db.cursor.close()


if __name__ == "__main__":
    main()
