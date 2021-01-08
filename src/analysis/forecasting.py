import pandas as pd
import os
import numpy as np
from datetime import datetime,date
from dateutil import relativedelta
import math
import argparse
import matplotlib.pyplot as plt
import copy
import pickle as pkl
import operator

from pandas.plotting import autocorrelation_plot
from statsmodels.tsa.arima_model import ARIMA
import statsmodels.api as sm
import itertools

# This function was supposed to forecast prices and demand based on SARIMA function.
# As it presents much worse solutions than Prophet, it wasn't used.
# Hyperparameters were chosen by previously done grid search method.

def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))

def plot_mean_and_CI(mean, lb, ub, color_mean=None, color_shading=None):
    # plot the shaded range of the confidence intervals
    plt.fill_between(range(mean.shape[0]), ub, lb,
                     color=color_shading, alpha=.5)
    # plot the mean on top
    plt.plot(mean, color_mean)

def forecast_prices(gas_data,
                    data_since = '2012-01-01', 
                    data_till = '2012-12-31',
                    forecasting_since = '2013-01-01',
                    forecasting_till = '2013-04-01',
                    ARIMA_order = (3,1,3),
                    ARIMA_season_order = (2,2,3,7)
                    ):
    """
    Here: a bit of comments on what this function does
    """
    data_since = pd.to_datetime(data_since)
    data_till = pd.to_datetime(data_till)
    forecasting_since = pd.to_datetime(forecasting_since)
    forecasting_till = pd.to_datetime(forecasting_till)

    series = gas_data.loc[data_since:data_till]

    # fit model
    model = sm.tsa.statespace.SARIMAX(series,
                                      order=ARIMA_order,
                                      seasonal_order=ARIMA_season_order,
                                      enforce_stationarity=False,
                                      enforce_invertibility=False)
    model_fit = model.fit(disp=0)
    
    pred = model_fit.get_prediction(start=forecasting_since, end=forecasting_till, dynamic=False)
    pred_ci = pred.conf_int()    
    return pred_ci

def forecast_demand(gas_data,
                    data_since = '2012-01-01', 
                    data_till = '2012-12-31',
                    forecasting_since = '2013-01-01',
                    forecasting_till = '2013-04-01',
                    ARIMA_order = (3,1,3),
                    ARIMA_season_order = (2,2,3,7)
                    ):
    """
    Here: a bit of comments on what this function does
    """
    data_since = pd.to_datetime(data_since)
    data_till = pd.to_datetime(data_till)
    forecasting_since = pd.to_datetime(forecasting_since)
    forecasting_till = pd.to_datetime(forecasting_till)

    # fit model
    model = sm.tsa.statespace.SARIMAX(gas_data,
                                      order=ARIMA_order,
                                      seasonal_order=ARIMA_season_order,
                                      enforce_stationarity=False,
                                      enforce_invertibility=False)
    model_fit = model.fit(disp=0)
    
    pred = model_fit.get_prediction(start=forecasting_since, end=forecasting_till, dynamic=False)
    pred_ci = pred.conf_int()    
    return pred_ci