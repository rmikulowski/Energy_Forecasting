import requests
import xmltodict
import pandas as pd
from datetime import timedelta
import configparser
import os

# CONFIG
config = configparser.ConfigParser()
api_filename = os.path.dirname(os.path.dirname(os.getcwd())) + "\\api.cfg"
config.read(api_filename)

processtype = {
    'A25':	'GeneralCapacityInformation',
    'A53':	'PlannedMaintenance',
    'A54':	'UnplannedOutage'
}

documenttype = {
    'A44':	'PriceDocument',
    'A65':	'SystemTotalLoad',
    'A69':	'WindSolarForecast',
    'A71':	'GenerationForecast',
    'A73':	'ActualGeneration',
    'A74':	'WindSolarGeneration',
    'A75':	'ActualGenerationType',
    'A76':	'LoadUnavailability',
    'A77':	'ProductionUnavailability',
    'A80':	'GenerationUnavailability',
    'A78':	'TransmissionUnavailability',
    'A85':	'ImbalancePrices',
    'A86':	'ImbalanceVolume',
    'A88':	'CrossBorderBalancing'
}

"""
A.2. Contract_MarketAgreement.Type, Type_MarketAgreement.Type
    A01 Daily
    A13 Hourly (Type_MarketAgreement.Type only)

A.6. BusinessType
    A25	General Capacity Information
    A53	Planned maintenance
    A54	Unplanned outage

A.7. ProcessType
    A01	Day ahead
    A16	Realised

A.10. Areas
    10YDOM-1001A082L - PL-CZ BZA / CA
    10YPL-AREA-----S - Poland, PSE SA BZ / BZA / CA / MBA
    10Y1001A1001A65H - Denmark
    10YDK-1--------W - DK1 BZ / MBA
    10YDK-2--------M - DK2 BZ / MBA
    10Y1001A1001A796 - Denmark, Energinet CA

A.9. DocumentType
    A44	Price Document
    A65	System total load
    A69	Wind and solar forecast
    A71	Generation forecast
    A73	Actual generation
    A74	Wind and solar generation
    A75	Actual generation per type
    A76	Load unavailability
    A77	Production unavailability
    A80	Generation unavailability
    A78	Transmission unavailability
    A85	Imbalance prices
    A86	Imbalance volume
    A88	Cross border balancing

periodStart=20181231
periodEnd=20191231

FINAL EXAMPLE: 
- Day-ahead Generation Forecasts for Wind and Solar
/api?documentType=A69&processType=A01&psrType=B16&in_Domain=10YCZ-CEPS-----N&periodStart=201512312300&periodEnd=201612312300

- Actual Generation Output per Generation Unit 
/api?documentType=A73&processType=A16&psrType=B02&in_Domain=10YCZ-CEPS-----N&periodStart=201512312300&periodEnd=201601012300
"""

if __name__ == "__main__":
    """
    To run the script,:
    - go to the entsoe_api dir,
    - run "python api_entsoe.py"
    
    App ID is required, which needs to be received from ENTSO-E after requested.

    Output: csv file to be analysed, saved in 'data/outputs' directory.
    """

    APP_ID = list(config['ENTSOE'].values())[0]
    PATH = 'https://transparency.entsoe.eu/api?securityToken='

    START_TIME = 201512312300
    END_TIME = 201912312300
    ZONE = '10YPL-AREA-----S'
    DOCUMENT_TYPE = 'A75'
    PROCESS_TYPE = 'A16'

    FINAL_STRING = f'{PATH}{APP_ID}&documentType={DOCUMENT_TYPE}&processType={PROCESS_TYPE}&in_Domain={ZONE}&periodStart={START_TIME}&periodEnd={END_TIME}'

    response = requests.get(FINAL_STRING)
    o = xmltodict.parse(response.content)

    time_indices = []
    values = []
    for i in (o['GL_MarketDocument']['TimeSeries']):
        for j in (i['Period']['Point']):
            j_index = pd.to_datetime(i['Period']['timeInterval']['start']) + timedelta(hours = int(j['position']))
            j_value = int(j['quantity'])
            time_indices.append(j_index)
            values.append(j_value)

    final_data = pd.DataFrame(index = time_indices, data = values)
    final_data.to_csv(f'./data/outputs/{DOCUMENT_TYPE}_{PROCESS_TYPE}_{ZONE}_{START_TIME}_{END_TIME}.csv')
