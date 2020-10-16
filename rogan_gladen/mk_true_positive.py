import pymc3 as pm
import pandas as pd
import arviz as az
import numpy as np


def mk_true_positive(df,se=[0.9,1],sp=[0.9,1]):



    data=df.copy()
    data.dropna(inplace=True)
    data['positive']=data.positive.rolling(window=7).mean()
    data['total']=data.total.rolling(window=7).mean()
    data.drop(data[data.total<data.positive].index)
    data.dropna(inplace=True)
    data=data.reset_index(drop=True)


    coords = {
    "date": data.index,
    "variables": ['total','positive']
            }

    with pm.Model(coords=coords) as model: 


        pi=pm.Uniform('pi',lower=0, upper=1,dims='date')
        se=pm.Uniform('se',lower=se[0], upper=se[1],dims='date')
        sp=pm.Uniform('sp',lower=sp[0], upper=sp[1],dims='date')
        #se=pm.Normal('se',mu=0.95 sigma=None, tau=None, sd=None,dims='date')


        p=pi*se+(1-pi)*(1-sp)



        observed_positive = pm.Binomial('observed_positive', n=data.total.values, p=p,
                                    observed=data.positive.values,dims='date')
        obs_positive_trace = pm.sample(target_accept=0.95)



        return obs_positive_trace,data

