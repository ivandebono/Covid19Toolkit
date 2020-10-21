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



def get_ecdc_data(plot=False,continent=False):


    euurl='https://opendata.ecdc.europa.eu/covid19/casedistribution/csv'

    dataframe=pd.read_csv(euurl,parse_dates=['dateRep'],dayfirst=True)
    if continent:
        dataframe=dataframe[dataframe.continentExp==continent]
    dataframe.rename(columns={"dateRep": "date","cases":"positive","countriesAndTerritories":"state"},inplace=True)
    dataframe=dataframe[['date','state','positive','deaths']]
    country_names={'Czechia':'Czech Republic','United_Kingdom':'United Kingdom',
                   'Bosnia_and_Herzegovina':'Bosnia and Herzegovina'}
    dataframe.state=dataframe.state.replace(country_names,regex=True)

    dataframe['datasource']='ecdc.europa.eu'

    #dataframe.sort_values(by=['date'],inplace=True)
    #dataframe['date']=pd.to_datetime(dataframe['date'],yearfirst=True)
    return dataframe

def get_data_Hesse(plot=False):
    GEurl='https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/deaths-rki-by-state.csv'

    GE=pd.read_csv(GEurl)

    GE['date']=pd.to_datetime((pd.to_datetime(GE['time_iso8601'])).dt.date)


    HEdeaths=pd.DataFrame({'date':GE.date,'deaths':cumulative2daily(GE['DE-HE'])})


    GEurl='https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/cases-rki-by-state.csv'

    GE=pd.read_csv(GEurl)

    GE['date']=pd.to_datetime((pd.to_datetime(GE['time_iso8601'])).dt.date)


    HEcases=pd.DataFrame({'date':GE.date,'positive':cumulative2daily(GE['DE-HE'])})
    
    HE=pd.merge(HEcases,HEdeaths,how='outer',on='date')
    
    HE['total']=None
    HE['datasource']='github.com/jgehrcke/covid-19-germany-gae'
    HE['state']='Hesse'


    if plot==True:
        testplot(HE)
    return HE



def get_data_Sweden(plot=False):
    
    url='https://free.entryscape.com/store/360/resource/15'
    df=pd.read_csv(url)
    SWE=pd.DataFrame({'date':pd.to_datetime(df.Statistikdatum,errors='coerce'),'positive':df.Totalt_antal_fall,
                 'deaths':df.Antal_avlidna})
    SWE['total']=None
    SWE['state']="Sweden"
    SWE['datasource']='www.dataportal.se'
    
    if plot==True:
        testplot(SWE)
    
    
    return SWE

def get_data_Estonia(plot=False):
    url='https://raw.githubusercontent.com/okestonia/koroonakaart/master/koroonakaart/src/data.json'
    d = json.loads(requests.get(url).text)

    positive=pd.Series(d['dataNewCasesPerDayChart']['confirmedCases'])
    date=pd.Series(pd.to_datetime(d['dates2']))
    deaths=pd.Series(d['dataNewCasesPerDayChart']['deceased'])
    total=pd.Series(d["dataCumulativeTestsChart"]["testsAdminstered"])


    EE=pd.DataFrame({'date':date,'positive':positive,'deaths':deaths,'total':total.diff().fillna(total)})
    EE['state']='Estonia'
    EE['datasource']='github.com/okestonia/koroonakaart'



    if plot==True:
        testplot(EE)
    
    return EE

def get_data_Luxemburg(plot=False):
    url='https://data.public.lu/en/datasets/r/1da1bb72-4450-4f60-915b-6c355db2e7fa'


    LU=pd.read_csv(url,sep=',',encoding='Latin-1')

    #dates=pd.to_datetime(LU["if(dateRep>'23/02/2020', if(dateRep<=today()-1, dateRep))"])
    dates=pd.to_datetime(LU["Date"],dayfirst=True)
    #date=pd.date_range(start=dates.iloc[0], end=dates.iloc[-1])
   # total=(pd.to_numeric(LU['Nb de tests effectués sur résidents'],errors='coerce'))
    try:
        total=(pd.to_numeric(LU['Nb de tests effectués'],errors='coerce'))
    except KeyError:
        total=(pd.to_numeric(LU['Nb de tests effectués sur résidents'],errors='coerce'))
    # total.fillna(0,inplace=True)
    # positive=(LU['Nouvelles infections (résidents)']).diff().fillna(LU['Nouvelles infections (résidents)'])
    try: positive=(pd.to_numeric(LU['Nb de positifs'],errors='coerce'))
    except KeyError:
        positive=(pd.to_numeric(LU['Nb de résidents positifs'],errors='coerce'))
    
    
    # tested=LU['Personnes testées (résidents)']
    deaths=(LU['[1.NbMorts]']).diff().fillna(LU['[1.NbMorts]'])
    LU=pd.DataFrame({'date':dates,'positive':positive,'deaths':deaths,'total':total})#,'tested':tested})
    LU['state']='Luxemburg'
    LU['datasource']='data.public.lu/en/datasets/donnees-covid19'
    if plot==True:
        testplot(LU)

    return LU


def get_data_Greece(plot=False):
    
    url='https://raw.githubusercontent.com/iMEdD-Lab/AUTO_COVID_DATA/master/auto_greeceTimeline.csv'

    GR=pd.read_csv(url).transpose().reset_index()
    GR.columns=GR.loc[0]
    GR['date']=pd.to_datetime(GR.Status,errors='coerce')
    GR=GR[GR.date.notnull()]
    GR=pd.DataFrame({'date':GR.date,'positive':GR.cases,'deaths':GR.deaths,'total':GR.total_tests.diff().fillna(GR.total_tests)})
    GR['state']='Greece'
    GR['datasource']='github.com/iMEdD-Lab'

    if plot==True:
        testplot(GR)
    
    return GR

def get_data_Ireland(plot=False):
    
    url='https://opendata.arcgis.com/datasets/f6d6332820ca466999dbd852f6ad4d5a_0.csv'
    IEtest=pd.read_csv(url)

    timestamp=pd.to_datetime(IEtest.Date_HPSC)
    IEtest=pd.DataFrame({'date':timestamp.dt.date, \
                         'total':IEtest.TotalLabs.diff().fillna(IEtest.TotalLabs)})



    url='https://opendata.arcgis.com/datasets/d8eb52d56273413b84b0187a4e9117be_0.csv'
    IE=pd.read_csv(url)

    timestamp=pd.to_datetime(IE.Date)
    IE=pd.DataFrame({'date':timestamp.dt.date, \
                     'positive':IE.ConfirmedCovidCases,'deaths':IE.ConfirmedCovidDeaths})

    IE=pd.merge(IE,IEtest,how='outer',on='date')
    
    IE['state']='Ireland'
    IE['datasource']='covid19ireland-geohive.hub.arcgis.com'
    IE['date']=pd.to_datetime(IE.date)
    
    if plot==True:
        testplot(IE)
        
    return IE


def get_data_Switzerland(plot=False):

    CHurl='https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland_openzh.csv'

    cases=pd.read_csv(CHurl)

    #CH=CH.groupby(by='date').sum()
    cases=pd.DataFrame({'date':pd.to_datetime(cases.Date),'positive':cases.CH.diff().fillna(cases.CH)})


    CHurl='https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_fatalities_switzerland_openzh.csv'
    deaths=pd.read_csv(CHurl)
    deaths=pd.DataFrame({'date':pd.to_datetime(deaths.Date),'deaths':deaths.CH.diff().fillna(deaths.CH)})

    CH=pd.merge(cases, deaths,on='date', how='outer')


    CHurl='https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_tested_switzerland_openzh.csv'

    tests=pd.read_csv(CHurl)
    tests=pd.DataFrame({'date':pd.to_datetime(tests.Date),'total':tests.CH.diff().fillna(tests.CH)})

    CH=pd.merge(CH, tests,on='date', how='outer')

    CH['state']='Switzerland'
    CH['datasource']='github.com/daenuprobst/covid19-cases-switzerland'

    if plot==True:
        testplot(CH)

    return CH


def get_data_Denmark(plot=False):

    url='https://files.ssi.dk/Data-Epidemiologiske-Rapport-21082020-pp98'
    url = urllib.request.urlopen(url)

    with ZipFile(BytesIO(url.read())) as my_zip_file:
        for contained_file in my_zip_file.namelist():
            if contained_file=='Test_pos_over_time.csv':
                DK=pd.read_csv(my_zip_file.open(contained_file),sep=';',thousands = '.')

                DK['date']=pd.to_datetime(DK.Date,errors='coerce')
                DK.dropna(inplace=True)

                DK=pd.DataFrame({'date':DK.date,'positive':pd.to_numeric(DK.NewPositive),
                                 'total':pd.to_numeric(DK.Tested)})

            if contained_file=='Deaths_over_time.csv':
                deaths=pd.read_csv(my_zip_file.open(contained_file),sep=';',thousands = '.')
                deaths['date']=pd.to_datetime(deaths.Dato,errors='coerce')
                deaths.dropna(inplace=True)
                deaths=pd.DataFrame({'date':deaths.date,'deaths':deaths['Antal_døde']})


    DK=DK.merge(deaths,on='date',how='outer')
    DK.deaths.fillna(0,inplace=True)

    DK['state']='Denmark'
    DK['datasource']='www.ssi.dk'
    
    if plot==True:
        testplot(DK)
        
    return DK

def get_data_Portugal(plot=False):

    PTurl='https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data.csv'
    PTdf=pd.read_csv(PTurl)
    PTdf['positive']=PTdf.confirmados_novos#.diff()#.fillna(0)
    PTdf['deaths']=PTdf.obitos.diff().fillna(0)
    PTdf['date']=pd.to_datetime(PTdf.data,dayfirst=True)
    PTdf.sort_values(by=['date'], inplace=True, ascending=False)
    idx = pd.date_range(start='2019-12-31',end=PTdf.date.max() )
    PTdf=PTdf.set_index('date').reindex(idx,fill_value=0).rename_axis('date').reset_index()
    PTdf['state']='Portugal'
    PTdf = PTdf[['state','date','positive','deaths']]

    PTdf['datasource']='github.com/dssg-pt/covid19pt-data'

    PTdf['total']=None

    if plot==True:
        testplot(PTdf)
    
    return PTdf

def get_data_Belgium(plot=False):

    BEtesturl='https://epistat.sciensano.be/Data/COVID19BE_tests.csv'
    BEtests=pd.read_csv(BEtesturl)
    BEtests=BEtests.groupby(by='DATE',as_index=False).sum()
    BEtests=pd.DataFrame({'date':pd.to_datetime(BEtests.DATE) ,'total': BEtests.TESTS_ALL})

    BEdeathsurl='https://epistat.sciensano.be/Data/COVID19BE_MORT.csv'
    BEdeaths=pd.read_csv(BEdeathsurl)
    BEdeaths=BEdeaths.groupby(by='DATE',as_index=False).sum()
    BEdeaths=(pd.DataFrame({'date':pd.to_datetime(BEdeaths.DATE),'deaths':BEdeaths.DEATHS})).dropna()


    BEcasesurl='https://epistat.sciensano.be/Data/COVID19BE.xlsx'
    BEcases=pd.read_excel(BEcasesurl)
    BEcases=BEcases.groupby(by='DATE',as_index=False).sum()
    BEcases=(pd.DataFrame({'date':pd.to_datetime(BEcases.DATE), 'positive':BEcases.CASES})).dropna()
    
    BE=pd.merge(BEcases,BEdeaths,on='date',how='outer').fillna(0)

    BE=pd.merge(BE,BEtests,on='date',how='outer').fillna(0)
    
    BE['state']='Belgium'
    BE['datasource']='epistat.sciensano.be'
    BE.deaths.fillna(0,inplace=True)
    BE.positive.fillna(0,inplace=True)

    if plot==True:
        testplot(BE)
    
    return BE


def get_data_Germany(plot=False):
    GEcasesurl='https://opendata.arcgis.com/datasets/dd4580c810204019a7b8eb3e0b329dd6_0.csv'
    GEcases=pd.read_csv(GEcasesurl)
    GEcases['date']=pd.to_datetime(GEcases.Refdatum)
    GEcases=GEcases.groupby(by='date',as_index=False).sum()
    GEcases['positive']=GEcases.AnzahlFall
    GEcases['deaths']=GEcases.AnzahlTodesfall
    GEcases=GEcases[['date','positive','deaths']]

    GE['state']='Germany'

    return GE

def get_data_France():
    # Tests since 13 May 2020

    url='https://www.data.gouv.fr/fr/datasets/r/dd0de5d9-b5a5-4503-930a-7b08dc0adc7c'
    frtestsdf=pd.read_csv(url,delimiter=';')
    frtestsdf['date']=pd.to_datetime(frtestsdf.jour)
    frtests=frtestsdf.loc[frtestsdf.cl_age90==0]
    frtests=frtests.groupby(by='date',as_index=False).sum()
    frtests=pd.DataFrame({'date':frtests.date,'total':frtests['T']})

    # Tests up to 13 May 2020
    url='https://www.data.gouv.fr/fr/datasets/r/b4ea7b4b-b7d1-4885-a099-71852291ff20'
    frtestsdf2=pd.read_csv(url,delimiter=';')
    frtestsdf2=frtestsdf2.groupby(by='jour',as_index=False).sum()
    frtests2=pd.DataFrame({'date':pd.to_datetime(frtestsdf2.jour),'total':frtestsdf2.nb_test})

    fr=pd.concat([frtests2[frtests2.date<frtests.date.min()],frtests])
    
    df=get_ecdc_data()
    FRdf=(df[df.state=='France']).reset_index(drop=True)
    FRdf['positive'].clip(lower=0,inplace=True)
    
    
    fr=pd.merge(fr,FRdf,on='date',how='outer')
    fr=fr.sort_values(by='date').reset_index(drop=True)

    #fr=pd.concat([frtests2,frtests])
    #fr=fr.groupby(by='date',as_index=False).sum()
    
    return fr


def get_data_France_OLD(plot=False):
    
    df=get_ecdc_data()
    FRdf=(df[df.state=='France']).reset_index()
    FRdf['positive'].clip(lower=0,inplace=True)

    FRurl='https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675'
    #FRurl='https://www.data.gouv.fr/en/datasets/r/b4ea7b4b-b7d1-4885-a099-71852291ff20'

    FRtest1=pd.read_csv(FRurl,delimiter=';')
    FRtest1['date']=pd.to_datetime(FRtest1.jour)
    FRtest1.rename(columns={'T':'total'},inplace=True)
    FRtestnew=(FRtest1[['date','total']]).groupby('date',as_index=False).sum()
    FRtestnew.sort_values(by='date',ascending=False,inplace=True)

    FRurl='https://www.data.gouv.fr/en/datasets/r/b4ea7b4b-b7d1-4885-a099-71852291ff20'
    FRtest1=pd.read_csv(FRurl,delimiter=';')

    FRtest1.rename(columns={'nb_test':'total','jour':'date'},inplace=True)
    FRtest=(FRtest1[['date','total']]).groupby('date',as_index=False).sum()
    FRtest['date']=pd.to_datetime(FRtest.date)
    FRtest.sort_values(by='date',ascending=False,inplace=True)

    FRtests=pd.concat([FRtestnew,FRtest[FRtest.date<FRtestnew.date.min()]],ignore_index=True)
    FRtests.sort_values(by='date',ascending=False,inplace=True,ignore_index=True)

    FR = FRdf.merge(FRtests,how='left', left_on='date', right_on='date').drop(columns={'index'})
    FR.sort_values(by='date',ascending=False,inplace=True,ignore_index=True)

    FR['state']='France'
    FR['datasource']='www.data.gouv.fr'

    if plot==True:
        testplot(FR)


    return FR

def get_data_Italy(plot=False):
    ITurl='https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
    ITdf=pd.read_csv(ITurl)
    ITdf['total']=ITdf.tamponi.diff().fillna(ITdf.tamponi)
    ITdf['deaths']=ITdf.deceduti.diff().fillna(ITdf.deceduti)
    ITdf=ITdf[['data','nuovi_positivi','total','deaths']]
    ITdf['state']='Italy'
    ITdf.rename(columns={'data':'date','nuovi_positivi':'positive'},inplace=True)
    ITdf['date']=pd.to_datetime(ITdf.date).dt.normalize()
    ITdf['datasource']='www.github.com/pcm-dpc/COVID-19'

    if plot==True:
        testplot(ITdf)

    return ITdf
    
def get_data_UK(plot=False):

    url='https://api.coronavirus.data.gov.uk/v1/data?filters=areaName=United%2520Kingdom;areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22plannedCapacityByPublishDate%22:%22plannedCapacityByPublishDate%22,%22capacityPillarOne%22:%22capacityPillarOne%22,%22capacityPillarTwo%22:%22capacityPillarTwo%22,%22capacityPillarThree%22:%22capacityPillarThree%22,%22capacityPillarFour%22:%22capacityPillarFour%22,%22capacityPillarOneTwo%22:%22capacityPillarOneTwo%22,%22newTestsByPublishDate%22:%22newTestsByPublishDate%22,%22newPillarOneTestsByPublishDate%22:%22newPillarOneTestsByPublishDate%22,%22newPillarTwoTestsByPublishDate%22:%22newPillarTwoTestsByPublishDate%22,%22newPillarThreeTestsByPublishDate%22:%22newPillarThreeTestsByPublishDate%22,%22newPillarFourTestsByPublishDate%22:%22newPillarFourTestsByPublishDate%22,%22newPillarOneTwoTestsByPublishDate%22:%22newPillarOneTwoTestsByPublishDate%22,%22cumTestsByPublishDate%22:%22cumTestsByPublishDate%22,%22cumPillarOneTwoTestsByPublishDate%22:%22cumPillarOneTwoTestsByPublishDate%22%7D&format=csv'


    tests=pd.read_csv(url)
    tests=pd.DataFrame({'date':pd.to_datetime(tests.date),'total':tests.newPillarOneTwoTestsByPublishDate})
    tests=tests.sort_values(by='date',ascending=True).reset_index(drop=True)
    tests.interpolate(how='ffill',inplace=True)
    
    
    url='https://api.coronavirus.data.gov.uk/v1/data?filters=areaName=United%2520Kingdom;areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22newCasesByPublishDate%22:%22newCasesByPublishDate%22,%22cumCasesByPublishDate%22:%22cumCasesByPublishDate%22%7D&format=csv'
    UKcases=pd.read_csv(url)
    cases=pd.DataFrame({'date':pd.to_datetime(UKcases.date),'positive':UKcases.newCasesByPublishDate})


    
#     url='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22newCasesBySpecimenDate%22:%22newCasesBySpecimenDate%22,%22cumCasesBySpecimenDate%22:%22cumCasesBySpecimenDate%22%7D&format=csv'

#     cases=pd.read_csv(url)
#     cases=pd.DataFrame({'date':pd.to_datetime(cases.date),'positive':cases.newCasesBySpecimenDate})
#     cases=cases.sort_values(by='date',ascending=True).reset_index(drop=True)
#     cases.positive.fillna(0,inplace=True)

    UK=pd.merge(cases,tests,on='date',how='outer')
    
#     url='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22newDeaths28DaysByDeathDate%22:%22newDeaths28DaysByDeathDate%22,%22cumDeaths28DaysByDeathDate%22:%22cumDeaths28DaysByDeathDate%22%7D&format=csv'
#     deaths=pd.read_csv(url)
#     deaths=pd.DataFrame({'date':pd.to_datetime(deaths.date),'deaths':deaths.newDeaths28DaysByDeathDate})
#     deaths=deaths.sort_values(by='date',ascending=True).reset_index(drop=True)

    url='https://api.coronavirus.data.gov.uk/v1/data?filters=areaType=overview&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22newDeaths28DaysByPublishDate%22:%22newDeaths28DaysByPublishDate%22,%22cumDeaths28DaysByPublishDate%22:%22cumDeaths28DaysByPublishDate%22%7D&format=csv'
    
    UKdeaths=pd.read_csv(url)
    deaths=pd.DataFrame({'date':pd.to_datetime(UKdeaths.date),'deaths':UKdeaths.newDeaths28DaysByPublishDate})
    deaths.deaths.fillna(0,inplace=True)

    UK=pd.merge(UK,deaths,on='date',how='outer')
    
    UK['state']='United Kingdom'
    UK['datasource']='coronavirus.data.gov.uk'
    
    if plot==True:
        testplot(UK)
        
    return UK

def get_data_UK_OLD(plot=False):
    #### !!!! Scrape correct url (name changes with date) from website
    mainurl='https://www.gov.uk/guidance/coronavirus-covid-19-information-for-the-public'


    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    resp = urllib.request.urlopen(mainurl)
    soup = BeautifulSoup(resp, parser, from_encoding=resp.info().get_param('charset'))

    urls=[]
    for link in soup.find_all('a', href=True):
        if '.csv' in link['href']:
            #print(link['href'])
            urls.append(link['href'])

    for s in urls:
        if 'testing' in s:
            UKtesturl=s
            print('Tests:',s)
        if 'deaths' in s:
            UKdeathsurl=s
            print('Deaths:',s)
        if 'cases' in s:
            UKcaseurl=s
            print('Cases:',s)
        
    #UKtesturl='https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/908596/2020-08-11_COVID-19_UK_testing_time_series.csv'
    UKtest=pd.read_csv(UKtesturl)
    UKtest=UKtest.loc[UKtest.Nation=='UK']
    UKtest['date']=pd.to_datetime(UKtest['Date of activity'],format='%d/%m/%Y')
    UKtest['Daily number of tests processed']=pd.to_numeric(UKtest['Daily number of tests processed'])
    #UKtest['total_inperson']=UKtest['Daily In-person (tests processed)']
    UKtest['total']=UKtest['Daily number of tests processed']
    UKtest=UKtest.groupby(by='date',as_index=False).sum() 


    UKtest=UKtest[['date','total']]

    #UKtest=UKtest.loc[UKtest.date<pd.datetime(2020,8,11)]

    #UKcaseurl='https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/905965/2020-07-31_COVID-19_UK_positive_cases_time_series_by_specimen_date.csv'
    UKcases=pd.read_csv(UKcaseurl)
    UKcases=UKcases.loc[UKcases.Nation=='UK']
    UKcases.rename(columns={'Daily number of positive cases (new methodology)':'positive'},inplace=True)
    UKcases['date']=pd.to_datetime(UKcases['Earliest Specimen Date'],format='%d/%m/%Y')
    UKcases=UKcases[['date','positive']]
    UKcases=UKcases.groupby('date',as_index=False).sum()

    #UKdeathsurl='https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/906106/2020-08-01_COVID-19_UK_deaths_time_series.csv'
    UKdeaths=pd.read_csv(UKdeathsurl)
    # UKdeaths.rename(columns={'UK Daily count of deaths in all settings':'deaths'},inplace=True)
    UKdeaths.rename(columns={'UK Daily count of deaths by reported date (28 day cut off)':'deaths'},inplace=True) 
    UKdeaths['date']=pd.to_datetime(UKdeaths['Publicly confirmed as deceased as of 5pm this day'],format='%d-%b-%y')
    UKdeaths=UKdeaths[['date','deaths']]

    UK=UKcases.merge(UKdeaths,on='date',how='left')

    UK.fillna(0,inplace=True)

    UK=UKtest.merge(UK,on='date',how='left')



    UK['state']='United Kingdom'
    UK['datasource']='www.gov.uk/guidance/coronavirus-covid-19-information-for-the-public'

    if plot:
        UK.plot(x='date',y=['deaths','total','positive'])

    return UK


def get_data_Spain(plot=False):
    url='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/nacional_covid19.csv'

    ESdf=pd.read_csv(url)
    ESdf.fillna(0,inplace=True)
    ESdf['date']=pd.to_datetime(ESdf.fecha)
    ESdf['positivecumulative']=ESdf.casos_pcr+ESdf.casos_test_ac
    ESdf=ESdf[['date','positivecumulative','fallecimientos']]
    ESdf.drop_duplicates(inplace=True)
    ESdf.set_index('date', inplace=True)
    ESdf=ESdf.resample('D').interpolate().reset_index()


    ESdf['positive']=ESdf.positivecumulative.diff().fillna(ESdf.positivecumulative)
    ESdf.positive.clip(0,inplace=True)
    ESdf['deaths']=ESdf.fallecimientos.diff().fillna(ESdf.fallecimientos)
    ESdf.deaths.clip(0,inplace=True)

    ESdf=ESdf[['date','positive','deaths']]



    url='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_test_realizados.csv'
    tests=pd.read_csv(url)
    tests=tests.loc[tests.CCAA=='España']
    weeklytests=pd.DataFrame({'date':pd.to_datetime(tests.Fecha),'total':tests.TOTAL_PRUEBAS.diff()})
    weeklytests.dropna(inplace=True)

    first3weeksdates=[(weeklytests.date.min()-timedelta(days=21)),(weeklytests.date.min()-timedelta(days=14)),(weeklytests.date.min()-timedelta(days=7))]

    first3weeksdf=pd.DataFrame({'date':first3weeksdates} )
    first3weeksdf['total']=tests.TOTAL_PRUEBAS.iloc[0]/3
    weeklytests=pd.concat([first3weeksdf,weeklytests])
    weeklytests.reset_index(inplace=True,drop=True)

    start_of_tests=weeklytests.date.min()
    days=pd.DataFrame({'date':(pd.date_range(start=start_of_tests-dt.timedelta(6),end=weeklytests.date.max()))})
    dailytests=pd.merge_ordered(weeklytests, days, fill_method="None")
    EStests=dailytests.interpolate()
    #EStests.sort_values(by='date',inplace=True, ascending=False)
    #EStests.reset_index(inplace=True,drop=True)


    ES=pd.merge(EStests,ESdf,on='date',how='outer')

    ES['state']='Spain'
    ES['datasource']='github.com/datadista'
                
    if plot==True:
        testplot(ES)

    #pcrurl='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_pcr_realizadas_diarias.csv'
    #pcr=pd.read_csv(pcrurl)
    
    return ES#,pcr

def get_data_Spain_OLD2(plot=False):
    url='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/nacional_covid19.csv'

    ES=pd.read_csv(url)
    ES.fillna(0,inplace=True)
    positive=ES.casos_pcr+ES.casos_test_ac
    ES['positive']=positive.diff().fillna(positive)
    ES.positive.clip(0,inplace=True)
    ES['deaths']=ES.fallecimientos.diff().fillna(ES.fallecimientos)
    ES.deaths.clip(0,inplace=True)
    ES['date']=pd.to_datetime(ES.fecha)
    ES.plot(x='date',y=['deaths','positive'])
    ES['total']=None
    ES['state']='Spain'
    ES['datasource']='github.com/datadista'
    
    return ES

def get_data_Spain_OLD(plot=False):

    ESurl='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_datos_isciii_nueva_serie.csv'
    ESdf=pd.read_csv(ESurl)
    ESdf['date']=pd.to_datetime(ESdf.fecha)
    ESdf=ESdf.groupby(by='date',as_index=False).sum()
    ESdf.rename(columns={'num_casos':'positive'},inplace=True)
    ESdf=ESdf[['date','positive']]


    ESdeathurl='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_fallecidos_por_fecha_defuncion_nueva_serie.csv'
    ESdfdeath=pd.read_csv(ESdeathurl)
    ESdfdeath.drop(columns=['cod_ine','CCAA'],inplace=True)
    deaths=pd.Series(ESdfdeath.sum(numeric_only=True).reset_index(drop=True))
    ESdfdeath=(ESdfdeath.transpose())
    date=pd.to_datetime(ESdfdeath.index)
    ESdeaths=pd.DataFrame({'date':date,'deaths':deaths})

    ES=ESdf.merge(ESdeaths,on='date',how='left')




    EStesturl='https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_test_realizados.csv'
    ESdftest=pd.read_csv(EStesturl)
    ESdftest=(ESdftest.loc[ESdftest.CCAA=='España']).reset_index(drop=True)




    TestedAll=cumulative2daily(ESdftest.TOTAL_PRUEBAS)
    EStest=pd.DataFrame({'date':pd.to_datetime(ESdftest.Fecha),'TestedAll':TestedAll})


    EStest=tests_week2day(EStest)


    ES=ES.merge(EStest,on='date',how='left')
    ES.total.interpolate(method = "spline", order = 2, limit_direction = "forward",inplace=True)
    ES.total.fillna(0,inplace=True)

    ES.deaths.fillna(0,inplace=True)
    ES.positive.fillna(0,inplace=True)

    ES['state']='Spain'
    ES['datasource']='github.com/datadista/datasets'

    if plot:
        ES.plot(x='date',y=['deaths','total','positive'])

    return ES


def get_data_Austria(plot=False):

#ATdata=pd.read_csv(ATurl,compression='zip')

    ATurl='https://info.gesundheitsministerium.at/data/data.zip'
    url = urllib.request.urlopen(ATurl)

    with ZipFile(BytesIO(url.read())) as my_zip_file:
        for contained_file in my_zip_file.namelist():
            if contained_file=='Epikurve.csv':

                # with open(("unzipped_and_read_" + contained_file + ".file"), "wb") as output:
                ATcases=pd.read_csv(my_zip_file.open(contained_file),sep=';')
                ATcases.drop(columns='Timestamp',inplace=True)
                ATcases['date']=pd.to_datetime(ATcases.time,dayfirst=True)
                ATcases.drop(columns='time',inplace=True)
                ATcases.rename(columns={'tägliche Erkrankungen':'positive'},inplace=True)
                ATcases=ATcases[['date', 'positive']]


            if contained_file=='TodesfaelleTimeline.csv':

                # with open(("unzipped_and_read_" + contained_file + ".file"), "wb") as output:
                ATdeaths=pd.read_csv(my_zip_file.open(contained_file),sep=';')
                ATdeaths.drop(columns='Timestamp',inplace=True)
                ATdeaths['date']=pd.to_datetime(ATdeaths.time,dayfirst=True)
                ATdeaths.drop(columns='time',inplace=True)
                ATdeaths.rename(columns={'Todesfälle':'deaths'},inplace=True)
                ATdeaths['deaths']=ATdeaths.deaths.diff().shift(periods=-1).fillna(ATdeaths.deaths)
                ATdeaths=ATdeaths[['date', 'deaths']]

    ATcorrect=ATcases.merge(ATdeaths, on='date') 

    ATcorrect.sort_values(by=['date'], inplace=True, ascending=False)

    idx = pd.date_range(start='12-31-2019',end=ATcorrect.date.max().date() )
    ATcorrect=ATcorrect.set_index('date').reindex(idx,fill_value=0).rename_axis('date').reset_index()
    ATcorrect['state']='Austria'
    ATcorrect=ATcorrect[['state','date','positive','deaths']]

    ATcorrect['total']=None
    
    ATcorrect['state']='Austria'
    ATcorrect['datasource']='info.gesundheitsministerium.at'
    if plot:
        ATcorrect.plot(x='date',y=['deaths','total','positive'])   

    return ATcorrect

def get_data_Malta(plot=False):

    MTurl='https://raw.githubusercontent.com/Lobeslab-Ltd/covid-19-MT/master/malta_time_series.csv'
    
    MTdf=pd.read_csv(MTurl)
    MTdf['positive']=MTdf.Confirmed.diff(1).fillna(0)
    MTdf['deaths']=MTdf.Deaths.diff(1).fillna(0)
    MTdf['date']=pd.to_datetime(MTdf.Date,dayfirst=True)
    MTdf_full=MTdf[['date','positive','deaths','Active']]

    MTdf=MTdf_full[['date','positive','deaths']]
    MTdf['state']='Malta'
    MTdf['total']=None
    MTdf['datasource']='github.com/Lobeslab-Ltd/covid-19-MT'

    if plot:
        MTdf.plot(x='date',y=['deaths','total','positive'])   

    
    return MTdf


def get_data_Berlin(plot=False):
    GEurl='https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/deaths-rki-by-state.csv'

    GE=pd.read_csv(GEurl)

    GE['date']=pd.to_datetime((pd.to_datetime(GE['time_iso8601'])).dt.date)


    Berlin=pd.DataFrame({'date':GE.date,'deaths':cumulative2daily(GE['DE-BE'])})
    
    Berlin['positive']=None
    Berlin['total']=None
    Berlin['datasource']='github.com/jgehrcke/covid-19-germany-gae'
    Berlin['state']='Berlin'

    if plot==True:
        testplot(Berlin)
    return Berlin

def get_data_Norway(plot=False):
    
    NOtestsurl='https://raw.githubusercontent.com/thohan88/covid19-nor-data/master/data/03_covid_tests/national_tests.csv'
    NOtests=pd.read_csv(NOtestsurl)

    NOtests=pd.DataFrame({'date':pd.to_datetime(NOtests.date),'total':NOtests.n_tests})

    NOtestsurllab='https://raw.githubusercontent.com/thohan88/covid19-nor-data/master/data/03_covid_tests/national_tests_lab.csv'
    NOlab=pd.read_csv(NOtestsurllab)
    NOlab=pd.DataFrame({'date':pd.to_datetime(NOlab.date),'total':NOlab.n_tests})
    NOtests = NOlab.append(NOtests)
    NOtests=NOtests.groupby(by='date',as_index=False).sum()

    NOdeathurl='https://raw.githubusercontent.com/thohan88/covid19-nor-data/master/data/04_deaths/deaths_total_fhi.csv'
    NOdeaths=pd.read_csv(NOdeathurl)
    NOdeaths['date']=pd.to_datetime(NOdeaths.date)
    NOdeaths.sort_values(by=['date'], inplace=True, ascending=True)
    NOdeaths['deaths']=NOdeaths.deaths.diff().fillna(NOdeaths.deaths)
    NOdeaths=pd.DataFrame({'date':NOdeaths.date,'deaths':NOdeaths.deaths})

    NOcasesurl='https://raw.githubusercontent.com/thohan88/covid19-nor-data/master/data/01_infected/msis/municipality.csv'
    NOcases=pd.read_csv(NOcasesurl)
    NOcases=NOcases.groupby(by='date',as_index=False).sum()
    NOcases.sort_values(by=['date'], inplace=True, ascending=True)
    positive=NOcases.cases.diff().fillna(NOcases.cases)
    NOcases=pd.DataFrame({'date':pd.to_datetime(NOcases.date),'positive':positive})

    ### MERGE AND KEEP *A L L* rows
    NO=pd.merge(NOtests, NOcases, on = ['date'], how = 'outer')
    NO=pd.merge(NO,NOdeaths,on=['date'],how='outer')

    NO.fillna(0,inplace=True)
    NO['state']='Norway'
    NO['datasource']='github.com/thohan88/covid19-nor-data'

    if plot==True:
        testplot(NO)

    return NO


def get_data_Netherlands(plot=False):

    NLurl='https://raw.githubusercontent.com/J535D165/CoronaWatchNL/master/data/rivm_NL_covid19_national.csv'
    NL=pd.read_csv(NLurl)
    NL=(pd.pivot_table(NL, values='Aantal',index='Datum',  columns=['Type'])).rename_axis(None, axis=1).reset_index()
    NL=pd.DataFrame({'date':pd.to_datetime(NL.Datum),'cases':NL.Totaal,'deathsc':NL.Overleden})
    NL['positive']=NL.cases.diff().fillna(NL.cases)
    NL['deaths']=NL.deathsc.diff().fillna(NL.deathsc)
    NL=pd.DataFrame({'date':NL.date,'positive':NL.positive,'deaths':NL.deaths,'total':None})
    NL['state']='Netherlands'
    NL['datasource']='github.com/J535D165/CoronaWatchNL'

    if plot==True:
        testplot(NL)
    
    return NL

