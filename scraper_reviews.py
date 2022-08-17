import requests
from bs4 import BeautifulSoup
import pymysql
import logging

""" DATABASE LOGIN ----------> REPLACE WITH ClI """
HOST = "localhost"
USER = "root"
PASSWORD = 'rootroot'
DB_NAME = "trust_pilot"

# HOST = CFG['DB']['Host']
# USER = CFG['DB']['User']
# PASSWORD = CFG['DB']['Password']
# DB_NAME = "trust_pilot"

""" TEST CONSTANT ----------> REPLACE WITH ClI """
CATEGORY = 'Animals & Pets'
COMPANY = 'Choice Mutual'


# CATEGORY = ['Site']['Category']
# COMPANY = ['Site']['Company']

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
    try:
        last_page = int(parser.find('a', {'name': 'pagination-button-last'}).text)

        if last_page is not None:
            last_page = int(parser.find('a', {'name': 'pagination-button-last'}).text)
            return last_page

        else:
            pass

    except AttributeError:
        pass


def get_list_of_pages(website, page_nb):
    """ This function returns the list of links from a given website and given number of pages to check """

    page_parameter = '?page='
    list_page = []

    try:
        for i in range(1, page_nb + 1):
            list_page.append(website + page_parameter + str(i))

        return list_page

    except TypeError:
        pass


def get_page_content(parser):
    """ This function is parsing the website, it takes 2 parameters:
        - URL
    """
    widgets = parser.find('section', class_='styles_reviewsContainer__3_GQw')
    return widgets


def connect_db():
    """
    Create connection to DB. Loading connection parameters from config.
    :return: conn, cursor
    """
    try:
        # conn = pymysql.connect(host=CFG["DB"]["Host"],
        #                        user=CFG["DB"]["User"],
        #                        password=CFG["DB"]["Password"])

        conn = pymysql.connect(host='localhost',
                               user='root',
                               password='rootroot')

        return conn, conn.cursor()
    except pymysql.err.OperationalError:
        # logger.critical(f"Can not connect to database. user or password may be incorrect.")
        exit()


def database_creation():
    """ DATABASE INITIALIZATION """
    connection, cursor = connect_db()

    with open('fill_db.sql', 'r', encoding='utf-8') as p:
        sqlFile = p.read()
        p.close()
        sqlCommands = sqlFile.split(';')

        for command in sqlCommands:
            try:
                if command.strip() != '':
                    cursor.execute(command)
            except IOError:
                print("Command skipped: ")

    cursor.execute(f'USE trust_pilot;')


def get_reviews_data(list_page):
    """ Dictionary Initialization"""
    main_dic = {}

    for page in list_page:
        parser = parser_initializer(page)
        widgets = get_page_content(parser)

        """ Business - Page_Content """
        for article in widgets.find_all('article'):

            """ Try country """
            try:
                country = article.find('span', {
                    'class': 'typography_typography__QgicV typography_weight-inherit__iX6Fc typography_fontstyle-inherit__ly_HV'}).text
            except AttributeError:
                country = 'None'
                # logger.warning(f"Can not find country. setting number to default.")

            """ Try score """
            try:

                score = article.find('div', {'styles_reviewHeader__iU9Px'}).attrs.values()

                if score is not None:
                    score = list(article.find('div', {'styles_reviewHeader__iU9Px'}).attrs.values())[1]
                else:
                    score = 'None'
            except IndexError:
                score = 'None'
                # logger.warning(f"Can not find score. setting number to default.")

            """ Try text """
            try:
                text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p.text

                if text is not None:
                    text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p.text

                    if len(text) < 250:
                        text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p.text

                    else:
                        text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p.text[:250] + '...'

                else:
                    text = 'None'
            except AttributeError:
                text = 'None'
                # logger.warning(f"Can not find text. setting number to default.")

            """ Try user name """
            try:
                user_name = article.a.div.text

                if user_name is not None:
                    user_name = article.a.div.text
                else:
                    user_name = 'None'
            except AttributeError:
                user_name = 'None'
                # logger.warning(f"Can not find user_name. setting number to default.")

            """ Try review title """
            try:
                review_title = article.h2.text.replace('…', '')

                if review_title is not None:
                    review_title = article.h2.text.replace('…', '')
                else:
                    review_title = 'None'
            except AttributeError:
                review_title = 'None'
                # logger.warning(f"Can not find review_title. setting number to default.")

            """ Try review date """
            try:
                review_date = list(article.time.attrs.values())[0].split('T')[0]

                if review_date is not None:
                    review_date = list(article.time.attrs.values())[0].split('T')[0]
                else:
                    review_date = 'None'
            except AttributeError:
                review_date = 'None'
                # logger.warning(f"Can not find review_date. setting number to default.")

            # business_url = e['url']

            url = 'https://www.trustpilot.com' + \
                  article.section.find('div', {'styles_reviewContent__0Q2Tg'}).h2.a['href']

            main_dic = {
                'user_name': user_name,
                'user_country': country,
                'score': score,
                'review_title': review_title,
                'text': text,
                'review_date': review_date,
                'url': url
            }

            user_name = main_dic['user_name']
            user_country = main_dic['user_country']
            score = main_dic['score']
            review_title = main_dic['review_title']
            text = main_dic['text']
            review_date = main_dic['review_date']
            url = main_dic['url']

            connection, cursor = connect_db()

            """ DATABASE SELECTION """
            cursor.execute('USE trust_pilot')

            """ USER_DETAILS """
            cursor.execute('''INSERT INTO User_details (
                                                user_name,
                                                user_location)
                                                VALUES (%s, %s)''', (user_name, user_country))

            userID = cursor.lastrowid

            """ REVIEW """
            cursor.execute('''INSERT INTO Review (
                                                user_id,
                                                score,
                                                url,
                                                review_date)
                             VALUES (%s, %s, %s, %s)''', (userID, score, url, review_date))

            reviewID = cursor.lastrowid

            """ TEXT """
            cursor.execute('''INSERT INTO Review_text (
                                                review_id,
                                                title,
                                                text)
                             VALUES (%s, %s, %s)''', (reviewID, review_title, text))

            connection.commit()


def main():
    """ Database connection """
    connection, cursor = connect_db()

    """ Database creation """
    with open('fill_db.sql', 'r', encoding='utf-8') as p:
        sqlFile = p.read()
        p.close()
        sqlCommands = sqlFile.split(';')

        for command in sqlCommands:
            try:
                if command.strip() != '':
                    cursor.execute(command)
            except IOError:
                print("Command skipped: ")

    cursor.execute(f'USE trust_pilot;')

    with connection.cursor() as cursor:
        sql = f"""SELECT B.url 
                  FROM Business AS B 
                  lEFT JOIN Category AS C 
                  ON B.category_id = C.category_id WHERE C.name ='{CATEGORY}'"""
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            row = row[0]
            parser = parser_initializer(row)
            page_nb = get_nb_page_review(parser)
            list_page = get_list_of_pages(row, page_nb)
            get_reviews_data(list_page)

    connection, cursor = connect_db()
    cursor.execute(f'USE trust_pilot;')

    """ SELECT TEXT FROM REVIEWS """
    with connection.cursor() as cursor:
        sql = """SELECT review_id, text 
                 FROM Review_text"""

        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            """ API - TRANSFORM TEXT TO SENTIMENT """
            url = "https://text-analysis12.p.rapidapi.com/sentiment-analysis/api/v1.1"

            payload = {
                "language": "english",
                "text": row[1]
            }
            headers = {
                "content-type": "application/json",
                "X-RapidAPI-Key": "108eb78b3cmsh21151a085f69b46p1ad84bjsnf3a18264468f",
                "X-RapidAPI-Host": "text-analysis12.p.rapidapi.com"
            }

            response = requests.request("POST", url, json=payload, headers=headers)

            neg = round(float(response.text.split('{')[2].split(',')[0].split(':')[1]), 2)
            neu = round(float(response.text.split('{')[2].split(',')[1].split(':')[1]), 2)
            pos = round(float(response.text.split('{')[2].split(',')[2].split(':')[1]), 2)

            """ API - INSERT SENTIMENT TO THE DATABASE """
            cursor.execute('''INSERT INTO Review_sentiment (
                                                    positive,
                                                    neutral,
                                                    negative)
                             VALUES (%s, %s, %s)''', (neg, neu, pos))

            connection.commit()

    """ API - SELECT SENTIMENT FROM THE DATABASE """
    connection, cursor = connect_db()
    cursor.execute(f'USE trust_pilot;')

    with connection.cursor() as cursor:
        sql = """SELECT S.review_id, positive, neutral, negative, text FROM Review_sentiment AS S LEFT JOIN Review_text AS T ON S.review_id = T.review_id"""

        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            print(row)


if __name__ == "__main__":
    main()
