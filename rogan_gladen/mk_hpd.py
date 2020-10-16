import pandas as pd
import arviz as az
import numpy as np




 
def mk_hpd(obs_positive_trace,data):

    obs_positive_trace_hpd = az.hdi(obs_positive_trace["pi"],hdi_prob=0.68)
    hpd_low=obs_positive_trace_hpd[:,0]
    hpd_high=obs_positive_trace_hpd[:,1]

    data['true_incidence']=[obs_positive_trace['pi'][:,i].mean() for i in data.index]
    data['true_positive']=data.total*data.true_incidence

    data['true_positive_low']=data.total.values*hpd_low
    data['true_positive_high']=data.total.values*hpd_high

    return data


