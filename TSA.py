import numpy as np 
import pandas as pd 
import math
import datetime

#-------------------------------#

## Reading files

Cons = pd.read_html('consumption-dk-areas_2018_hourly.xls')[0]
Prices = pd.read_html('elspot-prices_2018_hourly_dkk.xls')[0]

#-------------------------------#

## Data preprocessing

# Indexing

Cons.columns = ['Date', 'Hour', 'DK1', 'DK2', 'DK']
Prices = Prices.iloc[:,[0,1,8,9]]
Prices.columns = ['Date','Hour','DK1','DK2']

# Formatting dates
Cons['Date'] = pd.to_datetime(Cons['Date'])
Prices['Date'] = pd.to_datetime(Prices['Date'])

# Formatting hours
#Cons[,1] = int(Cons.iloc[:,1])