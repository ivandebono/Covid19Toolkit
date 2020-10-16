"""
.. module:: get_data
    :synopsis: Web scraping module for European country data
.. moduleauthor:: Ivan Debono <mail@ivandebono.eu>


This module fetches case, death, and testing time series from 
different sources dataframe containing:
date, cases, deaths, tests


"""
from bs4 import BeautifulSoup
import pandas as pd
from datetime import timedelta
import numpy as np
from io import BytesIO
from zipfile import ZipFile
import urllib.request
import json
import requests
import datetime as dt




#def get_data():

def cumulative2daily(series):
    return series.diff().fillna(series)


def get_daily(column):
    return (column.iloc[column.first_valid_index():]).diff().fillna(column).reset_index(drop=True)

def testplot(df):
    df.plot(x='date',y=['deaths','total','positive'])

def tests_week2day(df):
    
    start_of_tests=df.date.min()-timedelta(days=6)
    dailies=pd.Series(np.array([np.repeat(x1/7,7) for x1 in df.TestedAll.values]).flatten(),name='total').to_frame()
    date=(pd.Series(pd.date_range(start=start_of_tests,end=df.date.max()),name='date').to_frame()).reset_index(drop=True)

    df= date.join(dailies)
    
    return df


def transform_df(df, column, pretty_name):
    """Pick out one column of interest"""
    df = (df
          .rename(columns={"abbreviation_canton_and_fl": "Canton",
                           column: pretty_name,
                           "date": "Date"})
          .pivot_table(index="Date",
                       values=[pretty_name],
                       columns=['Canton'])
         )
    # Create a row for every day
    all_days = pd.date_range(df.index.min(), df.index.max(), freq='D')
    df = df.reindex(all_days)
    # Fill missing values with previous day's number
    df.fillna(method='pad', inplace=True)
    # Now there are only missing values at the start
    # of the series, so set them to zero
    df.fillna(value=0, inplace=True)
    return df


def get_data_Japan():
    JPNurl='https://raw.githubusercontent.com/kaz-ogiwara/covid19/master/data/summary.csv'
    JPN=pd.read_csv(JPNurl,usecols=['year', 'month','date','tested_positive','people_tested','death'])
    JPN.rename(columns={'date':'day'},inplace=True)


    JPN['date']=pd.to_datetime(JPN[['year','month','day']])


    JPN['positive']=get_daily(JPN.tested_positive)
    JPN.positive.clip(0,inplace=True)

    JPN['deaths']=get_daily(JPN.death)
    JPN['total']=get_daily(JPN.people_tested)
    JPN.total.clip(0,inplace=True)
    JPN.drop(columns=['year','month','day','tested_positive','people_tested','death'],inplace=True)
    JPN['state']='Japan'
    
    return JPN



def get_data_UnitedStates(plot=False):
    USurl='https://covidtracking.com/api/v1/us/daily.csv'
    US=pd.read_csv(USurl)
    US['date']=pd.to_datetime(US.date,format='%Y%m%d').dt.normalize()

    US=US[['date','positiveIncrease','deathIncrease','totalTestResultsIncrease']]
    US.rename(columns={'positiveIncrease':'positive','deathIncrease':'deaths','totalTestResultsIncrease':'total'},inplace=True)
    US.sort_values(by='date',inplace=True,ignore_index=True)

    if plot==True:
        US.plot(x='date')

    US['state']='United States'
    US['datasource']='covidtracking.com'
    
    return US


def get_data_Canada(plot=False):
    CNDurl='https://health-infobase.canada.ca/src/data/covidLive/covid19.csv'
    CNDdf=pd.read_csv(CNDurl)
    
    
    CNDdf=CNDdf[CNDdf.prname=='Canada']
    CNDdf.rename(columns={'numtoday':'positive','testedtoday':'total','deathstoday':'deaths'},inplace=True)

    CND=CNDdf[['date','positive','deaths','total']]
    CND=CND.groupby(by='date',as_index=False).sum()
    CND['state']='Canada'
    CND['date']=pd.to_datetime(CND.date,dayfirst=True, infer_datetime_format=True)
    CND['datasource']='health-infobase.canada.ca/src/data/covidLive'

    CND.sort_values(by='date',inplace=True,ignore_index=True)
    
    return CND


def get_data_Poland():

    url='https://docs.google.com/spreadsheets/d/1ierEhD6gcq51HAm433knjnVwey4ZE5DCnu1bW7PRG3E/edit#gid=1723839852'
    file='COVID-19 w Polsce - Testy.csv'
    tests=pd.read_csv(file,header=1)
    to_4digit_str = lambda flt: str(flt).ljust(4,"0")
    datatemp=tests.Data.map(to_4digit_str)
    datetemp=(datatemp.astype(str).str.replace('.', '/'))+'/2020'
    date=pd.to_datetime(datetemp,format='%d/%m/%Y')
    total=(tests['Dobowa liczba wykonanych testów'].fillna(0))
    PLtests=pd.DataFrame({'date':date,'total':total})

    casesfile='COVID-19 w Polsce - Wzrost.csv'
    cases=pd.read_csv(casesfile,header=1)
    to_4digit_str = lambda flt: str(flt).ljust(4,"0")
    datatemp=cases.Data.map(to_4digit_str)
    datetemp=(datatemp.astype(str).str.replace('.', '/'))+'/2020'
    date=pd.to_datetime(datetemp,format='%d/%m/%Y')
    positive=(cases['Nowe przypadki'].str.replace('+','')).astype(float)
    deaths=(cases['Nowe zgony'].str.replace('+','')).astype(float)
    PLcases=pd.DataFrame({'date':date,'positive':positive,'deaths':deaths})

    PL=pd.merge(PLcases,PLtests,on='date',how='outer')
    PL.dropna(inplace=True)
    
    PL['state']='Poland'
    PL['datasource']='http://korona.ws'
    
    return PL

