import pymysql
import tp_config
import tp_logger

SQL_ARCH = "fill_db.sql"

CFG = tp_config.CFG
logger = tp_logger.get_logger()


# connect to DB
def connect_db():
    """
    Create connection to DB. Loading connection parameters from config.
    :return: conn, cursor
    """
    print(CFG["DB"]["User"])
    print(CFG["DB"]["Host"])
    print(CFG["DB"]["Password"])
    try:
        conn = pymysql.connect(host=CFG["DB"]["Host"],
                               user=CFG["DB"]["User"],
                               password=CFG["DB"]["Password"])
        return conn, conn.cursor()
    except pymysql.err.OperationalError:
        logger.critical(f"Can not connect to {CFG['DB']['DB_Name']} DB. user or password may be incorrect.")
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


def db_cat_insert(category):
    query = f'INSERT INTO Category (name, url) VALUES ("{category.name}", "{category.url}");'
    exec_query(query)


def db_businesses_insert(category, business_lst):
    """ Insert the businesses of the category to the DB """
    if len(business_lst) == 0:
        return
    for business in business_lst:
        business.name = business.name.replace('"', "'")
        query = f'INSERT INTO Business (category_id, name, url, score, reviews) VALUES ({category.id}, ' \
                f'"{business.name}", "{business.url}", {business.score}, {business.reviews});'
        exec_query(query)


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
