import requests
import datetime

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

class DemoExtension(Extension):

	def __init__(self):
		super(DemoExtension, self).__init__()
		self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):

	def add_item(self, items, city, apikey):
		r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city + "&APPID=" + apikey + "&units=metric")
		data_string = r.json()

		weather = data_string["weather"][0]["description"]
		icon = data_string["weather"][0]["icon"]
		temp = data_string["main"]["temp"]
		press = data_string["main"]["pressure"]
		hum = data_string["main"]["humidity"]
		wind = data_string["wind"]["speed"]
		cloud = data_string["clouds"]["all"]

		items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='%s: %s, %s %sC' % (city.title(),weather.title(),str(temp),chr(176)),
										description='Pressure: %s Pa, Humidity: %s%%, Wind: %s m/s, Cloudiness: %s%%' % (press,hum,wind,cloud),
										on_enter=HideWindowAction()))

	def on_event(self, event, extension):
		items = []
		apikey = extension.preferences["api_key"]
		predef_cities = extension.preferences["predef_cities"].split(";")

		city = event.get_argument()

		if (city != None):
			self.add_item(items,city,apikey)
		else:
			for iterCity in predef_cities:
				self.add_item(items,iterCity,apikey)

		return RenderResultListAction(items)

if __name__ == '__main__':
	DemoExtension().run()