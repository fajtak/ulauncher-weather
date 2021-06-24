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

	def on_event(self, event, extension):
		items = []

		city = event.get_argument()

		r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city + "&APPID=0bb5716aa807576ad02c24541f096076&units=metric")
		data_string = r.json()

		weather = data_string["weather"][0]["description"]
		icon = data_string["weather"][0]["icon"]
		temp = data_string["main"]["temp"]
		press = data_string["main"]["pressure"]
		hum = data_string["main"]["humidity"]
		wind = data_string["wind"]["speed"]
		cloud = data_string["clouds"]["all"]
		#dollar = data_string["bpi"]["USD"]["rate"]
		# update = data_string['dt']
		# timestamp = datetime.datetime.fromtimestamp(update)

		items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
										name='%s: %s, %s %sC' % (city.title(),weather.title(),str(temp),chr(176)),
										# name='Thoiry: %s' % city,
										# description='Last Update: %s' % str(timestamp.strftiulame('%Y-%m-%d %H:%M:%S')),
										description='Pressure: %s Pa, Humidity: %s%%, Wind: %s m/s, Cloudiness: %s%%' % (press,hum,wind,cloud),
										on_enter=HideWindowAction()))

		return RenderResultListAction(items)

if __name__ == '__main__':
	DemoExtension().run()