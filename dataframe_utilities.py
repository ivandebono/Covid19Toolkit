#dataframe_utilities

import pandas as pd
import numpy as np
from datetime import timedelta

def ECDC_week2day(df,weeklyname,dailyname):
    
    start_of_tests=df.date.min()-timedelta(days=6)
    dailies=pd.Series(np.array([np.repeat(x1/7,7) for x1 in df[weeklyname].values]).flatten(),name=dailyname).to_frame()
    date=(pd.Series(pd.date_range(start=start_of_tests,end=df.date.max()),name='date').to_frame()).reset_index(drop=True)

    df2= date.join(dailies)
    
    return df2

def insert_row(idx, df, df_insert):
    return df.iloc[:idx, ].append(df_insert).append(df.iloc[idx:, ]) #.reset_index(drop = True)