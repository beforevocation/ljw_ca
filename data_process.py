#coding:utf-8
#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


def general_figure(monitor_point, date):
    df = pd.read_csv('TAB_VEH_15MIN_ADDBLACK.csv', encoding='utf-8').fillna(0)
    flow = list()
    speed = list()
    date_list = list()
    for index, row in df.iterrows():
        if row['SBBH'] == monitor_point and row['JCSJ'].startswith(date):
            flow.append(row['VEH_TOTAL'])
            speed.append(row['AVG_SPEED'])
            date_list.append(row['JCSJ'])
    date_list.sort(reverse=False)
    print speed
    print flow
    print date_list
    plt.xlabel('flow(veh/15min)')
    plt.ylabel('speed(km/h)')
    plt.scatter(flow, speed, s=4)
    plt.savefig('pic/speed-flow-general-38.png')
    plt.show()


def day_flow_figure(monitor_point, date):
    df = pd.read_csv('TAB_VEH_15MIN_ADDBLACK.csv', encoding='utf-8').fillna(0)
    flow = list()
    speed = list()
    date_list = list()
    for index, row in df.iterrows():
        if row['SBBH'] == monitor_point and row['JCSJ'].startswith(date):
            flow.append(row['VEH_TOTAL'])
            speed.append(row['AVG_SPEED'])
            date_list.append(row['JCSJ'])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    d = '2016-3-4 00:00'
    x = pd.date_range(d, periods=96, freq='15min')
    ax.plot(x, flow, label='True Data')
    date_format = mpl.dates.DateFormatter("%H:%M")
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    plt.xlabel('Time of Day')
    plt.ylabel('Flow')

    plt.show()


def search_data(monitor_point, date):
    df = pd.read_csv('TAB_VEH_15MIN_ADDBLACK.csv', encoding='utf-8').fillna(0)
    flow = list()
    for index, row in df.iterrows():
        if row['SBBH'] == monitor_point and row['JCSJ'].startswith(date):
            flow.append(row['VEH_TOTAL'])
    if len(flow) == 96:
        print date


def read_chunk():
    df = pd.read_csv('TT_VEHICLE_T.csv', encoding='utf-8', chunksize=1)
    chunk = df.get_chunk(1)
    print chunk


def data_filter(HD1, HD2):
    df = pd.read_csv('TAB_VEH_15MIN_ADDBLACK.csv', encoding='utf-8').fillna(0)
    df_38 = pd.DataFrame(columns=['SBBH', 'JCSJ', 'VEH_TOTAL', 'JB_COUNT', 'JP_COUNT', 'BLACK_COUNT',
                                     'AVG_SPEED', 'MAX_SPEED', 'MIN_SPEED'])
    df_39 = pd.DataFrame(columns=['SBBH', 'JCSJ', 'VEH_TOTAL', 'JB_COUNT', 'JP_COUNT', 'BLACK_COUNT',
                                  'AVG_SPEED', 'MAX_SPEED', 'MIN_SPEED'])
    for i in df.index:
        if df.loc[i].values[0:1] == HD1:
            df_38 = df_38.append(df.loc[i], ignore_index=True)
        elif df.loc[i].values[0:1] == HD2:
            df_39 = df_39.append(df.loc[i], ignore_index=True)

    df_38.to_csv('df_38.csv')
    df_39.to_csv('df_39.csv')


def read_store_data():
    df = pd.read_csv('speed-flow-storage.csv', encoding='utf-8').fillna(0)
    for index, row in df.iterrows():
        print int(row['flow'])


if __name__ == '__main__':
    # date = '2015/12/5'
    # day_flow_figure('HD001038', date)
    # day_flow_figure('HD001039', date)
    # data_filter('HD001038', 'HD001039')
    # read_store_data()
    for i in range(1, 3):
        print i



