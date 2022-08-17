import argparse
import json

CONFIG = 'config.json'


def load_configuration():
    """ load the json configuration file"""
    with open(CONFIG) as f:
        return json.load(f)


CFG = load_configuration()


def read_cli():
    """ CLI for different arguments that override the arguments in the config file."""
    parser = argparse.ArgumentParser(description='TrustPilot Scraper')
    parser.add_argument("-c", type=str, default="All", help="Category name to parse or 'All'")
    parser.add_argument("-b", type=str, default="All", help="Business name to parse or 'All'")
    parser.add_argument("-p", type=int, default=2, help="Number of category pages to scrape or 'All.")
    parser.add_argument("-lf", type=str, default="INFO",
                        help="Log level for log file (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
                             "default: INFO")
    parser.add_argument("-lc", type=str, default="INFO",
                        help="Log level for log to console (DEBUG, INFO, WARNING, ERROR, CRITICAL). "
                             "default: INFO")
    parser.add_argument("-user", type=str, default="root", help="DB user name. default: root.")
    parser.add_argument("-pwd", type=str, help="DB user password. No Default!.")
    parser.add_argument("-hst", type=str, default="localhost", help="DB host. default: localhost")
    parser.add_argument("-cd", default="N", type=str, choices={"Y", "N"},
                        help="Drop DB and create again before start scraping (Y/N). default: 'N'")

    # update config parameter with CLI arguments
    args = parser.parse_args()
    if args.c:
        CFG['Site']['Category'] = args.c
    if args.b:
        CFG['Site']['Business'] = args.b
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


read_cli()
