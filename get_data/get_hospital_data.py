import pandas as pd
import numpy as np

def get_hosp_France():
    url='https://www.data.gouv.fr/en/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7'
    fr=pd.read_csv(url,delimiter=';')
    fr=fr[fr.sexe==0]
    fr=fr.groupby(by='jour',as_index=False).sum()
    fr['date']=pd.to_datetime(fr.jour)
    current=fr.sort_values(by='date')
    
    
    
    url='https://www.data.gouv.fr/en/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c'
    fr=pd.read_csv(url,delimiter=';')
    #fr=fr[fr.sexe==0]
    fr=fr.groupby(by='jour',as_index=False).sum()
    fr['date']=pd.to_datetime(fr.jour)
    daily=fr.sort_values(by='date')

    daily['avg_incid_hosp']=daily.incid_hosp.rolling(window=7).mean()
    daily['avg_incid_rea']=daily.incid_rea.rolling(window=7).mean()
    daily['avg_incid_dc']=daily.incid_dc.rolling(window=7).mean()
    daily['avg_incid_rad']=daily.incid_rad.rolling(window=7).mean()



    daily['diff_incid_hosp']=daily.incid_hosp.diff().fillna(daily.incid_hosp)
    daily['diff_incid_rea']=daily.incid_rea.diff().fillna(daily.incid_rea)
    daily['diff_incid_dc']=daily.incid_dc.diff().fillna(daily.incid_dc)
    daily['diff_incid_rad']=daily.incid_rad.diff().fillna(daily.incid_rad)
    
    return current,daily



def get_hosp_UK():

    UKurl2='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=nation&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22newAdmissions%22:%22newAdmissions%22,%22cumAdmissions%22:%22cumAdmissions%22%7D&format=csv'
    UKdaily=pd.read_csv(UKurl2)
    UKdaily=UKdaily.groupby(by='date',as_index=False).sum()
    UKdaily=pd.DataFrame({'date':pd.to_datetime(UKdaily.date),'hospitaladmissions':UKdaily.newAdmissions})
    
    UKurl='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22hospitalCases%22:%22hospitalCases%22%7D&format=csv'
    UKcurrent=pd.read_csv(UKurl)
    UKcurrent=pd.DataFrame({'date':pd.to_datetime(UKcurrent.date),'hospitaloccupancy':UKcurrent.hospitalCases})

    url3='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22covidOccupiedMVBeds%22:%22covidOccupiedMVBeds%22%7D&format=csv'
    UKicu=pd.read_csv(url3)
    UKicu=pd.DataFrame({'date':pd.to_datetime(UKicu.date),'icuoccupancy':UKicu.covidOccupiedMVBeds})
    UKcurrent=pd.merge(UKcurrent,UKicu,on='date',how='outer')

    return UKcurrent,UKdaily