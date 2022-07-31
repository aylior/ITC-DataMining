import requests
from bs4 import BeautifulSoup
import json
import csv
import db_creation as db


def parser_initializer(url):
    """ This function initialize the parser, it takes as argument :
        - URL """
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        return soup

    except ConnectionError:
        print("We didn't succeed to parse your link")


def get_nb_page_review(parser):
    """ This function returns the number of reviewing pages it takes as argument :
        - parser """

    last_page = int(parser.find('a', {'name': 'pagination-button-last'}).text)
    return last_page


def get_list_of_pages(website, page_nb):
    """ This function returns the list of links from a given website and given number of pages to check """

    page_parameter = '&page='
    list_page = []

    for i in range(1, page_nb + 1):
        list_page.append(website + page_parameter + str(i))

    return list_page


def get_page_content(parser):
    """ This function is parsing the website, it takes 2 parameters:
        - URL
        - Main element class
    """
    widgets = parser.find('section', class_='styles_reviewsContainer__3_GQw')
    return widgets


def get_url_websites(json_file):
    """ Dictionary Initialization"""
    main_dic = {}

    header = ['category_name', 'business', 'business_url', 'user_name', 'user_country', 'score', 'review_title', 'text',
              'review_date', 'url']

    with open('export.csv', 'a') as p:
        writer = csv.writer(p)
        writer.writerow(header)
        p.close()

    """ Parsing JSON file """
    with open(json_file, 'r') as f:
        data = json.load(f)

        """ Categories """
        for a in data:
            category_name = list(a.keys())[0]

            """ Categories - Values """
            for b in a.values():

                """ Business - Values """
                for e in b['businesses'].values():
                    name = e['name']
                    url = e['url'] + '?languages=all'

                    parser = parser_initializer(url)
                    page_nb = get_nb_page_review(parser)
                    list_page = get_list_of_pages(url, page_nb)

                    """ Business - Page_Content """
                    for page in list_page:
                        parser = parser_initializer(page)
                        widgets = get_page_content(parser)

                        """ Business - Page_Content """
                        for article in widgets.find_all('article'):

                            try:
                                country = article.find('span', {
                                    'class': 'typography_typography__QgicV typography_weight-inherit__iX6Fc typography_fontstyle-inherit__ly_HV'}).text

                            except AttributeError:
                                country = 'None'

                            try:
                                text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p

                                if text is not None:
                                    text = text.text
                                else:
                                    text = 'None'

                            except AttributeError:
                                text = 'None'

                            try:
                                score = article.img['alt']

                                if score is not None:
                                    score = article.img['alt']
                                else:
                                    score = 'None'

                            except AttributeError:
                                score = 'None'

                            main_dic = {'category_name': category_name,
                                        'business': name,
                                        'business_url': url,
                                        'user_name': article.a.div.text,
                                        'user_country': country,
                                        'score': article.img['alt'],
                                        'review_title': article.h2.text.replace('…', ''),
                                        'text': article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p,
                                        'review_date': list(article.time.attrs.values())[0].split('T')[0],
                                        'url': 'https://www.trustpilot.com' +
                                               article.section.find('div', {'styles_reviewContent__0Q2Tg'}).h2.a['href']
                                        }

                            category_name = main_dic['category_name']
                            business = main_dic['business']
                            business_url = main_dic['business_url']
                            user_name = main_dic['user_name']
                            user_country = main_dic['user_country']
                            score = main_dic['score']
                            review_title = main_dic['review_title']
                            text = main_dic['text']
                            review_date = main_dic['review_date']
                            url = main_dic['url']

                            nlist = [category_name, business, business_url, user_name, user_country, score,
                                     review_title, text, review_date, url]
                            print(nlist)

                            with open('export.csv', 'a') as f:
                                writer = csv.writer(f)
                                writer.writerow(nlist)

def main():
    get_url_websites('ml1_test_2.json')
    db.database_creation()


if __name__ == "__main__":
    main()
