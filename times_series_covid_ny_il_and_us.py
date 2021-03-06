# -*- coding: utf-8 -*-
"""Times Series Covid NY IL and US.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gsTJGIjHfybo3gmhgtvSzIuIReVMLYpw
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

from sklearn.metrics import r2_score, median_absolute_error, mean_absolute_error
from sklearn.metrics import median_absolute_error, mean_squared_error, mean_squared_log_error

from scipy.optimize import minimize
import statsmodels.tsa.api as smt
import statsmodels.api as sm

from tqdm import tqdm_notebook

from itertools import product

def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

import warnings
warnings.filterwarnings('ignore')

# %matplotlib inline

from google.colab import drive

drive.mount('/content/drive')

data = pd.read_csv('/content/drive/My Drive/us-states.csv', index_col=['date'], parse_dates=['date'])
data.head(10)

data.dtypes

data.sort_values(by=['state','date'], inplace=True)

data.head(5)



"""

---


### New York



1.   New cases metrics
2.   Moving average
3.   Exponential smoothing
4.   Double exponential smoothing
5.   Stationarity
6.  





---

"""

NY = data[data.state=='New York']

NY['cases_1'] = NY['cases'].shift(-1)

NY.tail()

"""New cases

"""

NY['New_cases'] = NY['cases_1'] - NY['cases']

NY.shape

plt.figure(figsize=(17, 8))
plt.plot(NY.New_cases)
plt.title('New Cases in CA')
plt.ylabel('New Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

plt.figure(figsize=(17, 8))
plt.plot(NY.cases)
plt.title('Cases in NY')
plt.ylabel('Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

"""### Moving average

"""

def plot_moving_average(series, window, plot_intervals=False, scale=1.96):

    rolling_mean = series.rolling(window=window).mean()
    
    plt.figure(figsize=(17,8))
    plt.title('Moving average\n window size = {}'.format(window))
    plt.plot(rolling_mean, 'g', label='Rolling mean trend')
    
    #Plot confidence intervals for smoothed values
    if plot_intervals:
        mae = mean_absolute_error(series[window:], rolling_mean[window:])
        deviation = np.std(series[window:] - rolling_mean[window:])
        lower_bound = rolling_mean - (mae + scale * deviation)
        upper_bound = rolling_mean + (mae + scale * deviation)
        plt.plot(upper_bound, 'r--', label='Upper bound / Lower bound')
        plt.plot(lower_bound, 'r--')
            
    plt.plot(series[window:], label='Actual values')
    plt.legend(loc='best')
    plt.grid(True)

#Smooth by the previous 7 days (by week)
plot_moving_average(NY.New_cases, 7)

#Smooth by the previous 14 days (by 2-week)
plot_moving_average(NY.New_cases, 14)

#Smooth by the previous 30 days (by month)
plot_moving_average(NY.New_cases, 30)

"""### Exponential smoothing"""

def exponential_smoothing(series, alpha):

    result = [series[0]] # first value is same as series
    for n in range(1, len(series)):
        result.append(alpha * series[n] + (1 - alpha) * result[n-1])
    return result

def plot_exponential_smoothing(series, alphas):
 
    plt.figure(figsize=(17, 8))
    for alpha in alphas:
        plt.plot(exponential_smoothing(series, alpha), label="Alpha {}".format(alpha))
    plt.plot(series.values, "c", label = "Actual")
    plt.legend(loc="best")
    plt.axis('tight')
    plt.title("Exponential Smoothing")
    plt.grid(True);

plot_exponential_smoothing(NY.New_cases, [0.05,0.2, 0.1])

"""### Double exponential smoothing"""

def double_exponential_smoothing(series, alpha, beta):

    result = [series[0]]
    for n in range(1, len(series)+1):
        if n == 1:
            level, trend = series[0], series[1] - series[0]
        if n >= len(series): # forecasting
            value = result[-1]
        else:
            value = series[n]
        last_level, level = level, alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        result.append(level + trend)
    return result

def plot_double_exponential_smoothing(series, alphas, betas):
     
    plt.figure(figsize=(17, 8))
    for alpha in alphas:
        for beta in betas:
            plt.plot(double_exponential_smoothing(series, alpha, beta), label="Alpha {}, beta {}".format(alpha, beta))
    plt.plot(series.values, label = "Actual")
    plt.legend(loc="best")
    plt.axis('tight')
    plt.title("Double Exponential Smoothing")
    plt.grid(True)

plot_double_exponential_smoothing(NY.New_cases, alphas=[0.05, 0.02], betas=[0.3, 0.5])

"""### Stationarity"""

print(NY.New_cases.isna())
NY.New_cases.isna().sum()

NY = NY.dropna()

def tsplot(y, lags=None, figsize=(12, 7), syle='bmh'):
    
    if not isinstance(y, pd.Series):
        y = pd.Series(y)
        
    with plt.style.context(style='bmh'):
        fig = plt.figure(figsize=figsize)
        layout = (2,2)
        ts_ax = plt.subplot2grid(layout, (0,0), colspan=2)
        acf_ax = plt.subplot2grid(layout, (1,0))
        pacf_ax = plt.subplot2grid(layout, (1,1))
        
        y.plot(ax=ts_ax)
        p_value = sm.tsa.stattools.adfuller(y)[1]
        ts_ax.set_title('Time Series Analysis Plots\n Dickey-Fuller: p={0:.5f}'.format(p_value))
        smt.graphics.plot_acf(y, lags=lags, ax=acf_ax)
        smt.graphics.plot_pacf(y, lags=lags, ax=pacf_ax)
        plt.tight_layout()
        
tsplot(NY.New_cases, lags=30)

data_diff = NY.New_cases - NY.New_cases.shift(1)

tsplot(data_diff[1:], lags=30)

data_diff

"""### SARIMA"""

#Set initial values and some bounds
ps = range(0, 5)
d = 1
qs = range(0, 5)
Ps = range(0, 5)
D = 1
Qs = range(0, 5)
s = 5

#Create a list with all possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)
len(parameters_list)

def optimize_SARIMA(parameters_list, d, D, s):
    """
        Return dataframe with parameters and corresponding AIC
        
        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
    """
    
    results = []
    best_aic = float('inf')
    
    for param in tqdm_notebook(parameters_list):
        try: model = sm.tsa.statespace.SARIMAX(NY.New_cases, order=(param[0], d, param[1]),
                                               seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue
            
        aic = model.aic
        
        #Save best model, AIC and parameters
        if aic < best_aic:
            best_model = model
            best_aic = aic
            best_param = param
        results.append([param, model.aic])
        
    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    #Sort in ascending order, lower AIC is better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    
    return result_table

result_table = optimize_SARIMA(parameters_list, d, D, s)

#Set parameters that give the lowest AIC (Akaike Information Criteria)
p, q, P, Q = result_table.parameters[0]

best_model = sm.tsa.statespace.SARIMAX(NY.New_cases, order=(p, d, q),
                                       seasonal_order=(P, D, Q, s)).fit(disp=-1)

print(best_model.summary())



def plot_SARIMA(series, model, n_steps):
    """
        Plot model vs predicted values
        
        series - dataset with time series
        model - fitted SARIMA model
        n_steps - number of steps to predict in the future
    """
    
    NY = series.copy().rename(columns = {'cases': 'actual'})
    NY['arima_model'] = model.fittedvalues
    #Make a shift on s+d steps, because these values were unobserved by the model due to the differentiating
    NY['arima_model'][:s+d] = np.NaN
    
    #Forecast on n_steps forward
    forecast = model.predict(start=NY.shape[0], end=NY.shape[0] + n_steps)
    forecast = NY.arima_model.append(forecast)
    #Calculate error
    error = mean_absolute_percentage_error(NY['actual'][s+d:], NY['arima_model'][s+d:])
    
    plt.figure(figsize=(17, 8))
    plt.title('Mean Absolute Percentage Error: {0:.2f}%'.format(error))
    plt.plot(forecast, color='r', label='model')
    plt.axvspan(NY.index[-1], forecast.index[-1],alpha=0.5, color='lightgrey')
    plt.plot(NY, label='actual')
    plt.legend()
    plt.grid(True);
    
# plot_SARIMA(NY, best_model, 5)
print(best_model.predict(start=269, end=273))
print(mean_absolute_percentage_error(NY.New_cases[s+d:], best_model.fittedvalues[s+d:]))

def plot_SARIMA(series, model, n_steps):
    """
        Plot model vs predicted values
        
        series - dataset with time series
        model - fitted SARIMA model
        n_steps - number of steps to predict in the future
    """
    
    NY = series.copy().rename(columns = {'cases': 'actual'})
    NY['arima_model'] = model.fittedvalues
    #Make a shift on s+d steps, because these values were unobserved by the model due to the differentiating
    NY['arima_model'][:s+d] = np.NaN
    
    #Forecast on n_steps forward
    forecast = model.predict(start=NY.shape[0], end=NY.shape[0] + n_steps)
    forecast = NY.arima_model.append(forecast)
    #Calculate error
    error = mean_absolute_percentage_error(NY['actual'][s+d:], NY['arima_model'][s+d:])
    
    plt.figure(figsize=(17, 8))
    plt.title('Mean Absolute Percentage Error: {0:.2f}%'.format(error))
    plt.plot(forecast, color='r', label='model')
    plt.axvspan(NY.index[-1], forecast.index[-1],alpha=0.5, color='lightgrey')
    plt.plot(NY, label='actual')
    plt.legend()
    plt.grid(True);
    
# plot_SARIMA(NY, best_model, 5)
print(best_model.predict(start=233, end=238))
print(mean_absolute_percentage_error(NY.New_cases[s+d:], best_model.fittedvalues[s+d:]))

nypredicted = pd.DataFrame(best_model.predict(start=50, end=238))
nypredicted = nypredicted.iloc[:,[0]]
nypredicted.head()

nypredictedactual = pd.concat([nypredicted,NY[['New_cases']]], axis=0, ignore_index=False)
nypredictedactual.head()

NY.New_cases.shape[0]

NY.tail()

#November
comparisonNYNov = pd.DataFrame({'actual': [2029, 1629, 1636, 2058, 1633],
                          'predicted': [2665, 2542, 2567, 2513, 2714]}, 
                          index = pd.date_range(start='2020-10-20', periods=5,))

#October
comparisonNYOct = pd.DataFrame({'actual': [2029, 1629, 1636, 2058, 1633],
                          'predicted': [1437, 1839, 1360, 1563, 1859]}, 
                          index = pd.date_range(start='2020-10-20', periods=5,))

#mape
np.mean(np.abs((comparisonNYOct.actual - comparisonNYOct.predicted) / comparisonNYOct.actual)) * 100
#MAPE < 10% is Excellent, MAPE < 20% is Good

comparison.head()

plt.figure(figsize=(17, 8))
plt.plot(comparison.actual, label = 'actual')
plt.plot(comparison.predicted, label = 'predicted November')
plt.plot(comparisonO.predicted, label = 'predicted October')
plt.title('Predicted New cases vs. Actual New cases')
plt.ylabel('New cases')
plt.xlabel('Date')
plt.ylim(ymin=0)

plt.legend(loc='best')
plt.grid(False)
plt.show()



sarima_mae = mean_absolute_percentage_error(comparisonO.predicted, comparisonO.actual)
sarima_mae

sklearn.metrics.mean_absolute_percentage_error(comparison0.predicted, comparison0.actual)

"""

---


### Illinois"""

IL = data[data.state=='Illinois']
IL['cases_1'] = IL['cases'].shift(-1)
IL['New_cases'] = IL['cases_1'] - IL['cases']

plt.figure(figsize=(17, 8))
plt.plot(IL.New_cases)
plt.title('New Cases in IL')
plt.ylabel('New Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

plt.figure(figsize=(17, 8))
plt.plot(IL.cases)
plt.title('Cases in IL')
plt.ylabel('Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

print(IL.New_cases.isna())
IL.New_cases.isna().sum()
IL = IL.dropna()

def tsplot(y, lags=None, figsize=(12, 7), syle='bmh'):
    
    if not isinstance(y, pd.Series):
        y = pd.Series(y)
        
    with plt.style.context(style='bmh'):
        fig = plt.figure(figsize=figsize)
        layout = (2,2)
        ts_ax = plt.subplot2grid(layout, (0,0), colspan=2)
        acf_ax = plt.subplot2grid(layout, (1,0))
        pacf_ax = plt.subplot2grid(layout, (1,1))
        
        y.plot(ax=ts_ax)
        p_value = sm.tsa.stattools.adfuller(y)[1]
        ts_ax.set_title('Time Series Analysis Plots\n Dickey-Fuller: p={0:.5f}'.format(p_value))
        smt.graphics.plot_acf(y, lags=lags, ax=acf_ax)
        smt.graphics.plot_pacf(y, lags=lags, ax=pacf_ax)
        plt.tight_layout()
        
tsplot(IL.New_cases, lags=30)

data_diff = IL.New_cases - IL.New_cases.shift(1)

tsplot(data_diff[1:], lags=30)

#Set initial values and some bounds
ps = range(0, 5)
d = 1
qs = range(0, 5)
Ps = range(0, 5)
D = 1
Qs = range(0, 5)
s = 5

#Create a list with all possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)
len(parameters_list)

def optimize_SARIMA(parameters_list, d, D, s):
    """
        Return dataframe with parameters and corresponding AIC
        
        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
    """
    
    results = []
    best_aic = float('inf')
    
    for param in tqdm_notebook(parameters_list):
        try: model = sm.tsa.statespace.SARIMAX(IL.New_cases, order=(param[0], d, param[1]),
                                               seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue
            
        aic = model.aic
        
        #Save best model, AIC and parameters
        if aic < best_aic:
            best_model = model
            best_aic = aic
            best_param = param
        results.append([param, model.aic])
        
    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    #Sort in ascending order, lower AIC is better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    
    return result_table

result_table = optimize_SARIMA(parameters_list, d, D, s)

#Set parameters that give the lowest AIC (Akaike Information Criteria)
p, q, P, Q = result_table.parameters[0]

best_model = sm.tsa.statespace.SARIMAX(IL.New_cases, order=(p, d, q),
                                       seasonal_order=(P, D, Q, s)).fit(disp=-1)

print(best_model.summary())

def plot_SARIMA(series, model, n_steps):
    """
        Plot model vs predicted values
        
        series - dataset with time series
        model - fitted SARIMA model
        n_steps - number of steps to predict in the future
    """
    
    IL = series.copy().rename(columns = {'cases': 'actual'})
    IL['arima_model'] = model.fittedvalues
    #Make a shift on s+d steps, because these values were unobserved by the model due to the differentiating
    IL['arima_model'][:s+d] = np.NaN
    
    #Forecast on n_steps forward
    forecast = model.predict(start=IL.shape[0], end=IL.shape[0] + n_steps)
    forecast = IL.arima_model.append(forecast)
    #Calculate error
    error = mean_absolute_percentage_error(IL['actual'][s+d:], IL['arima_model'][s+d:])
    
    plt.figure(figsize=(17, 8))
    plt.title('Mean Absolute Percentage Error: {0:.2f}%'.format(error))
    plt.plot(forecast, color='r', label='model')
    plt.axvspan(IL.index[-1], forecast.index[-1],alpha=0.5, color='lightgrey')
    plt.plot(IL, label='actual')
    plt.legend()
    plt.grid(True);
    
# plot_SARIMA(NY, best_model, 5)
print(best_model.predict(start=300, end=305))
print(mean_absolute_percentage_error(IL.New_cases[s+d:], best_model.fittedvalues[s+d:]))

IL.tail()

#November
comparison = pd.DataFrame({'actual': [4009, 4960, 5014, 5900, 4031],
                          'predicted': [7803, 7877, 8056, 8088, 8146]}, 
                          index = pd.date_range(start='2020-10-20', periods=5,))

#October
comparisonO = pd.DataFrame({'actual': [4009, 4960, 5014, 5900, 4031],
                          'predicted': [3989, 4243, 4481, 5139, 5167]}, 
                          index = pd.date_range(start='2020-10-20', periods=5,))

plt.figure(figsize=(17, 8))
plt.plot(comparison.actual, label = 'actual')
plt.plot(comparison.predicted, label = 'predicted November')
plt.plot(comparisonO.predicted, label = 'predicted October')
plt.title('Predicted New cases vs. Actual New cases')
plt.ylabel('New cases')
plt.xlabel('Date')
plt.ylim(ymin=0)

plt.legend(loc='best')
plt.grid(False)
plt.show()

#mape
np.mean(np.abs((comparisonO.actual - comparisonO.predicted) / comparisonO.actual)) * 100
#MAPE < 10% is Excellent, MAPE < 20% is Good

"""###United States

"""

US = pd.read_csv('/content/drive/My Drive/us.csv', index_col=['date'], parse_dates=['date'])
US.head(5)

US['cases_1'] = US['cases'].shift(-1)
US['New_cases'] = US['cases_1'] - US['cases']
US['New_cases_log'] = np.log(US['New_cases'])

plt.figure(figsize=(17, 8))
plt.plot(US.New_cases)
plt.plot(US.New_cases_log)
plt.title('New Cases in US')
plt.ylabel('New Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

plt.figure(figsize=(17, 8))
plt.plot(US.cases)
plt.title('Cases in US')
plt.ylabel('Cases')
plt.xlabel('Date')
plt.grid(False)
plt.show()

print(US.New_cases.isna())
US.New_cases.isna().sum()
US = US.dropna()

def tsplot(y, lags=None, figsize=(12, 7), syle='bmh'):
    
    if not isinstance(y, pd.Series):
        y = pd.Series(y)
        
    with plt.style.context(style='bmh'):
        fig = plt.figure(figsize=figsize)
        layout = (2,2)
        ts_ax = plt.subplot2grid(layout, (0,0), colspan=2)
        acf_ax = plt.subplot2grid(layout, (1,0))
        pacf_ax = plt.subplot2grid(layout, (1,1))
        
        y.plot(ax=ts_ax)
        p_value = sm.tsa.stattools.adfuller(y)[1]
        ts_ax.set_title('Time Series Analysis Plots\n Dickey-Fuller: p={0:.5f}'.format(p_value))
        smt.graphics.plot_acf(y, lags=lags, ax=acf_ax)
        smt.graphics.plot_pacf(y, lags=lags, ax=pacf_ax)
        plt.tight_layout()
        
tsplot(US.New_cases, lags=30)

data_diff = US.New_cases - US.New_cases.shift(1)

tsplot(data_diff[1:], lags=30)

#Set initial values and some bounds
ps = range(0, 5)
d = 1
qs = range(0, 5)
Ps = range(0, 5)
D = 1
Qs = range(0, 5)
s = 5

#Create a list with all possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)
len(parameters_list)

def optimize_SARIMA(parameters_list, d, D, s):
    """
        Return dataframe with parameters and corresponding AIC
        
        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
    """
    
    results = []
    best_aic = float('inf')
    
    for param in tqdm_notebook(parameters_list):
        try: model = sm.tsa.statespace.SARIMAX(US.New_cases, order=(param[0], d, param[1]),
                                               seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue
            
        aic = model.aic
        
        #Save best model, AIC and parameters
        if aic < best_aic:
            best_model = model
            best_aic = aic
            best_param = param
        results.append([param, model.aic])
        
    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    #Sort in ascending order, lower AIC is better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    
    return result_table

result_table = optimize_SARIMA(parameters_list, d, D, s)

def plot_SARIMA(series, model, n_steps):

    US = series.copy().rename(columns = {'cases': 'actual'})
    US['arima_model'] = model.fittedvalues
    #Make a shift on s+d steps, because these values were unobserved by the model due to the differentiating
    US['arima_model'][:s+d] = np.NaN
    
    #Forecast on n_steps forward
    forecast = model.predict(start=US.shape[0], end=US.shape[0] + n_steps)
    forecast = US.arima_model.append(forecast)
    #Calculate error
    error = mean_absolute_percentage_error(US['actual'][s+d:], US['arima_model'][s+d:])
    
    plt.figure(figsize=(17, 8))
    plt.title('Mean Absolute Percentage Error: {0:.2f}%'.format(error))
    plt.plot(forecast, color='r', label='model')
    plt.axvspan(US.index[-1], forecast.index[-1],alpha=0.5, color='lightgrey')
    plt.plot(US, label='actual')
    plt.legend()
    plt.grid(True)

print(best_model.predict(start=307, end=311))
print(mean_absolute_percentage_error(US.New_cases[s+d:], best_model.fittedvalues[s+d:]))

US.tail()

#November
comparisonUSNov = pd.DataFrame({'actual': [74428, 81902, 90728, 99784, 84285],
                          'predicted': [8250, 8423, 8448, 8501, 8531]}, 
                          index = pd.date_range(start='2020-10-25', periods=5,))

#October
comparisonUSOct = pd.DataFrame({'actual': [74428, 81902, 90728, 99784, 84285],
                          'predicted': [5015, 5225, 5628, 5628, 5821]}, 
                          index = pd.date_range(start='2020-10-25', periods=5,))

plt.figure(figsize=(17, 8))
plt.plot(comparisonUSOct.actual, label = 'actual')
plt.plot(comparisonUSNov.predicted, label = 'predicted November')
plt.plot(comparisonUSOct.predicted, label = 'predicted October')
plt.title('Predicted New cases vs. Actual New cases')
plt.ylabel('New cases')
plt.xlabel('Date')
plt.ylim(ymin=0)

plt.legend(loc='best')
plt.grid(False)
plt.show()

#mape
np.mean(np.abs((comparisonUSOct.actual - comparisonUSOct.predicted) / comparisonUSOct.actual)) * 100
#MAPE < 10% is Excellent, MAPE < 20% is Good

import pandas as pd
data = pd.read_excel('business ethics.xlsx', names = ['state', 'hospit_14_days', 'deaths_14_days'])
data.head()

df['DataFrame Column'].dtypes

data['state'] = data['state'].astype('str')

data.hospit_14_days = data.hospit_14_days.astype(float)

y = data.state
x = data.hospit_14_days

plt.bar(x, y, color = 'blue')

plt.figure(figsize=(8, 17))

plt.show()
#plt.plot(data.hospit_14_days)
#plt.plot(data.state)
#plt.title('Percentage Change in Hospitilizations Across Last 14 days')
#plt.ylabel('State')
#plt.xlabel('Percentage Change in Hospitilizations')
#plt.ylim(ymin=0)

#plt.legend(loc='best')
#plt.grid(False)
#plt.show()