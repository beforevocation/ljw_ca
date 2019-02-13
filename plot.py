#coding:utf-8
#!/usr/bin/env python
import matplotlib.pyplot as plt
import road
import matplotlib as mpl
import car as car
import pandas as pd
import random
import csv

def f_1(x, A, B):
    return A*x + B


def f_2(x, A, B, C):
    return A*x*x + B*x + C


def f_3(x, A, B, C, D):
    return A*x*x*x + B*x*x + C*x + D


def basic_figure():
    df = pd.read_csv('HD32_test.csv', encoding='utf-8').fillna(0)
    flow = df.loc[:, ['VEH_TOTAL']]
    speed = df.loc[:, ['AVG_SPEED']]
    flow.rename(columns={'VEH_TOTAL':'SUM'}, inplace=True)
    speed.rename(columns={'AVG_SPEED':'SUM'}, inplace=True)
    density = flow / speed
    xdata = flow['SUM']
    ydata = speed['SUM']
    xlist = xdata.values.tolist()
    ylist = ydata.values.tolist()
    xset = set(xlist)
    d = dict()
    # for s in xset:
    #     sum = 0
    #     count = 0
    #     for i in range(0, len(xlist)):
    #         if xlist[i] == s:
    #             sum += ylist[i]
    #             count += 1
    #     d[s] = sum/count
    # plt.plot(d.keys(), d.values(), '.')

    print speed
    plt.scatter(flow, speed, s=2)
    # plt.scatter(density, flow, linewidths=1)
    # plt.scatter(density, speed, linewidths=1)
    # '''拟合test'''
    # A1, B1, C1 = optimize.curve_fit(f_2, xdata, ydata)[0]
    # x1 = np.arange(0, 200, 1)
    # y1 = A1*x1*x1 + B1*x1 + C1
    # plt.plot(x1, y1)
    # '''拟合test'''
    plt.show()


def space_time():
    df = pd.read_csv('space_time.csv', encoding='utf-8').fillna(0)
    plt.scatter()
    print df


def road_visualization_dynamic(road, time_interval, pause_time):

    colors = ['white', 'blue', 'red', 'black']
    cmap = mpl.colors.ListedColormap(colors)

    temp_flow = 0
    temp_flow_fast = 0
    temp_flow_other = 0
    temp_speed = 0
    temp_speed_fast = 0
    temp_speed_other = 0
    temp_travel_time = 0

    '''list to storage'''
    flow_store = list()
    speed_store = list()
    '''list to storage'''

    '''list for basic_figure'''
    flow_list = list()
    speed_list = list()
    density_list = list()
    '''list for basic_figure'''

    plt.ion()
    fig = plt.figure()
    '''可视化界面布局begin'''
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(334)
    ax3 = fig.add_subplot(335)
    # ax4 = fig.add_subplot(336)
    ax5 = fig.add_subplot(337)
    # ax6 = fig.add_subplot(338)
    # ax7 = fig.add_subplot(339)
    ax2.axis('off')
    ax3.axis('off')
    time_space_count = 0
    '''写入CSV'''
    out = open('speed-flow-storage.csv', 'a')
    csv_write = csv.writer(out, dialect='excel')
    title = ['speed1', 'flow1', 'speed2-3', 'flow2-3', 'flow-all']
    csv_write.writerow(title)
    '''写入CSV'''
    '''可视化界面布局end'''
    for t in range(road.simulation_times):
        for i in range(1, road.lanes + 1):
            carr = car.Car()
            if random.uniform(0, 1) < road.prob_in:
                # TODO 初始速度的随机分布
                car.Car.new_car(carr, road, 0, i)
        '''每一时间步一展示数据begin'''
        str_t = 'timestamp= %d' % t
        str_limit_begin = 'limit begin= %d' % (road.limit_begin + 1)
        str_limit_end = 'limit end= %d' % (road.limit_end + 1)
        str_travel_time = 'travel time=%.2f s' % (road.travel_time/road.count_flow if road.count_flow != 0 else 0)
        travel_speed = (road.travel_speed/road.count_flow if road.count_flow != 0 else 0)
        travel_speed_fast = (road.travel_speed_fast/road.count_flow_fast if road.count_flow_fast != 0 else 0)
        travel_speed_other = (road.travel_speed_other/road.count_flow_other if road.count_flow_other != 0 else 0)
        str_travel_speed = 'travel speed (all lanes)=%.2f cells/s' % travel_speed
        str_travel_speed_fast = 'travel speed (fast lane)=%.2f cells/s' % travel_speed_fast
        str_travel_speed_other = 'travel speed (other lanes)=%.2f cells/s' % travel_speed_other
        str_flow = 'traffic flow sum (all lanes)= %d' % road.count_flow
        str_flow_fast = 'traffic flow sum (fast lane)= %d' % road.count_flow_fast
        str_flow_other = 'traffic flow sum (other lanes)= %d' % road.count_flow_other
        str_density = 'traffic density (all lanes)= %.2f' % (road.count_flow/travel_speed if travel_speed != 0 else 0)
        str_switch_counter = 'switch_times= % d' % road.switch_counter
        ax2.text(0, 0.9, str_t)
        ax2.text(0, 0.15, str_density)
        ax2.text(0, 0.6, str_flow_fast)
        ax2.text(0, 0.45, str_flow_other)
        ax2.text(0, 0.3, str_travel_speed)
        # ax2.text(1.5, 0.3, str_travel_speed_fast)
        # ax2.text(1.5, 0.45, str_travel_speed_other)
        # ax2.text(0, 0.6, str_travel_time)
        ax2.text(0, 0.75, str_flow)
        '''每一时间步一展示数据end'''
        '''每t时间步展示数据begin'''
        if t % time_interval == 0:
            interval_flow = road.count_flow - temp_flow
            temp_flow = road.count_flow
            interval_flow_fast = road.count_flow_fast - temp_flow_fast
            temp_flow_fast = road.count_flow_fast
            interval_flow_other = road.count_flow_other - temp_flow_other
            temp_flow_other = road.count_flow_other
            interval_speed = road.travel_speed - temp_speed
            temp_speed = road.travel_speed
            interval_speed_fast = road.travel_speed_fast - temp_speed_fast
            temp_speed_fast = road.travel_speed_fast
            interval_speed_other = road.travel_speed_other - temp_speed_other
            temp_speed_other = road.travel_speed_other
            interval_travel_time = road.travel_time - temp_travel_time
            temp_travel_time = road.travel_time
            interval_travel_speed = interval_speed / interval_flow if interval_flow != 0 else 0
            time_space_y = list()
            time_space_x = list()
            if interval_flow == 0 and interval_speed == 0:
                pass
            else:
                time_space_temp = road.positionArray[road.lane_for_st_figure, road.limit_begin : road.limit_end].tolist()
                for i in range(0, len(time_space_temp)):
                    if time_space_temp[i] == 0:
                        time_space_y.append(time_space_temp[i] + time_space_count)
                        time_space_x.append(i)
                speed_list.append(interval_speed)
                flow_list.append(interval_flow)
                density_list.append((interval_flow / interval_travel_speed if interval_travel_speed != 0 else 0))
                time_space_count += 1
            # ax4.scatter(time_space_x, time_space_y, s=1, c='b')
            ax5.scatter(flow_list, speed_list, c='b')
            ax5.set_xlabel('flow')
            ax5.set_ylabel('speed')
            # ax6.scatter(density_list, speed_list, c='b')
            # ax6.set_xlabel('density')
            # ax6.set_ylabel('speed')
            # ax7.scatter(density_list, flow_list, c='b')
            # ax7.set_xlabel('density')
            # ax7.set_ylabel('flow')
            '''写入CSV'''
            out = open('speed-flow-storage.csv', 'a')
            csv_write = csv.writer(out, dialect='excel')
            newline = [interval_speed_fast, interval_flow_fast, interval_speed_other, interval_flow_other, interval_flow]
            csv_write.writerow(newline)
            '''写入CSV'''
        '''每t时间步展示数据end'''
        str_interval_flow = '15min flow (all lanes)= %d' % interval_flow
        str_interval_flow_fast = '15min flow (fast lane)= %d' % interval_flow_fast
        str_interval_flow_other = '15min flow (other lanes)= %d' % interval_flow_other
        interval_travel_speed = interval_speed / interval_flow if interval_flow != 0 else 0
        interval_travel_speed_fast = interval_speed_fast / interval_flow_fast if interval_flow_fast != 0 else 0
        interval_travel_speed_other = interval_speed_other / interval_flow_other if interval_flow_other != 0 else 0
        str_interval_traval_speed = '15min travel speed (all lanes)= %.2f' % interval_travel_speed
        str_interval_traval_speed_fast = '15min travel speed (fast lane)= %.2f' % interval_travel_speed_fast
        str_interval_traval_speed_oter = '15min travel speed (other lanes)= %.2f' % interval_travel_speed_other
        str_interval_density = '15min density= %.2f' % (interval_flow/interval_travel_speed if interval_travel_speed != 0 else 0)
        str_interval_travel_time = '15min travel time= %.2f' % (interval_travel_time/interval_flow if interval_flow != 0 else 0)
        ax2.text(1, 0.9, str_interval_flow)
        ax2.text(1, 0.75, str_interval_flow_fast)
        ax2.text(1, 0.6, str_interval_flow_other)
        ax2.text(1, 0.15, str_interval_traval_speed_oter)
        ax2.text(1, 0.3, str_interval_traval_speed_fast)
        ax2.text(1, 0.45, str_interval_traval_speed)
        # ax2.text(0, -0.45, str_interval_density)
        # ax2.text(0, -0.6, str_interval_travel_time)
        ax1.imshow(road.positionArray[:, 600:645], cmap=cmap)
        ax1.axis('off')
        plt.pause(pause_time)
        ax2.clear()
        ax2.axis('off')
        road.progress(road.limit_speed)
    plt.ioff()

if __name__ == '__main__':

    colors = ['white', 'blue', 'black']
    cmap = mpl.colors.ListedColormap(colors)

    time_interval = 900
    pause_time = 1

    road = road.Road()
    road_visualization_dynamic(road, time_interval, pause_time)


