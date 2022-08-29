import requests
from bs4 import BeautifulSoup
import pymysql
import json

import tp_config
import tp_db
import tp_logger

# TODO: Solve issue with matching between categories, business and the the rest of tables.
# TODO: Implement's Lior's CLI.
# TODO: Implement's Lior's Logger.

CFG = tp_config.CFG
logger = tp_logger.get_logger()

""" DATABASE LOGIN ----------> (REPLACE WITH ClI DATA) """
# HOST = "localhost"
# USER = "root"
# PASSWORD = 'rootroot'
# DB_NAME = "trust_pilot"

HOST = CFG['DB']['Host']
USER = CFG['DB']['User']
PASSWORD = CFG['DB']['Password']
DB_NAME = CFG['DB']['DB_Name']

""" TEST CONSTANT ----------> (REPLACE WITH ClI DATA) """
# CATEGORY = 'Animals & Pets'
# BUSINESS = 'Pet Rebellion'

CATEGORY = CFG['Site']['Category']
BUSINESS = CFG['Site']['Business']


def parser_initializer(url):
    """ This function initialize the parser, it takes as argument :
        - website URL """
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        return soup

    except ConnectionError:
        print("We didn't succeed to parse your link")


def get_nb_page_review(parser):
    """ This function returns the number of review pages of a specific URL it takes as argument :
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

    page_nb = 2

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
    Create connection to DB. Loading connection parameters from config. ----------> CAN BE CALLED FROM LIOR CODE
    :return: conn, cursor
    """
    try:

        # conn = pymysql.connect(host=CFG["DB"]["Host"],
        #                        user=CFG["DB"]["User"],
        #                        password=CFG["DB"]["Password"])

        conn = pymysql.connect(host=HOST,
                               user=USER,
                               password=PASSWORD)

        return conn, conn.cursor()
    except pymysql.err.OperationalError:
        logger.critical(f"Can not connect to database. user or password may be incorrect.")
        exit()


def database_creation():
    """ DATABASE INITIALIZATION ----------> CAN BE CALLED FROM LIOR CODE """
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


def get_reviews_data(list_page, business_id):
    """ 1. We are collecting the data of a given list of pages"""
    for page in list_page:
        parser = parser_initializer(page)
        widgets = get_page_content(parser)

        """ a. For every review bloc (article) inside the page content """

        art = widgets.find_all('article')
        if art is None:
            continue

        for article in art:

            """ Let's collect the [COUNTRY], if it exists """
            try:
                user_country = article.find('span', {
                    'class': 'typography_typography__QgicV typography_weight-inherit__iX6Fc typography_fontstyle-inherit__ly_HV'}).text
            except AttributeError:
                user_country = 'None'
                logger.warning(f"Can not find country. setting number to default.")

            """ Let's collect the review [SCORE], if it exists """
            try:

                score = article.find('div', {'styles_reviewHeader__iU9Px'}).attrs.values()

                if score is not None:
                    score = list(article.find('div', {'styles_reviewHeader__iU9Px'}).attrs.values())[1]
                else:
                    score = 'None'
            except IndexError:
                score = 'None'
                logger.warning(f"Can not find score. setting number to default.")

            """ Let's collect the review [TEXT], if it exists """

            text = ''

            try:
                text = article.section.find('div', {'styles_reviewContent__0Q2Tg'}).p.text

                if text is not None:
                    if len(text) > 250:
                        text = text[:250] + '...'

            except AttributeError:
                logger.warning(f"Can not find text. setting number to default.")

            """ Let's collect the review [USER_NAME], if it exists """
            try:
                user_name = article.a.div.text

                if user_name is not None:
                    user_name = article.a.div.text
                else:
                    user_name = 'None'
            except AttributeError:
                user_name = 'None'
                logger.warning(f"Can not find user_name. setting number to default.")

            """ Let's collect the review [TITLE], if it exists """
            try:
                review_title = article.h2.text.replace('…', '')

                if review_title is not None:
                    review_title = article.h2.text.replace('…', '')
                else:
                    review_title = 'None'
            except AttributeError:
                review_title = 'None'
                logger.warning(f"Can not find review_title. setting number to default.")

            """ Let's collect the review [DATE], if it exists """
            try:
                review_date = list(article.time.attrs.values())[0].split('T')[0]

                if review_date is not None:
                    review_date = list(article.time.attrs.values())[0].split('T')[0]
                else:
                    review_date = 'None'
            except AttributeError:
                review_date = 'None'
                logger.warning(f"Can not find review_date. setting number to default.")

            # business_url = e['url']

            """ Let's collect the review [URL] """
            url = 'https://www.trustpilot.com' + \
                  article.section.find('div', {'styles_reviewContent__0Q2Tg'}).h2.a['href']

            """ SQL CONNECTION """
            connection, cursor = connect_db()

            """ DATABASE SELECTION """
            cursor.execute(f"USE {CFG['DB']['DB_Name']}")

            """ SELECT BUSINESS_ID """
            # with connection.cursor() as cursor:

            """ INSERT USER_DETAILS """
            cursor.execute('''INSERT INTO User_details (
                                                user_name,
                                                user_location)
                                                VALUES (%s, %s)''', (user_name, user_country))

            userID = cursor.lastrowid

            """ INSERT REVIEW """
            cursor.execute('''INSERT INTO Review (
                                                business_id,
                                                user_id,
                                                score,
                                                url,
                                                review_date)
                             VALUES (%s, %s, %s, %s, %s)''', (business_id, userID, score, url, review_date))

            reviewID = cursor.lastrowid

            """ INSERT TEXT """
            cursor.execute('''INSERT INTO Review_text (
                                                review_id,
                                                title,
                                                text)
                             VALUES (%s, %s, %s)''', (reviewID, review_title, text))

            connection.commit()


def main():
    """ SQL CONNECTION """
    connection, cursor = connect_db()

    """ DATABASE SELECTION """
    cursor.execute(f'USE {CFG["DB"]["DB_Name"]};')

    if BUSINESS != 'All':
        sql = f"""SELECT B.url, B.business_id 
                  FROM Business AS B 
                  WHERE B.name ='{BUSINESS}'"""

    else:
        sql = f"""SELECT url, business_id
                  FROM Business"""

    cursor.execute(sql)
    result = cursor.fetchall()

    """ Let's use the ClI arguments set up by the user - {CATEGORY} & {BUSINESS} """
    # with connection.cursor() as cursor:
    # sql = f"""SELECT B.url, B.business_id
    #           FROM Business AS B
    #           lEFT JOIN Category AS C
    #           ON B.category_id = C.category_id WHERE B.name ='{BUSINESS}'"""
    # cursor.execute(sql)
    # result = cursor.fetchall()

    logger.info(f"3")

    """ FOR every row in the SELECT query, let's collect the reviews """
    for row in result:
        business_url = row[0]
        business_id = row[1]
        parser = parser_initializer(business_url)
        page_nb = get_nb_page_review(parser)
        list_page = get_list_of_pages(business_url, page_nb)
        get_reviews_data(list_page, business_id)

    connection, cursor = connect_db()
    cursor.execute(f'USE {CFG["DB"]["DB_Name"]};')

    """ -------------------------> API IMPLEMENTATION <-------------------------"""

    """ SELECT TEXT FROM [Review_text] TABLE """
    with connection.cursor() as cursor:
        sql = f"""SELECT R.review_id, T.text, name
                 FROM Review AS R
                 LEFT JOIN Review_text AS T
                 ON R.review_id = T.review_id
                 LEFT JOIN Business AS B
                 ON R.business_id = B.business_id
                 WHERE name = '{CFG['Site']['Business_API']}';"""

        cursor.execute(sql)
        result = cursor.fetchall()

        """ FOR every row, let's convert TEXT to sentiment """
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

            """ Let's clean the returned data, in order to prepare the insertion to the database """

            json_file = json.loads(response.text)

            if response.text.find("aggregate_sentiment") == -1 or json_file is None or json_file == '':
                logger.info(f"Can not find country. setting number to default.")
                continue

            neg = round(json_file["aggregate_sentiment"]['neg'], 4)
            neu = round(json_file["aggregate_sentiment"]['neu'], 4)
            pos = round(json_file["aggregate_sentiment"]['pos'], 4)

            """ INSERT SENTIMENT TO A NEW TABLE CALLED Review_sentiment - (ALREADY IMPLEMENTED IN THE fill_db.sql FILE) """
            cursor.execute('''INSERT INTO Review_sentiment (
                                                    positive,
                                                    neutral,
                                                    negative)
                             VALUES (%s, %s, %s)''', (neg, neu, pos))

            connection.commit()

    """ SELECT SENTIMENT FROM THE DATABASE """
    connection, cursor = connect_db()
    cursor.execute(f'USE {CFG["DB"]["DB_Name"]};')

    with connection.cursor() as cursor:
        sql = """SELECT S.review_id, positive, neutral, negative, text 
                     FROM Review_sentiment AS S 
                     LEFT JOIN Review_text AS T 
                     ON S.review_id = T.review_id"""

        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            print(row)


if __name__ == "__main__":
    main()
