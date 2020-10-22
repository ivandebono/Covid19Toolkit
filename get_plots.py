from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MonthLocator, WeekdayLocator, DateFormatter
import seaborn as sns

import mpld3

def mirrorplot(df,country=None,datasource=None,mirror=True,mynotes=True):
    
    if mynotes:
        country=country
        datasource=datasource
    else:
        if country is not None:
            try: country=df.state.unique()[0]
            except: country=country
        
        if datasource is not None:
            try: datasource=df.datasource.unique()[0]
            except: datasource=datasource


    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')



    fig, ax = plt.subplots(figsize=(15, 8))
    plt.title(country+': Official Covid daily cases and deaths \n'+datasource)    
    
    ax.bar(df.date, df.positive,label='Reported cases',color='RoyalBlue',alpha=1)
    
    
    if mirror:
        ax.bar(df.date, -1*df.deaths,label='Reported deaths',color='crimson',alpha=1)
    else: ax.bar(df.date, df.deaths,label='Reported deaths',color='crimson',alpha=1)

    ax.plot(df.date,df.positive_avg,label='Cases: rolling average',color='blue')

  # Formatting x labels
    plt.xticks(rotation=90)

# Use absolute value for y-ticks
#ticks =  ax.get_yticks()
    #ax.set_yticklabels([int(abs(tick)) for tick in ticks])

    ax.xaxis.set_major_locator(months)
    #ax.format_xdata = mdates.DateFormatter('%b %Y')
    monthsFmt = DateFormatter("%b")
    ax.xaxis.set_major_formatter(monthsFmt)

    ax.xaxis.set_minor_locator(WeekdayLocator())

    ticks =  ax.get_yticks()
    ax.set_yticklabels([int(abs(tick)) for tick in ticks])
    #plt.ylim=[-100000,300000]
    plt.legend(loc='upper left')
    plt.grid(axis='y',alpha=0.4)
    #plt.grid(which='minor', axis='y',linestyle='--')

    plt.tight_layout()
    fig.set_facecolor('w')

    fig.autofmt_xdate()
    sns.despine;
    plt.tight_layout()
    plt.savefig('plots/'+country.replace(' ', '_').replace('/','_')+'MirrorPlot.png',dpi=250)
    
    return





def plot_fpr(df,df_fpr,country=None,datasource=None,mynotes=True):
    
    if mynotes:
        country=country
        datasource=datasource
    else:
        if country is not None:
            try: country=df.state.unique()[0]
            except: country=country
        
        if datasource is not None:
            try: datasource=df.datasource.unique()[0]
            except: datasource=datasource

    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')



    fig, ax = plt.subplots(figsize=(15, 8))
    plt.title(country+': Official Covid daily cases and deaths \n'+datasource)
          
    
#plt.title('Out of all deaths worldwide, how many are due to Covid?')
#plt.title(country+': Daily deaths \n Data: '+datasource)          
    
    ax.bar(df.date, df.positive,label='Reported positive tests',color='RoyalBlue',alpha=0.7)
    ax.plot(df.date,df.positive_avg,label='Reported positive tests: rolling average',color='blue')
    
    
    ax.bar(df.date, df.deaths,label='Reported deaths',color='crimson',alpha=1)

    #ax.plot(df.date, df.falsepositive,label='False positives',color='orange',alpha=1)
    ax.plot(df_fpr.date, df_fpr.true_positive,label='True positives (with 68% confidence interval)',color='MidnightBlue',alpha=1,linewidth=3)
    plt.fill_between(df_fpr.date.values, df_fpr.true_positive_low.values,df_fpr.true_positive_high.values,color='grey',alpha=0.7)
    

  # Formatting x labels
    plt.xticks(rotation=90)

# Use absolute value for y-ticks
#ticks =  ax.get_yticks()
    #ax.set_yticklabels([int(abs(tick)) for tick in ticks])

    ax.xaxis.set_major_locator(months)
    #ax.format_xdata = mdates.DateFormatter('%b %Y')
    monthsFmt = DateFormatter("%b")
    ax.xaxis.set_major_formatter(monthsFmt)

    ax.xaxis.set_minor_locator(WeekdayLocator())

    ticks =  ax.get_yticks()
    ax.set_yticklabels([int(abs(tick)) for tick in ticks])

    handles, labels = plt.gca().get_legend_handles_labels()
    order = [2,3,0,1]
    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc='upper left')


    plt.grid(axis='y',alpha=0.4)
    #plt.grid(which='minor', axis='y',linestyle='--')

    fig.set_facecolor('w')

    fig.autofmt_xdate()
    sns.despine;
    plt.tight_layout()
    plt.savefig('plots/'+country.replace(' ', '_').replace('/','_')+'FPR_plot.png',dpi=250)

    html_str = mpld3.fig_to_html(fig)
    Html_file= open("index.html","w")
    Html_file.write(html_str)
    Html_file.close()
    
    return





def mirrorplot_withtest(df,testdf,country=None,datasource=None,mirror=True,mynotes=True):
    
    if mynotes:
        country=country
        datasource=datasource
    else:
        if country is not None:
            try: country=df.state.unique()[0]
            except: country=country
        
        if datasource is not None:
            try: datasource=df.datasource.unique()[0]
            except: datasource=datasource

    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')



    fig, ax = plt.subplots(figsize=(15, 8))
    plt.title(country+': Official Covid daily cases & deaths, and tests \n'+datasource)
          
    
#plt.title('Out of all deaths worldwide, how many are due to Covid?')
#plt.title(country+': Daily deaths \n Data: '+datasource)          
    

    ax.plot(testdf.date,testdf.dailytestsavg,label='Tests: rolling average',color='green',alpha=1)
    ax.bar(testdf.date,testdf.total,label='Tests',color='green',alpha=0.8)

    ax.bar(df.date, df.positive,label='Reported cases',color='RoyalBlue',alpha=1)
    
    if mirror:
        ax.bar(df.date, -1*df.deaths,label='Reported deaths',color='crimson',alpha=1)
    else: ax.bar(df.date, df.deaths,label='Reported deaths',color='crimson',alpha=1)

    

  # Formatting x labels
    plt.xticks(rotation=90)

# Use absolute value for y-ticks
#ticks =  ax.get_yticks()
    #ax.set_yticklabels([int(abs(tick)) for tick in ticks])

    ax.xaxis.set_major_locator(months)
    #ax.format_xdata = mdates.DateFormatter('%b %Y')
    monthsFmt = DateFormatter("%b")
    ax.xaxis.set_major_formatter(monthsFmt)

    ax.xaxis.set_minor_locator(WeekdayLocator())

    ticks =  ax.get_yticks()
    ax.set_yticklabels([int(abs(tick)) for tick in ticks])

    handles, labels = plt.gca().get_legend_handles_labels()
    order = [1,0,2,3]
    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc='upper left')

    plt.grid(axis='y',alpha=0.4)
    #plt.grid(which='minor', axis='y',linestyle='--')

    plt.tight_layout()
    fig.set_facecolor('w')

    fig.autofmt_xdate()
    sns.despine;

    plt.savefig('plots/'+country.replace(' ', '_').replace('/','_')+'MirrorPlot_withtests.png',dpi=250)
    
    return