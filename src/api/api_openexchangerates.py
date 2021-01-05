import requests

APP_ID = 'd74c1ab7e73843ea9c595d1d489a57bb'

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
