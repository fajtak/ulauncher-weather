import requests
import datetime

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

def gen_url(cityID):
	base_url = "https://openweathermap.org/city/"
	return base_url + str(cityID)

class WeatherExtension(Extension):

	def __init__(self):
		super(WeatherExtension, self).__init__()
		self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):

	def add_current_weather(self, items, city):
		r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city + "&APPID=" + self.apikey + "&units=metric")
		data_string = r.json()

		weather = data_string["weather"][0]["description"]
		icon = data_string["weather"][0]["icon"]
		temp = data_string["main"]["temp"]
		press = data_string["main"]["pressure"]
		hum = data_string["main"]["humidity"]
		wind = data_string["wind"]["speed"]
		cloud = data_string["clouds"]["all"]
		cityID = data_string["id"]

		items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='%s: %s, %s %sC' % (city.title(),weather.title(),str(temp),chr(176)),
										description='Pressure: %s Pa, Humidity: %s%%, Wind: %s m/s, Cloudiness: %s%%' % (press,hum,wind,cloud),
										on_enter=OpenUrlAction(gen_url(cityID))))

	def add_future_precipitations(self, items, city):
		r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city + "&APPID=" + self.apikey + "&units=metric")
		data_string = r.json()

		lon = data_string["coord"]["lon"]
		lat = data_string["coord"]["lat"]
		icon = data_string["weather"][0]["icon"]
		cityID = data_string["id"]

		r = requests.get("https://api.openweathermap.org/data/2.5/onecall?lat=" + str(lat) + "&lon=" + str(lon) + '&exclude=hourly,daily,alerts&appid=' + self.apikey + "&units=metric")
		data_string = r.json()
		# recent_time = data_string["current"]["dt"]
		precip = data_string["minutely"]

		total_prec = 0.0
		for event in precip:
			total_prec += event["precipitation"]

		if (total_prec == 0):
			items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='No rain in the next hour!',
										description='',
										on_enter=OpenUrlAction(gen_url(cityID))))
		elif (precip[0]["precipitation"] != 0):
			rainStopTime = 60
			for idx, event in enumerate(precip):
				if event["precipitation"] == 0:
					rainStopTime = idx+1
					break
			if rainStopTime == 60:
				items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='Raining! It will not end within an hour',
										description='Expected precipitations in the next hour: %2.1f mm/h' % (total_prec/len(precip)),
										on_enter=OpenUrlAction(gen_url(cityID))))
			else:
				items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='Raining! It should stop in %s minutes' % (rainStopTime),
										description='Expected precipitations in the next hour: %2.1f mm/h' % (total_prec/len(precip)),
										on_enter=OpenUrlAction(gen_url(cityID))))
		else:
			rainStartTime = 0
			for idx, event in enumerate(precip):
				if event["precipitation"] != 0:
					rainStartTime = idx+1
					break
			items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='It should start raining in %s minutes' % (rainStartTime),
										description='Expected precipitations in the next hour: %2.1f mm/h' % (total_prec/len(precip)),
										on_enter=HideWindowAction()))

	def on_event(self, event, extension):
		items = []
		self.apikey = extension.preferences["api_key"]
		predef_cities = extension.preferences["predef_cities"].split(";")

		city = event.get_argument()

		if (city != None):
			self.add_current_weather(items,city)
			self.add_future_precipitations(items,city)
		else:
			for iterCity in predef_cities:
				self.add_current_weather(items,iterCity)

		return RenderResultListAction(items)

if __name__ == '__main__':
	WeatherExtension().run()