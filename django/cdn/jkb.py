import re
import os
import shutil
import time
import pymongo
import gc
import datetime
import pandas as pd
from urllib.parse import urlparse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

username = config['jkb']['username']

password = config['jkb']['password']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

now = datetime.datetime.now()

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--window-size=1920,1080')

prefs={"download.default_directory":"/opt/data/tmp"}

chrome_options.add_experimental_option("prefs",prefs)

driver = webdriver.Chrome(chrome_options=chrome_options)

driver.get("https://monitoring.cloudwise.com/users/login")

driver.maximize_window()

time.sleep(1)

driver.find_elements_by_xpath('//*[@id="email"]')[0].send_keys(username)

driver.find_elements_by_xpath('//*[@id="pwd"]')[0].send_keys(password)

driver.find_elements_by_xpath('//*[@id="sigin_btn"]')[0].click()

time.sleep(3)

driver.get("https://monitoring.cloudwise.com/monitoring/#/taskmgmt/list")

time.sleep(3)

try:
    driver.find_elements_by_xpath('//*[@id="myV6Modal"]/div/div/div[3]/button')[0].click()

except:
    pass

driver.find_elements_by_xpath('//*[@id="page_rows_select"]')[0].click()

time.sleep(0.5)

driver.find_elements_by_xpath('//*[@id="page_rows_select"]/option[3]')[0].click()

time.sleep(0.5)

driver.find_elements_by_xpath('//*[@id="check_all"]')[0].click()

driver.find_elements_by_xpath('/html/body/div[1]/div[1]/div/div[2]/div/div[2]/div[4]/div/div[1]/div[1]/a[8]')[0].click()

time.sleep(5)

driver.quit()

filename = max([os.path.join('/opt/data/tmp/', f) for f in os.listdir('/opt/data/tmp/')],key=os.path.getctime)

shutil.move(filename,os.path.join('/opt/data/tmp/',r"1.xlsx"))

df = pd.read_excel('/opt/data/tmp/1.xlsx', engine='openpyxl', usecols=[1, 2, 4])

#credentials = ServiceAccountCredentials.from_json_keyfile_name('/opt/prom/dragonball/credentials.json',scopes='https://www.googleapis.com/auth/spreadsheets')

from google.oauth2 import service_account
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
service = discovery.build('sheets', 'v4', credentials=delegated_credentials)

#service = discovery.build('sheets', 'v4', credentials=credentials)

spreadsheet_id = '1AZcypq9YXrD5emrSA3J0GNmeEW3JV66SK_kwBkqyCqc'

range_ = "'sheet'!A2:C"

value_render_option = 'FORMATTED_VALUE'

date_time_render_option = 'SERIAL_NUMBER'

request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option)

response = request.execute()

failList = []

if "values" in response:
    failList = response['values']


for i, row in df.iterrows():
    new = {}

    domain = row[0]

    new['url'] = domain

    if re.search('//', domain):
        domain = urlparse(domain).netloc

    domain = domain.split(':')[0]

    new['domain'] = domain

    new['type'] = row[1]

    new['updateTime'] = now

    if row[2] == "-":
        new['health'] = "standby"
    else:
        new['health'] = "ok"

    if failList:
        for each in failList:
            if re.search(new['domain'], each[0]):
                new['health'] = "fail"
                new['detail'] = each[1] + ' ' + each[2]

    mycol.update_many({"domain": new['domain']}, {"$set": {"jkb": new}})

    mycol.update_many({"jkb.updateTime": {"$lt": now}}, {"$unset": {"jkb": ""}})

gc.collect()
