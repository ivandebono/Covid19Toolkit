"""
.. module:: get_euromomo_data
    :synopsis: Web scraping module for Euromomo.eu data
.. moduleauthor:: Ivan Debono <mail@ivandebono.eu>


This module fetches death and baseline time series from 
www.euromomo.eu and outputs a dataframe containing:
date, deaths, baseline, baseline upper confidence interval, baseline lower confidence interval

It also defines a module to convert calendar week (float) into date (datetime)
* :func:`date_from_calendar_week`

"""


from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
import urllib.parse
from jsonfinder import jsonfinder
import requests
import yaml
import numpy as np
from datetime import date, timedelta


def date_from_calenderweek(year, week):
    first = date(year, 1, 1)
    base = 2 if first.isocalendar()[1] == 1 else 8
    return first + timedelta(days=base - first.isocalendar()[2] + 7 * (week))


def get_euromomo_data():

    EUROurl='https://www.euromomo.eu/graphs-and-maps'

    soup = BeautifulSoup(((requests.get(EUROurl)).text),features="lxml")


    # Get the link to the .js source data for the graphs
    for link in soup.find_all('script'):
        if "src-templates-graphs-and-maps" in str(link.get('src')):
            src_link=link.get('src')
            #print(src_link)


    # Go to the link and scrape data
    parsed=urllib.parse.urlsplit(EUROurl)

    EUROurl_src_link=str(parsed.scheme+'://'+parsed.netloc+src_link)
    print('Data source:',EUROurl_src_link)


    scrape_url = EUROurl_src_link
    content = requests.get(scrape_url).text
    #objects=[]
    for _, __, obj in jsonfinder(content, json_only=True):   
        if 'weeks' in str(obj):
            objects = obj
        

    d=yaml.load(str(objects),Loader=yaml.FullLoader)

    weeks=d['pooled']['weeks']



    d2=yaml.load(str(d['pooled']['groups']),Loader=yaml.FullLoader)
    for i in d2:
        if "group': 'Total'" in str(i):
            #print(i)
            d3=yaml.load(str(i),Loader=yaml.FullLoader)
        
    deaths=np.array(d3['nbc'])

    baseline=np.array(d3['pnb'])
    baseline_upper=np.array(d3['hnr'])
    baseline_lower=np.array(d3['lnr'])

    wk=np.array([date_from_calenderweek(int(w.split('-')[0]),int(w.split('-')[1])) for w in weeks])
    dt=pd.to_datetime(pd.Series(wk),infer_datetime_format=True)


    data=pd.DataFrame({'date':dt,'deaths':deaths,'baseline':baseline,
                       'baseline_upper':baseline_upper,
                      'baseline_lower':baseline_lower})

    return data




