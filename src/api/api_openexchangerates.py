import requests
import configparser
import os


if __name__ == '__main__':
    """
    This script is just to make sure that config and connection to some API works.
    """
    # CONFIG
    config = configparser.ConfigParser()
    api_filename = os.path.dirname(os.path.dirname(os.getcwd())) + "\\api.cfg"
    config.read(api_filename)


    APP_ID = list(config['EXCHANGE'].values())[0]

    # # Time series
    # ENDPOINT = 'https://openexchangerates.org/api/time-series.json'
    # START_DATE = '2019-01-01'
    # END_DATE = '2020-01-01'
    # BASE = 'PLN'
    # SYMBOLS = 'EUR, DKK, USD'

    # response = requests.get(f'{ENDPOINT}?app_id={APP_ID}&start={START_DATE}&end={END_DATE}&base={BASE}&symbols={SYMBOLS}&prettyprint=1')
    # print(response)

    # exchange_rates = response.json()['rates']
    # print(exchange_rates['2019-01-01'])

    # Latest
    ENDPOINT = 'https://openexchangerates.org/api/latest.json'
    SYMBOLS = 'EUR, DKK, USD, PLN'

    response = requests.get(f'{ENDPOINT}?app_id={APP_ID}')
    print(response)

    exchange_rates = response.json()['rates']
    print(exchange_rates['PLN'], exchange_rates['DKK'])
