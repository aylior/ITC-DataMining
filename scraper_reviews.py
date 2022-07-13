import requests
from bs4 import BeautifulSoup
import json




# TODO: Limit the results by page or value. #Improve
# TODO: Use Grequest, to improve speed.
# TODO: Solve the text issues, review without text, how to count them properly and return NONE if it doesn't exist.
# TODO: Review with unique id or page_id.
# TODO: Page number not relevant or not.
# TODO: Create JSON file and put text #Done
# TODO: Remove special character.
# TODO: Parse CONFIG.
# TODO: Generate stats JSON file

def get_url_websites(json_file):
    website_list = []

    with open(json_file, 'r') as f:
        data = json.load(f)

        for a in data:
            for b in a.values():
                for e in b['businesses'].values():
                    website_list.append(e['url'])

    return website_list


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

    page_parameter = '?page='
    list_page = []

    for i in range(1, page_nb + 1):
        list_page.append(website + page_parameter + str(i)+ '?languages=all')

    return list_page


def get_page_content(parser, global_tag):
    """ This function is parsing the website, it takes 2 parameters:
        - URL
        - Main element class
    """
    widgets = parser.find('div', class_=global_tag)
    return widgets


def element_parsing(widgets):
    """ This function collect details about user reviews like :
        - User_name
        - User_nb_reviews
        - User_country
        - review_title
        - review_date
        - review_rating
    """

    dict_test = {}
    user_id = 0

    for e in widgets.find_all('article'):
        user_id += 1

        try:
            country = e.find('span', {
                'class': 'typography_typography__QgicV typography_weight-inherit__iX6Fc typography_fontstyle-inherit__ly_HV'}).text

        except AttributeError:
            country = 'None'

        #
        # try:
        #     rating = list(e.section.div.div.img.attrs.values())[0].split(' ')[1]
        #
        # except AttributeError:
        #     rating = 'None'

        dict_test[user_id] = {'user_name': e.a.div.text,
                              # 'user_nb_reviews': e.span.text.split()[0],
                              'user_country': country,
                              'review_title': e.h2.text.replace('…', ''),
                              'review_date': list(e.time.attrs.values())[0].split('T')[0],
                              # 'review_rating': rating

                              #
                              # 'user_review': e.find('p', {
                              #     'class': 'typography_typography__QgicV typography_body__9UBeQ typography_color-black__5LYEn typography_weight-regular__TWEnf typography_fontstyle-normal__kHyN3'}).text
                              }
    return dict_test


def get_all_reviews(page_list):
    """ This function returns a dictionary including all the reviews details from the given link list"""
    main_dictionary = {}
    PAGE_COUNT = 0

    CLASS_TO_PARSE = 'styles_mainContent__nFxAv'

    for link in page_list:
        PAGE_COUNT += 1
        index_text = 'page_' + str(PAGE_COUNT)
        soup = parser_initializer(link)
        widgets = get_page_content(soup, CLASS_TO_PARSE)
        main_dictionary[index_text] = element_parsing(widgets)

    return main_dictionary


def export_to_json(dictionary, file_name):
    """ This function convert a dictionary into a JSON file, it takes 2 parameters :
        - Dictionary
        - Expected indentation
    """

    try:
        with open(file_name, 'a+') as f:
            f.write(json.dumps(dictionary, indent=4))


    except FileExistsError:
        print('Your file has not been created')


def read_from_json():

    with open('data.json', 'r') as f:
        data = json.load(f)

        lg = len(data)

        for i in range(lg):
            key = list(data[i].keys())[0]

            for k in dict(data[i]).get(key).get('businesses').keys():
                website = dict(data[i]).get(key).get('businesses').get(k).get("url")

            """ parser initilization"""
            soup = parser_initializer(website)

            """ page number """
            page_nb = get_nb_page_review(soup)

            """ get all pages in list """
            all_pages = get_list_of_pages(website, page_nb)

            """ get all reviews """
            reviews = get_all_reviews(all_pages)

            """ export dictionary to json file """
            json_file = export_to_json(reviews, 'reviews.json')

            print('EXPORTED :', reviews)


def main():

    read_from_json()


if __name__ == "__main__":
    main()
