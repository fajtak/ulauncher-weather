import requests
import datetime
import gettext
import os

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
        r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city +
                         "&APPID=" + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()
        print(data_string)

        weather = data_string["weather"][0]["description"]
        icon = data_string["weather"][0]["icon"]
        temp = data_string["main"]["temp"]
        press = data_string["main"]["pressure"]
        hum = data_string["main"]["humidity"]
        wind = data_string["wind"]["speed"]
        cloud = data_string["clouds"]["all"]
        cityID = data_string["id"]

        items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                         name='%s: %s, %s %s' % (
                                             city.title(), weather.title(), str(temp), self.temp_symbol),
                                         description=self.translator(
                                             "Pressure: %s Pa), (Humidity: %s%%), (Wind: %s m/s), (Cloudiness): %s%%") % (press, hum, wind, cloud),
                                         on_enter=OpenUrlAction(gen_url(cityID))))

    def precip_in_hour(self, items, precip, icon, cityID):
        total_prec = 0.0
        
        for event in precip:
            total_prec += event["precipitation"]

        if (total_prec == 0):
            items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                             name=self.translator(
                                                 'No rain in the next hour!'),
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
                                                 name=self.translator(
                                                     'Raining! It will not end within an hour'),
                                                 description=self.translator(
                                                     'Expected precipitations in the next hour: %2.1f mm/h') % (total_prec/len(precip)),
                                                 on_enter=OpenUrlAction(gen_url(cityID))))
            else:
                items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                                 name=self.translator('Raining! It should stop in %s minutes') % (
                                                     rainStopTime),
                                                 description=self.translator(
                                                     'Expected precipitations in the next hour: %2.1f mm/h') % (total_prec/len(precip)),
                                                 on_enter=OpenUrlAction(gen_url(cityID))))
        else:
            rainStartTime = 0
            for idx, event in enumerate(precip):
                if event["precipitation"] != 0:
                    rainStartTime = idx+1
                    break
            items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                             name=self.translator('It should start raining in %s minutes') % (
                                                 rainStartTime),
                                             description=self.translator(
                                                 'Expected precipitations in the next hour: %2.1f mm/h') % (total_prec/len(precip)),
                                             on_enter=OpenUrlAction(gen_url(cityID))))

    def precip_in_12hours(self, items, hourly, icon, cityID):
        # dt = datetime.datetime.now()
        total_prec = 0.0
        times = ""
        precip = ""
        nEntries = 0
        
        for eventID in range(12):
            if nEntries == 6:
                times += " ..."
                break
            if "rain" in hourly[eventID]:
                precip += "" + str(hourly[eventID]["rain"]["1h"]) + "mm/h   "
                nEntries += 1
            else:
                continue
                # precip += "  " + "0 mm/h" + "  "
            time = datetime.datetime.fromtimestamp(hourly[eventID]["dt"])
            times += " " + str(time.hour)
            if time.hour < 12:
                times += "am    "
            else:
                times += "pm    "
        if (len(precip) == 0):
            items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                             name=self.translator(
                                                 'No rain in the next 12 hours!'),
                                             description='',
                                             on_enter=OpenUrlAction(gen_url(cityID))))
        else:
            items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                             name=str(times),
                                             description=str(precip),
                                             on_enter=OpenUrlAction(gen_url(cityID))))

    def add_future_precipitations(self, items, city):
        r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city +
                         "&APPID=" + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()

        lon = data_string["coord"]["lon"]
        lat = data_string["coord"]["lat"]
        icon = data_string["weather"][0]["icon"]
        cityID = data_string["id"]

        r = requests.get("https://api.openweathermap.org/data/2.5/onecall?lat=" + str(lat) + "&lon=" + str(lon) +
                         '&exclude=current,daily,alerts&appid=' + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()
        # recent_time = data_string["current"]["dt"]
        precip = data_string["minutely"]
        self.precip_in_hour(items, precip, icon, cityID)
        hourly = data_string["hourly"]
        self.precip_in_12hours(items, hourly, icon, cityID)
		

    def add_3day_forecast(self, items, city):
        r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city +
                         "&APPID=" + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()

        lon = data_string["coord"]["lon"]
        lat = data_string["coord"]["lat"]
        icon = data_string["weather"][0]["icon"]
        cityID = data_string["id"]

        r = requests.get("https://api.openweathermap.org/data/2.5/onecall?lat=" + str(lat) + "&lon=" + str(lon) +
                         '&exclude=current,minutely,hourly,alerts&appid=' + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()
        # recent_time = data_string["current"]["dt"]
        daily = data_string["daily"]

        for day in range(1, 4):
            time = datetime.datetime.fromtimestamp(daily[day]["dt"])
            descr = ""
            if "rain" in daily[day]:
                items.append(ExtensionResultItem(icon='images/'+daily[day]["weather"][0]["icon"][0:2]+'d.png',
                                                 name='%s, %s %s - %s:' % (str(time.strftime("%a")), str(time.strftime("%d")), str(
                                                     time.strftime("%b")), daily[day]["weather"][0]["description"]),
                                                 description='%2.0f / %2.0f %s, %2.1f mm/day' % (
                                                     daily[day]["temp"]["max"], daily[day]["temp"]["min"], self.temp_symbol, daily[day]["rain"]),
                                                 on_enter=OpenUrlAction(gen_url(cityID))))
            else:
                items.append(ExtensionResultItem(icon='images/'+daily[day]["weather"][0]["icon"][0:2]+'d.png',
                                                 name='%s,f %s %s - %s' % (str(time.strftime("%a")), str(time.strftime("%d")), str(
                                                     time.strftime("%b")), daily[day]["weather"][0]["description"]),
                                                 description='%2.0f / %2.0f %s' % (
                                                     daily[day]["temp"]["max"], daily[day]["temp"]["min"], self.temp_symbol),
                                                 on_enter=OpenUrlAction(gen_url(cityID))))

    def on_event(self, event, extension):
        items = []
        self.apikey = extension.preferences["api_key"]
        self.units = extension.preferences["units"]
        self.language = extension.preferences["language"]
        self.temp_symbol = f'{chr(176)}C' if self.units == 'metric' else f'{chr(176)}F'
        predef_cities = extension.preferences["predef_cities"].split(";")

        localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locales')
        translator = gettext.translation('base', localedir=localedir, languages=[self.language])
        self.translator = translator.gettext

        city = event.get_argument()

        if (city != None):
            self.add_current_weather(items, city)
            self.add_future_precipitations(items, city)
            self.add_3day_forecast(items, city)
        else:
            for iterCity in predef_cities:
                self.add_current_weather(items, iterCity)

        return RenderResultListAction(items)


if __name__ == '__main__':
    WeatherExtension().run()
