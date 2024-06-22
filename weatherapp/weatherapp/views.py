from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
import urllib.request
import json
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseServerError

def get_local_time(latitude, longitude):
    api_key_timezone = settings.TIMEZONE_API_KEY
    api_url = f'http://api.timezonedb.com/v2.1/get-time-zone?key={api_key_timezone}&format=json&by=position&lat={latitude}&lng={longitude}'
    try:
        source = urllib.request.urlopen(api_url).read()
        timezone_data = json.loads(source)
        if timezone_data['status'] == 'OK':
            local_time = timezone_data['formatted']
            return local_time
        else:
            return None
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code}. Error fetching local time."
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}. Error fetching local time."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def home(request):
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if city:
            try:
                api_key_weather = settings.WEATHER_API_KEY
                api_url_weather = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key_weather}'
                source_weather = urllib.request.urlopen(api_url_weather).read()
                weather_data = json.loads(source_weather)
                coordinates = {
                    'lon': weather_data['coord']['lon'],
                    'lat': weather_data['coord']['lat']
                }
                return redirect(reverse('report') + f'?city={city}&lat={coordinates["lat"]}&lon={coordinates["lon"]}')
            except urllib.error.HTTPError as e:
                error = f"The city '{city}' was not found."
            except urllib.error.URLError as e:
                error = f"URL Error: {e.reason}."
            except Exception as e:
                error = f"An unexpected error occurred: {str(e)}"
        else:
            error = "Please enter a valid city name."
    else:
        error = None
    context = {
        'error': error,
    }
    return render(request, 'index.html', context)

def report(request):
    city = request.GET.get('city')
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not city or not lat or not lon:
        return HttpResponseBadRequest('City parameter missing')
    try:
        api_key_weather = settings.WEATHER_API_KEY
        api_url_weather = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key_weather}'
        source_weather = urllib.request.urlopen(api_url_weather).read()
        weather_data = json.loads(source_weather)
        api_url_forecast = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key_weather}'
        source_forecast = urllib.request.urlopen(api_url_forecast).read()
        forecast_data = json.loads(source_forecast)
        weather_condition = weather_data['weather'][0]['description']
        temp_celsius = weather_data['main']['temp']
        temp_fahrenheit = (temp_celsius * 9/5) + 32
        country_code = weather_data['sys']['country']
        coordinates = {
            'lon': weather_data['coord']['lon'],
            'lat': weather_data['coord']['lat']
        }
        pressure = weather_data['main']['pressure']
        humidity = weather_data['main']['humidity']
        weather_icon = weather_data['weather'][0]['icon']
        sunrise_timestamp = weather_data['sys']['sunrise']
        sunset_timestamp = weather_data['sys']['sunset']
        sunrise_time = datetime.utcfromtimestamp(sunrise_timestamp).strftime('%H:%M')
        sunset_time = datetime.utcfromtimestamp(sunset_timestamp).strftime('%H:%M')
        local_time = get_local_time(lat, lon)
        forecast_list = []
        today_date = datetime.utcnow().date()
        next_day = today_date + timedelta(days=1)
        for forecast in forecast_data['list']:
            forecast_date = datetime.utcfromtimestamp(forecast['dt']).date()
            if forecast_date >= next_day and len(forecast_list) < 4:
                forecast_list.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'weather_condition': forecast['weather'][0]['description'],
                    'weather_icon': forecast['weather'][0]['icon'],
                    'temp_min': forecast['main']['temp_min'],
                    'temp_max': forecast['main']['temp_max'],
                })
                next_day += timedelta(days=1)

        context = {
            'city': city,
            'country_code': country_code,
            'coordinates': coordinates,
            'temp_celsius': f"{temp_celsius} °C",
            'temp_fahrenheit': f"{temp_fahrenheit} °F",
            'pressure': f"{pressure} hPa",
            'humidity': f"{humidity} %",
            'weather_condition': weather_condition.capitalize(),
            'sunrise_time': sunrise_time,
            'sunset_time': sunset_time,
            'local_time': local_time,
            'weather_icon': weather_icon,
            'forecast_list': forecast_list,
        }

    except Exception as e:
        return HttpResponseServerError(f"Error fetching weather data: {str(e)}")

    return render(request, 'report.html', context)

def handling_404(request,exception):
    return render(request,'404.html',{})
