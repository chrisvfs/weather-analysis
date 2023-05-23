import json
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pyodbc


f = open('db_data.json')
js = json.load(f)


driver = js['server_info']['driver']
server = js['server_info']['server']
database = js['server_info']['database']
username = js['server_info']['username']
password = js['server_info']['password']

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';DATABASE='+database+';ENCRYPT=yes;UID='+username+';PWD='+ password)
cursor = cnxn.cursor()


locations = {
    "Sheffield": 2638077,
    "Manchester": 2643123,
    "Leeds": 2644688,
    "Felixstowe": 2649579
}


def get_weather(loc):
    loc_code = locations.get(loc)
    print("Downloading today's weather for "+loc)

    return requests.get("https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/"+str(loc_code))

def process_individual_forecast(t, l, d_count):
    r_list = []
    #date variables
    r_list.append(l) # location
    r_list.append(datetime.now()) # time of extract
        
    HH = t.find_element(By.CLASS_NAME,"wr-time-slot-primary__time").text.split('\n')[0] # view time
    if int(HH) < 6:
        d_count+=1
    
    r_list.append((datetime.now()+timedelta(days=d_count)).date()) #date
    r_list.append(HH) # hour
    r_list.append(t.find_element(By.CLASS_NAME,"wr-weather-type__icon").get_attribute("title")) # weather title
    r_list.append((t.find_element(By.CLASS_NAME,"wr-time-slot-primary__temperature").text)[:-1]) #temperature
    r_list.append((t.find_element(By.CLASS_NAME,"wr-time-slot-primary__precipitation").text.split('\n')[0])[:-1]) #precipitation
    r_list.append(t.find_element(By.CLASS_NAME,"wr-time-slot-primary__wind-speed").text.split('\n')[1]) #wind speed (MPH)
    r_list.append(t.find_element(By.CLASS_NAME,"wr-time-slot-primary__wind-speed").text.split('\n')[3]) #wind direction
    return r_list

def process_weather(location):
    extract = []

    #count days
    day_count = 0

    #selenium setup
    driver = webdriver.Chrome()
    driver.get('https://www.bbc.co.uk/weather/' + str(locations.get(location)))
    assert location in driver.title

    #loop through each visible day
    days = driver.find_elements(By.CLASS_NAME,"wr-js-day")
    for day in days:
        day.click()
        curr_day = day.find_element(By.CLASS_NAME,"wr-date").text
        forecast = driver.find_elements(By.CLASS_NAME, "wr-js-time-slot")
        for times in forecast:
            extract.append(process_individual_forecast(times,location,day_count))
        day_count += 1
    return extract


def upload_to_SQL_server(data_extract):
    for rows in data_extract:
        cursor.execute(
            "insert into weatherData(location,extractDT,forecastD,hour,weather,temp,precipitation,windSpeed,direction) values (?,?,?,?,?,?,?,?,?)",(rows)
        )
    cnxn.commit()

upload_to_SQL_server(process_weather("Sheffield"))
