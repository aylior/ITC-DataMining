# [TrustPilot.com](https://www.trustpilot.com) Scraper
## ITC - Data Science course 2022 - Data Mining project

[Github](https://github.com/aylior/ITC-DataMining.git)

### milestone - 1: Scraping
The purpose of this milestone is to write a scraper for [TrustPilot.com](https://www.trustpilot.com) website.
<img src="img/tp.png"/>

#### Handling the challenge:

1. The scraper starting point is the website [categories page](https://www.trustpilot.com/categories).

   The scraper collect all categories urls.


2. For each category the scraper follows its url and scrape the category pages.

   The call to the pages is asynchronous in a batch size defined in the configuration.


3. The scraper create an entry for each business in the page containing its

   name, url, rank and number of reviews. Businesses with no score will be 
   
   skipped (it means that they also don't have reviews).

   <img src="img/tpb.png"/>


4. After getting all the category businesses, the data is dumped to the data.

   json file before scraping the next category.

   <img src="img/data.png"/>


5. After scraping the categories businesses pages, the scraper follow the url of each business 
   and get additional information from the business page in TrustPilot website 
   such as review's text, it's date, author etc.

   <img src="img/tpr.png"/>


6. The scraper log its progress to trustpilot.log and to the console at the same time.


7. The scraper log its total run time as the final log line.


### Selected Configuration
* Site: Category - "All" or category name to be scraped.
* Site: Filters - define the filters apply on the category pages.
* Site: Pages - number of pages to scrape for each category or "All".
* Site: Min_Reviews_Num - minimum number of review. Currently set to 210.
* Log: File_Log_Level/Log_Console_Level - log level to the handler. Currently INFO.
* Log: Batch_Size - Number of async calls. Currently set to 20


### Installation
pip install -r requirements.txt

### Entry Point
python trustpilot_scraper.py -pwd [DB pwd]

### Requierments
#### Modules
* grequests~=0.6.0
* requests~=2.28.1
* beautifulsoup4~=4.11.1
* PyMySQL~=1.0.2
### Files
* config.json - on the main directory
* trustpilot.log - will be created by the scraper in the main directory.

### milestone - 2: Database
All data is inserted to database according to the ERD instead of dumped to json.

#### Added configuration
* DB: Host - host name of the DB. Defaul: localhost
* DB: User - DB user. Default: root
* DB: Password - need to provide through CLI
* DB: Create_db_file - sql file name to create the DB and tables on main directory.
* DB: Create_db - drop db and create again. Default: 'N'

#### Added files
* create_db.sql - on the main directory. build the DB and tables.

#### CLI
-c :   Category name to parse or 'All'")<br>
-p :   Number of category pages to scrape or 'All'<br>
-lf :  Log level for log file (DEBUG, INFO, WARNING, ERROR, CRITICAL).default: INFO<br>
-lc  : Log level for log to console (DEBUG, INFO, WARNING, ERROR, CRITICAL). default: INFO<br>
-user: DB user name. default: root.<br>
-pwd: DB user password. No Default!.<br>
-hst:  DB host. default: localhost<br>
-cd :  Drop DB and create again before start scraping (Y/N). default: 'N'<br>

#### DB
ERD<br>
<img src="img/ERD.png"><br>
Category Table<br>
<img src="img/category_tbl.png"><br>
Business Table<br>
<img src="img/business_tbl.png">

