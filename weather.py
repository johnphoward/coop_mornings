# weather.py
# Get weather from Forecast API

import requests
import time
from geopy.geocoders import Nominatim

forecast_api_key = '1e51e3cae8556dc7c38f2881d074d957'
forecast_api_base = 'https://api.forecast.io/forecast/'


def getWeatherForAddress(address):
	""" 
	Forecast API calls take the form below:
	https://api.forecast.io/forecast/APIKEY/LATITUDE,LONGITUDE 
	Uses geocoder to get the latitude and longitude of an address, 
	then returns all gathered weather data for that location
	"""
	geocoder = Nominatim()
	home_location = geocoder.geocode(address)
	latitude = str(home_location.latitude)
	longitude = str(home_location.longitude)
	url = forecast_api_base + forecast_api_key + '/' + latitude + ',' + longitude
	weather_response = requests.get(url)
	weather_json = weather_response.json()
	return weather_json

weather = getWeatherForAddress('218 Hemenway St Boston')
hourly_data = weather['hourly']['data']
print hourly_data[0].keys()
for hour in hourly_data:
	this_time = time.localtime(hour['time'])
	print this_time.tm_hour, hour['temperature'], hour['precipProbability'] * 100.0