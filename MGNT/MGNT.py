import numpy as np
import pandas as pd
import datetime as dt
import re

from os import listdir
from os.path import isfile, join
import copy

import matplotlib.pyplot as plt

stock_name = "MGNT"
S = 101911355 #Кол-во акций в обращении

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

#Фьючерсы, дневной датасет
Futures_daily = pd.DataFrame(index = daily_index)

for j in listdir("Finam"):
    future_Finam = pd.read_csv(f'Finam/{j}', sep=";", header=0, names = Finam_headers)
    instrument = Future_to_MOEX(j, 'MN')

    future_Finam["Hour"]= future_Finam["Hour"].replace(0, "000000")
    future_Finam.index = pd.to_datetime(future_Finam["Date"].astype(str) + future_Finam["Hour"].astype(str), format = '%Y%m%d%H%M%S')
    future_Finam.index  = future_Finam.index - dt.timedelta(seconds=1)

    future_MOEX = pd.read_csv(f'MOEX/{instrument}-ru.csv', sep=";", encoding = 'CP1251')
    future_MOEX.index = pd.to_datetime(future_MOEX["Дата"], format = "%d.%m.%Y")
    future_MOEX["Open_con"] = future_MOEX['Объем открытых позиций, контр.']
    future_MOEX["Open_pos"] = future_MOEX['Объем открытых позиций, руб.']
    future_MOEX = future_MOEX[["Open_pos", "Open_con"]]

    F_daily_index = np.unique(future_Finam.index.date)
    Futures_columns = ['Open', 'Close', 'High', 'Low', 'Vol', 'Log_returns', 'Amihud', 'LHH', 'LIX','VAR' , 'VAR_21', 'MACD', 'EMA_21', 'MA_21', 'Open_pos', 'Open_con']
    future_daily = pd.DataFrame(index = F_daily_index, columns=Futures_columns)
    

    for i in F_daily_index:
        day = future_Finam[future_Finam.index.date == i]
        day_M = future_MOEX[future_MOEX.index.date == i]
        future_daily["High"][i] = max(day["High"])
        future_daily["Low"][i] = min(day["Low"])
        future_daily["Open"][i] = day["Open"][0]
        future_daily["Close"][i] = day["Close"][-1]
        future_daily["Vol"][i] = sum(day["Vol"])
        future_daily['Log_returns'][i] = np.log(day["Close"][-1]) - np.log(day["Open"][0])
        future_daily['Amihud'][i] = sum(abs(day["Close"] - day["Open"]) / (day["Close"] * day["Vol"])) / len(day)
        future_daily['LHH'][i] = (max(day["High"]) - min(day["Low"])) / min(day["Low"]) / (sum(day["Vol"]) / day_M["Open_con"][0])
        future_daily['VAR'][i] = np.sqrt(sum((np.log(day["Close"]) - np.log(day["Open"]))**2) / len(day))
        future_daily['Open_pos'][i] = day_M['Open_pos'][0]
        future_daily['Open_con'][i] = day_M['Open_con'][0]

    future_daily['LIX'] = np.log10(list((future_daily['Vol'] * future_daily["Close"]) / (future_daily['High'] - future_daily['Low'])))
    future_daily['VAR_21'] = np.sqrt(future_daily['Log_returns'].rolling(21).var())
    future_daily['MACD'] = (future_daily["Close"].ewm(com = 12).mean()-
                       future_daily["Close"].ewm(span = 26).mean())
    future_daily['EMA_21'] = future_daily["Close"].ewm(span = 21).mean().pct_change() 
    future_daily['MA_21'] = future_daily["Close"].rolling(window=21).mean().pct_change() 
    future_daily['Vol'] = future_daily['Vol'].pct_change() 
    future_daily['Open_pos'] = future_daily['Open_pos'].pct_change()
    future_daily['Open_con'] = future_daily['Open_con'].pct_change()

    new_headers = []
    for s in future_daily.columns:
        new_headers.append(instrument + "_" + s)
    future_daily.columns = new_headers   

    Futures_daily = pd.merge(Futures_daily, future_daily, how = "left", left_index=True, right_index=True) #Склеивем


####Ближайший фьючерс по экспирации
Exp_date = Futures_daily[Futures_daily.filter(like='_Log_returns').columns].apply(lambda column: column.dropna().index[-1]) #[1:-1] чтобы избавиться от фьючерса 12.18

closest = []
i = stock_daily.index[0]
for i in stock_daily.index:
    #closest.append(Exp_date[Exp_date >= i].min())
    closest.append(Exp_date[Exp_date == Exp_date[Exp_date >= i].min()].index[0].replace("_Log_returns", ""))

stock_daily["Closest"] = closest
####


#Итоговый датасет
Final_data = pd.DataFrame(index = daily_index)
Final_data = pd.merge(Final_data, stock_daily, how = "left", left_index=True, right_index=True) #Склеивем

Futures_columns = ['Open', 'Close', 'High', 'Low', 'Vol', 'Log_returns', 'Amihud', 'LHH', 'LIX','VAR' , 'VAR_21', 'MACD', 'EMA_21', 'MA_21', 'Open_pos', 'Open_con']
Futures_columns = ["F_" + s for s in Futures_columns]
Final_future = pd.DataFrame(index = daily_index, columns=Futures_columns)
for i in daily_index:
    like = Final_data["Closest"][i]
    Final_future.loc[i] = list(Futures_daily[Futures_daily.filter(like=like).columns].loc[i])

Finale = pd.merge(Final_data, Final_future, how = "left", left_index=True, right_index=True) #Склеивем
Finale = Finale.drop(["Closest"], axis = 1)
Finale.to_csv(f"{stock_name}.csv", sep=';', index=True)
