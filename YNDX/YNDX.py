import numpy as np
import pandas as pd
import datetime as dt
import re

from os import listdir
from os.path import isfile, join
import copy

import matplotlib.pyplot as plt

stock_name = "YNDX"
S = 355995773 #Кол-во акций в обращении

MOEX_per = dict([('319', 'H9'),
                ('619', 'M9'),
                ('919', 'U9'),
                ('1219', 'Z9'),
                ('320', 'H0'),
                ('620', 'M0'),
                ('920', 'U0'),
                ('1220', 'Z0'),
                ('321', 'H1'),
                ('621', 'M1'),
                ('921', 'U1'),
                ('1221', 'Z1')])
#ФУНКЦИИ
def Future_to_MOEX(x, name):
    x = x.replace("_180901_210411.txt", "")
    x = re.sub("[^0-9]*", "", x)
    return name + MOEX_per[x]

###########
Finam_headers = ["Ticker", "Per", "Date", "Hour", "Open", "High", "Low", "Close", "Vol"]
stock = pd.read_csv(f'{stock_name}_190101_210411.txt', sep=";", header=0, names = Finam_headers)

stock["Hour"] = stock["Hour"].replace(0, "000000")
stock.index = pd.to_datetime(stock["Date"].astype(str) + stock["Hour"].astype(str), format = '%Y%m%d%H%M%S')
stock.index = stock.index - dt.timedelta(seconds=1)  ####Сдвиг на 1 секунду назад чтобы избежать 000000 часов как новый день
#Stock готов


#Акции дневной датасет
daily_index = np.unique(stock.index.date)
Stock_columns = ['Open', 'Close', 'High', 'Low', 'Vol', 'Log_returns', 'Amihud', 'LHH', 'LIX', 'VAR', 'VAR_21']
stock_daily = pd.DataFrame(index = daily_index, columns=Stock_columns)

for i in daily_index:
    day = stock[stock.index.date == i]
    stock_daily["High"][i] = max(day["High"])
    stock_daily["Low"][i] = min(day["Low"])
    stock_daily["Low"][i] = day["Close"][-1]
    stock_daily["Open"][i] = day["Open"][0]
    stock_daily["Close"][i] = day["Close"][-1]
    stock_daily["Vol"][i] = sum(day["Vol"])
    stock_daily['Log_returns'][i] = np.log(day["Close"][-1]) - np.log(day["Open"][0])
    stock_daily['Amihud'][i] = sum(abs(day["Close"] - day["Open"]) / (day["Close"] * day["Vol"])) / len(day)
    stock_daily['LHH'][i] = (max(day["High"]) - min(day["Low"])) / min(day["Low"]) / (sum(day["Vol"]) / S)
    stock_daily['VAR'][i] = np.sqrt(sum((np.log(day["Close"]) - np.log(day["Open"]))**2) / len(day))

stock_daily['LIX'] = np.log10(list((stock_daily['Vol'] * stock_daily["Close"]) / (stock_daily['High'] - stock_daily['Low'])))
stock_daily['MACD'] = (stock_daily["Close"].ewm(com = 12).mean()-
                       stock_daily["Close"].ewm(span = 26).mean())
stock_daily['EMA_21'] = stock_daily["Close"].ewm(span = 21).mean().pct_change() 
stock_daily['MA_21'] = stock_daily["Close"].rolling(window=21).mean().pct_change() 
stock_daily['Vol'] = stock_daily['Vol'].pct_change()
stock_daily['VAR_21'] = np.sqrt(stock_daily["Log_returns"].rolling(window=21).var())
#Ещё индикаторы для акций


#Итоговый датасет
Final_data = pd.DataFrame(index = daily_index)
Final_data = pd.merge(Final_data, stock_daily, how = "left", left_index=True, right_index=True) #Склеивем
Final_data.to_csv(f"{stock_name}.csv", sep=';', index=True)
