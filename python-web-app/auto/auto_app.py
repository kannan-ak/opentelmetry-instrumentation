from flask import Flask, render_template, request, redirect, url_for, jsonify as flask_jsonify
import requests
import hvac
import sys
import jsonify # type: ignore
from auto_database import init_db, add_search, get_recent_searches  # Import database functions

app = Flask(__name__)

# Fetch API key from Vault
def fetch_api_key(path):
    client = hvac.Client(url='http://0.0.0.0:8200', token='myvault')
    try:
        secret = client.secrets.kv.v2.read_secret_version(path=path)
        API_KEY = secret['data']['data']['api_key']
        return API_KEY
    except hvac.exceptions.InvalidPath:
        print("Invalid secret path.")
        return None
    except Exception as e:
        print(e.args)
        return None

BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    if request.method == 'POST':

        # Call vault to get the weather api key
        API_KEY = fetch_api_key('weather-app')
        if not API_KEY:
            error = 'Could not retrieve API key from Vault.'
            recent_searches = get_recent_searches()
            return render_template('index.html', weather_data={'error': error}, recent_searches=recent_searches)

        # Fetch user input of city from the ui
        city = request.form['city']
        params = {'q': city, 'appid': API_KEY, 'units': 'metric'}

        # Make a call to openweather and fetch city weather data
        response = requests.get(BASE_URL, params=params)

        if response.status_code == 200:
            weather_data = response.json()
            add_search(
                city=city,
                temperature=weather_data['main']['temp'],
                description=weather_data['weather'][0]['description']
            )
        else:
            weather_data = {'error': 'City not found or invalid API key.'}
    
    recent_searches = get_recent_searches()
    return render_template('index.html', weather_data=weather_data, recent_searches=recent_searches)


@app.route('/weather/<city>', methods=['GET'])
def get_weather_by_city(city):
    # Call vault to get the weather API key
    API_KEY = fetch_api_key('weather-app')
    if not API_KEY:
        return jsonify({'error': 'Could not retrieve API key from Vault.'}), 500

    # Set parameters for the API call
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}

    # Make a call to openweather and fetch city weather data
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        weather_data = response.json()
        add_search(
            city=city,
            temperature=weather_data['main']['temp'],
            description=weather_data['weather'][0]['description']
        )
        return flask_jsonify(weather_data)
    else:
        return flask_jsonify({'error': 'City not found or invalid API key.'}), 404
    

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8081)
