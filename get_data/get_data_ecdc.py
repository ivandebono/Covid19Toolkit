   
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_data_ecdc_tests(url='https://www.ecdc.europa.eu/en/publications-data/covid-19-testing'):

    data = requests.get(f"{url}")
    parsed = BeautifulSoup(data.text, "html.parser")
    link = parsed.find("a", href=re.compile(".xlsx"))
    EUtesturl = link["href"]
    EUtestdf=pd.read_excel(EUtesturl)
    EUtestdf.replace({'Czechia':'Czech Republic'},inplace=True)

    return EUtestdf


def get_data_ecdc_hosp(url='https://www.ecdc.europa.eu/en/publications-data/download-data-hospital-and-icu-admission-rates-and-current-occupancy-covid-19'):

    data = requests.get(f"{url}")
    parsed = BeautifulSoup(data.text, "html.parser")
    link = parsed.find("a", href=re.compile(".xlsx"))
    EUhospurl = link["href"]
    EUhospdf=pd.read_excel(EUhospurl)
    EUhospdf.replace({'Czechia':'Czech Republic'},inplace=True)

    return EUhospdf


def get_data_ecdc_response(url='https://www.ecdc.europa.eu/en/publications-data/download-data-response-measures-covid-19'):

    data = requests.get(f"{url}")
    parsed = BeautifulSoup(data.text, "html.parser")
    link = parsed.find("a", href=re.compile(".csv"))
    EUurl = link["href"]
    EUdf=pd.read_csv(EUurl)
    EUdf.replace({'Czechia':'Czech Republic'},inplace=True)

    return EUdf

