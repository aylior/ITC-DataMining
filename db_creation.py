import csv
import pymysql


def database_creation():
    """ DATABASE LOGIN """
    HOST = "localhost"
    USER = "root"
    PASSWORD = "rootroot"
    DB_NAME = "trust_pilot"

    """ DATABASE INITIALIZATION """
    connection = pymysql.connect(host=HOST,
                                 user=USER,
                                 password=PASSWORD,
                                 cursorclass=pymysql.cursors.DictCursor)

    cursor = connection.cursor()

    with open('fill_db.sql', 'r') as p:
        sqlFile = p.read()
        p.close()
        sqlCommands = sqlFile.split(';')

        for command in sqlCommands:
            try:
                if command.strip() != '':
                    cursor.execute(command)
            except IOError:
                print("Command skipped: ")

    with open('export.csv', 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        with connection.cursor() as cursor:
            for line_num, line in enumerate(reader):
                """ CATEGORY """

                cursor.execute('''INSERT INTO Category (
                                                    name)
                                 VALUES (%s)''', (line[0]))

                categoryID = cursor.lastrowid

                """ BUSINESS """
                cursor.execute('''INSERT INTO Business (
                                                    category_id,
                                                    name,
                                                    url)
                                 VALUES (%s,%s,%s)''', (categoryID, line[1], line[2]))

                businessID = cursor.lastrowid

                """ USER_DETAILS """
                cursor.execute('''INSERT INTO User_details (
                                                    user_name,
                                                    user_location)
                                                    VALUES (%s, %s)''', (line[3], line[4]))

                userID = cursor.lastrowid

                """ REVIEW """
                cursor.execute('''INSERT INTO Review (
                                                    business_id,
                                                    user_id,
                                                    score,
                                                    url,
                                                    review_date)
                                 VALUES (%s, %s, %s, %s, %s)''', (businessID, userID, line[5], line[9], line[8]))

                reviewID = cursor.lastrowid

                """ TEXT """
                cursor.execute('''INSERT INTO Review_text (
                                                    review_id,
                                                    title,
                                                    text)
                                 VALUES (%s, %s, %s)''', (reviewID, line[6], line[7]))

    with connection.cursor() as cursor:
        sql = "SELECT * FROM Business"
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            print(row)
