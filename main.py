"""
This is the lambda function to make the auto reply to the zomato / google reviews
"""
import json
import sys
import logging
import os

import pandas as pd
from sqlalchemy import create_engine, text

from datetime import datetime
from dateutil.relativedelta import relativedelta

from utils import generate_traceback as api_traceback
from utils import generate_response as api_response
from utils import environment_config, constants
from utils.authentication import authenticate
from utils.constants import Const

from boto3 import client as boto3_client
import requests

from time_series_predict import predict_current_month

lambda_client = boto3_client('lambda' , region_name='ap-south-1')

# Load variables from .env file
with open('env.env', 'r') as file:
    for line in file:
        key, value = line.strip().split('=')
        os.environ[key] = value
# logger client to enable logging
logger = logging.getLogger()
logger.setLevel(int(os.environ.get("LOG_LEVEL")))

env_object = environment_config.EnvironmentConfigurations()
try:
    api_secrets = env_object.get_value(os.environ.get("API_SECRETS"))
except ValueError as e:
    logger.error(str(e))
    sys.exit()

rds_host = api_secrets.get("rds_host")
user_name = api_secrets.get("rds_user_name")
password = api_secrets.get("rds_password")
db_name = api_secrets.get("rds_db_name")

try:
    conn = create_engine(f'mysql+pymysql://{user_name}:{password}@{rds_host}/{db_name}')
except Exception as e:
    print(e)
    logger.error("ERROR: Unexpected error: Could not connect to the MySQL instance.")
    sys.exit()


def fetch_data_from_db(query, conn, params=None):
    try:

        result = pd.read_sql(text(query), conn, params=params)
        conn.dispose()
        return result

    except Exception as e:
        logger.error(f"Failed to retrieve data from the database: {str(e)}")
        return None

def lambda_handler(event , context):
    query = '''
                SELECT
                    res_id,
                    period,
                    date,
                    sum(sales_generated_ads) AS total_sales_generated_ads,
                    sum(ads_consumed_ads) AS total_ads_consumed_ads,
                    ROUND(SUM(sales_generated_ads) / SUM(ads_consumed_ads), 2) AS ROI,

                    sum(orders_tm) AS total_orders_tm,
                    sum(menu_opens_funnel) AS total_menu_opens_funnel,
                    ROUND(SUM(orders_tm) / SUM(menu_opens_funnel), 2) AS Organic_conversions,

                    sum(ad_orders_ads) AS total_ad_orders_ads,
                    sum(inorganic_menu_opens_ads) AS total_inorganic_menu_opens_ads,
                    ROUND(SUM(ad_orders_ads) / SUM(inorganic_menu_opens_ads), 2) AS Inorganic_conversions

                FROM
                    historical_data_zomato
                WHERE
                    res_id = '18175468'
                GROUP BY
                    res_id,
                    date
                ORDER BY
                    date asc
            '''

    data = fetch_data_from_db(query , conn)

    date = data['date']
    dates = [datetime.strptime(str(date_str), '%Y%m%d') for date_str in date]
    dates = [date.strftime('%Y-%m-%d') for date in dates]

    roi = data['ROI'].tolist()
    organic_conversions = data['Organic_conversions'].tolist()
    inorganic_conversions = data['Inorganic_conversions'].tolist()
    menu_opens_funnel = data['total_menu_opens_funnel'].tolist()

    print("ROI PREDICTED")
    roi = predict_current_month(dates , roi)
    # print(roi)
    # breakpoint()
    print("ORGANIC CONVERSIONS PREDICTED")
    organic_conversions = predict_current_month(dates , organic_conversions)
    # print(organic_conversions)

    print("INORGANIC CONVERSIONS PREDICTED")
    inorganic_conversions = predict_current_month(dates , inorganic_conversions)
    # print(inorganic_conversions)

    print("MENU OPEN FUNNEL PREDICTED")
    menu_opens_funnel = predict_current_month(dates , menu_opens_funnel)
    # print(menu_opens_funnel)

    conn.dispose()

if __name__ == "__main__":

    f = open('./sample_api_gw_event.json', "r")

    event = json.loads(f.read())

    data = lambda_handler(event, {})