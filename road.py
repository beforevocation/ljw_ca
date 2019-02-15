#coding:utf-8
#!/usr/bin/env python
import numpy as np
import sys
import random
import csv
import ConfigParser

HAVECAR = 1
WALL = 3
EMPTY = 0
CONGESTION = 2
PROBSLOW = 0.1


class Road(object):
    def __init__(self):
        cp = ConfigParser.SafeConfigParser()
        cp.read('road.conf')
        self.simulation_times = cp.getint('road', 'simulation_times')
        self.lanes = cp.getint('road', 'lanes')
        self.length = cp.getint('road', 'road_length')
        self.positionArray = np.zeros((self.lanes + 2, self.length))
        self.speedArray = np.zeros((self.lanes + 2, self.length))
        self.speedCounter = np.zeros((self.lanes + 2, self.length))
        self.timeWaited = np.zeros((self.lanes + 2, self.length))
        self.positionArray[0, :] = WALL
        self.positionArray[self.lanes + 1, :] = WALL
        self.speedArray[0, :] = WALL
        self.speedArray[self.lanes + 1, :] = WALL
        self.speedCounter[0, :] = WALL
        self.speedCounter[self.lanes + 1, :] = WALL
        self.timeWaited[0, :] = WALL
        self.timeWaited[self.lanes + 1, :] = WALL
        self.vmax = cp.getint('road', 'vmax')
        self.prob_in = cp.getfloat('road', 'pro_in')
        self.is_limit = cp.getboolean('road', 'islimit')
        self.limit_begin = cp.getint('road', 'limit_begin')
        self.limit_end = cp.getint('road', 'limit_end')
        self.lane_for_st_figure = cp.getint('road', 'lane_for_st_figure')
        self.count_flow = 0
        self.travel_time = 0
        self.travel_speed = 0
        self.switch_lane_prob = cp.getfloat('road', 'switch_lane_prob')
        self.switch_counter = 0
        self.limit_speed = cp.getint('road', 'limit_speed')
        self.iscongestion = cp.getboolean('road', 'iscongestion')
        self.vmax1 = cp.getint('road', 'vmax1')
        self.vmax2 = cp.getint('road', 'vmax2')
        self.vmax3 = cp.getint('road', 'vmax3')
        self.count_flow_fast = 0
        self.count_flow_other = 0
        self.travel_time_fast = 0
        self.travel_time_other = 0
        self.travel_speed_fast = 0
        self.travel_speed_other = 0
        if self.iscongestion:
            self.congestion_point_lane = cp.getint('road', 'congestion_point_lane')
            self.congestion_point_point = cp.getint('road', 'congestion_point_point')
            self.congestion_length = cp.getint('road', 'congestion_length')
            self.positionArray[self.congestion_point_lane,
            self.congestion_point_point: self.congestion_point_point + self.congestion_length] = CONGESTION
        self.time_can_wait = cp.getint('road', 'time_can_wait')
        self.switch_left_prob = cp.getfloat('road', 'switch_left_prob')

    def get_vmax(self, lane):
        if lane == 1:
            return self.vmax1
        elif lane == 2:
            return self.vmax2
        elif lane == 3:
            return self.vmax3

    def progeress_dqn(self, speed, input_actions):
        self.progress(speed)

    def progress(self, speed):
        '''中间量'''
        limit_speed = speed
        positionArray = self.positionArray
        speedArray = self.speedArray
        speedCounter = self.speedCounter
        timeWaited = self.timeWaited
        islimit = False
        '''中间量'''
        '''中间量：只有减速步的时候用'''
        gap = np.zeros(positionArray.shape)
        left_change_condition = np.zeros(positionArray.shape)
        right_change_condition = np.zeros(positionArray.shape)
        left_change_real = np.zeros(positionArray.shape)
        right_change_real = np.zeros(positionArray.shape)
        '''中间量：只有减速步的时候用'''
        for i in range(1, positionArray.shape[0] - 1):
            gap_position_temp = sys.maxint
            for j in range(positionArray.shape[1] - 1, -1, -1):
                '''确定当前的vmax：vmax or limit_speed'''
                vmax = self.get_vmax(i)
                if positionArray[i, j] == 1:
                    if positionArray[i, j] == 1 and self.is_limit and self.limit_begin <= j <= self.limit_end:
                        islimit = True
                        vmax = limit_speed
                    else:
                        islimit = False
                '''确定当前的vmax：vmax or limit_speed'''
                '''加速步骤begin'''
                speedArray[i, j] = min(speedArray[i, j] + 1, vmax)
                '''加速步骤end'''
                '''计算前车距离begin'''
                if positionArray[i, j] == 1 or positionArray[i, j] == 2:
                    if gap_position_temp - j - 1 < 0:
                        raise RuntimeError('gap error')
                    gap[i, j] = gap_position_temp - j - 1
                    gap_position_temp = j
                '''计算前车距离end'''
                '''行程开始时间累计begin'''
                if self.limit_begin <= j <= self.limit_end and speedCounter[i, j] != 0:
                    speedCounter[i, j] += 1
                '''行程开始时间累计end'''
        '''逐车道换道begin'''
        for i in range(1, self.lanes + 1):
            switch_lane(positionArray, i, self.lanes, self.vmax, right_change_condition, left_change_condition,
                        speedArray, gap, left_change_real, right_change_real, self.switch_lane_prob, speedCounter, self, timeWaited, islimit)
        '''逐车道换道end'''
        '''换道后更新前车距离begin'''
        gap = np.zeros(positionArray.shape)
        for i in range(1, positionArray.shape[0] - 1):
            gap_position_temp = sys.maxint
            for j in range(positionArray.shape[1] - 1, -1, -1):
                if positionArray[i, j] == 1 or positionArray[i, j] == 2:
                    if gap_position_temp - j - 1 < 0:
                        raise RuntimeError('gap error')
                    gap[i, j] = gap_position_temp - j - 1
                    gap_position_temp = j
        '''换道后更新前车距离end'''
        '''减速步、随机慢化步begin'''
        for i in range(1, positionArray.shape[0] - 1):
            # 计数器，第1辆车和第2辆车减速步特殊处理
            count = 1
            gap_position_temp2 = sys.maxint
            for j in range(positionArray.shape[1] - 1, -1, -1):
                '''确定当前的vmax：vmax or limit_speed'''
                vmax = limit_speed if (positionArray[i, j] == 1 and self.is_limit and self.limit_begin <= j <= self.limit_end) else self.vmax
                '''确定当前的vmax：vmax or limit_speed'''
                '''减速步begin'''
                if positionArray[i, j] == 1 or positionArray[i, j] == 2:
                    if positionArray[i, j] == 2:
                        pass
                    elif gap_position_temp2 < positionArray.shape[1] and positionArray[i, gap_position_temp2] == 2:
                        temp_speed = min(speedArray[i, j], gap[i, j])
                        speedArray[i, j] = max(temp_speed, 0)
                    elif count == 1:
                        pass
                    elif count == 2:
                        temp_speed = min(speedArray[i, j], gap[i, j])
                        speedArray[i, j] = max(temp_speed, 0)
                    else:
                        d = max(0, gap[i, gap_position_temp2] - 1)
                        vmax_before = limit_speed if (self.is_limit and self.limit_begin <= gap_position_temp2 <= self.limit_end) else self.vmax
                        vq = min(vmax_before - 1, d)
                        vq = min(vq, speedArray[i, gap_position_temp2])
                        speedArray[i, j] = min(speedArray[i, j], gap[i, j] + vq)
                        if speedArray[i, j] > d + gap[i, j]:
                            raise RuntimeError('ve error')
                    count += 1
                    gap_position_temp2 = j
                    if speedArray[i, j] < 0:
                        raise RuntimeError('v error')
                '''减速步end'''
                '''随机慢化步begin'''
                if (positionArray[i, j] == 1 and random.uniform(0, 1) <= PROBSLOW):
                    speedArray[i, j] = max(speedArray[i, j] - 1, 0)
                '''随机慢化步end'''
        '''减速步、随机慢化步end'''
        for i in range(1, positionArray.shape[0] - 1):
            for j in range(positionArray.shape[1] - 1, -1, -1):
                '''Nasch位置更新步begin'''
                if (positionArray[i, j] == 1):
                    position_next = int(j + speedArray[i, j])
                    if position_next != j:
                        if position_next < positionArray.shape[1] and position_next != 1:
                            for c in range(j + 1, position_next + 1):
                                if positionArray[i, c] == 1:
                                    print 'i= %d' % i
                                    print 'j= %d' % j
                                    print 'c= %d' % c
                                    print 'i speed= %d' % speedArray[i, j]
                                    print 'position_next= %d' % position_next
                                    raise RuntimeError('car conflict')
                                if positionArray[i, c] == 2:
                                    print 'i= %d' % i
                                    print 'j= %d' % j
                                    print 'c= %d' % c
                                    print 'i speed= %d' % speedArray[i, j]
                                    print 'position_next= %d' % position_next
                                    print 'gap= %d' % gap[i, j]
                                    raise RuntimeError('congestion conflict')
                        '''流量&总行程时间&总行程车速统计begin'''
                        if j <= self.limit_end <= position_next:
                            if i == 1:
                                self.count_flow_fast += 1
                                self.travel_time_fast += speedCounter[i, j]
                                self.travel_speed_fast += (self.limit_end - self.limit_begin) / speedCounter[i, j]
                            elif i != 1:
                                self.count_flow_other += 1
                                self.travel_time_other += speedCounter[i, j]
                                self.travel_speed_other += (self.limit_end - self.limit_begin) / speedCounter[i, j]
                            self.count_flow += 1
                            self.travel_time += speedCounter[i, j]
                            self.travel_speed += (self.limit_end - self.limit_begin) / speedCounter[i, j]
                        '''流量&总行程时间&总行程车速统计end'''
                        if (position_next < positionArray.shape[1]):
                            positionArray[i, position_next] = 1
                            speedArray[i, position_next] = speedArray[i, j]
                            speedCounter[i, position_next] = speedCounter[i, j]
                            timeWaited[i, position_next] = 0
                        positionArray[i, j] = 0
                        speedArray[i, j] = 0
                        speedCounter[i, j] = 0
                        timeWaited[i, j] = 0
                    elif position_next == j and j != 0:
                        timeWaited[i, j] += 1
                '''Nasch位置更新步end'''
        return positionArray


# def prepare_space_time(positionArray, lane):
#     out = open('space_time.csv', mode='a')
#     csv_writer = csv.writer(out, dialect='excel')
#     csv_writer.writerow(positionArray[lane, :])


def switch_lane(positionArray, i, lanes, vmax, right_change_condition, left_change_condition, speedArray, gap, left_change_real, right_change_real, switch_lane_prob, speedCounter, road, timeWaited, islimit):
    for j in range(positionArray.shape[1] - 1, -1, -1):
        change_force = False
        if positionArray[i, j] == 1 and road.iscongestion and i == road.congestion_point_lane and j < road.congestion_point_point and j + vmax > road.congestion_point_point:
            change_force = True
        if (timeWaited[i, j] != 0 and timeWaited[i, j] % (road.time_can_wait * 2) == 0) or change_force:
            '''计算换道条件begin'''
            if positionArray[i, j] == 1:
                if i == 1:
                    change = True
                    '''判断位置当量begin'''
                    if j - vmax - 1 >= 0:
                        for d in range(j - 1, j - vmax - 1, -1):
                            if positionArray[i + 1, d] == 1:
                                if d + speedArray[i + 1, d] > j + speedArray[i, j]:
                                    change = False
                                break
                    '''判断位置当量end'''
                    if positionArray[i + 1, j] == 1 or positionArray[i + 1, j] == 2:
                        change = False
                    right_change_condition[i, j] = change
                elif i == lanes:
                    change = True
                    '''判断位置当量begin'''
                    if j - vmax - 1 >= 0:
                        for d in range(j - 1, j - vmax - 1, -1):
                            if positionArray[i - 1, d] == 1:
                                if d + speedArray[i - 1, d] > j + speedArray[i, j]:
                                    change = False
                                break
                    '''判断位置当量begin'''
                    if positionArray[i - 1, j] == 1 or positionArray[i - 1, j] == 2:
                        change = False
                    left_change_condition[i, j] = change
                elif 1 < i < lanes:
                    change_left = True
                    change_right = True
                    '''判断位置当量begin'''
                    if j - vmax - 1 >= 0:
                        for d in range(j - 1, j - vmax - 1, -1):
                            if positionArray[i - 1, d] == 1:
                                if d + speedArray[i - 1, d] > j + speedArray[i, j]:
                                    change_left = False
                                break
                    '''判断位置当量begin'''
                    '''判断位置当量begin'''
                    if j - vmax - 1 >= 0:
                        for d in range(j - 1, j - vmax - 1, -1):
                            if positionArray[i + 1, d] == 1:
                                if d + speedArray[i + 1, d] > j + speedArray[i, j]:
                                    change_right = False
                                break
                    '''判断位置当量begin'''
                    if positionArray[i - 1, j] == 1 or positionArray[i - 1, j] == 2:
                        change_left = False
                    if positionArray[i + 1, j] == 1 or positionArray[i + 1, j] == 2:
                        change_right = False
                    left_change_condition[i, j] = change_left
                    right_change_condition[i, j] = change_right
            '''计算换道条件end'''
            '''计算是否满足换道动机（即是否换道）begin'''
            if positionArray[i, j] == 1:
                if i == 1:
                    if (gap[i, j] == 0 and right_change_condition[i, j] == 1 and random.uniform(0, 1) < switch_lane_prob) or (change_force and right_change_condition[i, j] == 1):
                        right_change_real[i, j] = 1
                elif 1 < i < lanes:
                    if (gap[i, j] == 0 and right_change_condition[i, j] == 1 and random.uniform(0, 1) < switch_lane_prob) or (change_force and right_change_condition[i, j] == 1):
                        right_change_real[i, j] = 1
                    if (gap[i, j] == 0 and left_change_condition[i, j] == 1 and random.uniform(0, 1) < switch_lane_prob) or (change_force and left_change_condition[i, j] == 1):
                        left_change_real[i, j] = 1
                elif i == lanes:
                    if (gap[i, j] == 0 and left_change_condition[i, j] == 1 and random.uniform(0, 1) < switch_lane_prob) or (change_force and left_change_condition[i, j] == 1):
                        left_change_real[i, j] = 1
            '''计算是否满足换道动机（即是否换道）end'''
            '''进行换道begin'''
            if positionArray[i, j] == 1 and (left_change_real[i, j] == 1 or right_change_real[i, j] == 1):
                if i == 1:
                    if positionArray[i + 1, j] == 1:
                        print 'lane= %d' % i
                        print 'j= %d' % j
                        raise RuntimeError('switch error')
                    positionArray[i + 1, j] = 1
                    speedArray[i + 1, j] = speedArray[i, j]
                    speedCounter[i + 1, j] = speedCounter[i, j]
                    timeWaited[i + 1, j] = 0
                elif 1 < i < lanes and left_change_real[i, j] == 1 and random.uniform(0, 1) < road.switch_left_prob:
                    if left_change_real[i, j] == 1 and right_change_real[i, j] != 1:
                        if positionArray[i - 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i - 1, j] = 1
                        speedArray[i - 1, j] = speedArray[i, j]
                        speedCounter[i - 1, j] = speedCounter[i, j]
                        timeWaited[i - 1, j] = 0
                    if left_change_real[i, j] != 1 and right_change_real[i, j] == 1:
                        if positionArray[i + 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i + 1, j] = 1
                        speedArray[i + 1, j] = speedArray[i, j]
                        speedCounter[i + 1, j] = speedCounter[i, j]
                        timeWaited[i + 1, j] = 0
                    if left_change_real[i, j] == 1 and right_change_real[i, j] == 1 and random.uniform(0, 1) < road.switch_left_prob:
                        if positionArray[i - 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i - 1, j] = 1
                        speedArray[i - 1, j] = speedArray[i, j]
                        speedCounter[i - 1, j] = speedCounter[i, j]
                        timeWaited[i - 1, j] = 0
                    elif right_change_real[i, j] == 1 and left_change_real[i, j] == 1:
                        if positionArray[i + 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i + 1, j] = 1
                        speedArray[i + 1, j] = speedArray[i, j]
                        speedCounter[i + 1, j] = speedCounter[i, j]
                        timeWaited[i + 1, j] = 0
                elif i == lanes:
                    if positionArray[i - 1, j] == 1:
                        print 'lane= %d' % i
                        print 'j= %d' % j
                        raise RuntimeError('switch error')
                    positionArray[i - 1, j] = 1
                    speedArray[i - 1, j] = speedArray[i, j]
                    speedCounter[i - 1, j] = speedCounter[i, j]
                    timeWaited[i - 1, j] = 0
                positionArray[i, j] = 0
                speedArray[i, j] = 0
                speedCounter[i, j] = 0
                road.switch_counter += 1
                timeWaited[i, j] = 0
            elif positionArray[i, j] == 1 and j != 0 and (left_change_real[i, j] != 1 and right_change_real[i, j] != 1):
                timeWaited[i, j] += 1
            '''进行换道end'''
        else:
            '''计算换道条件begin'''
            if positionArray[i, j] == 1:
                if i == 1:
                    change = True
                    tempvmax1 = vmax if islimit else road.get_vmax(i + 1)
                    '''后车距离'''
                    for r in range(j - tempvmax1 - 1, j + 1):
                        if positionArray[i + 1, r] == 1 or positionArray[i + 1, r] == 2:
                            change = False
                            break
                    '''后车距离'''
                    right_change_condition[i, j] = change
                elif i == lanes:
                    change = True
                    tempvmax2 = vmax if islimit else road.get_vmax(i - 1)
                    for l in range(j - tempvmax2 - 1, j + 1):
                        if positionArray[i - 1, l] == 1 or positionArray[i - 1, l] == 2:
                            change = False
                            break
                    left_change_condition[i, j] = change
                elif 1 < i < lanes:
                    change_left = True
                    change_right = True
                    tempvmaxl = vmax if islimit else road.get_vmax(i - 1)
                    tempvmaxr = vmax if islimit else road.get_vmax(i + 1)
                    for l in range(j - tempvmaxl - 1, j + 1):
                        if positionArray[i - 1, l] == 1 or positionArray[i - 1, l] == 2:
                            change_left = False
                            break
                    for r in range(j - tempvmaxr - 1, j + 1):
                        if positionArray[i + 1, r] == 1 or positionArray[i + 1, r] == 2:
                            change_right = False
                            break
                    left_change_condition[i, j] = change_left
                    right_change_condition[i, j] = change_right
            '''计算换道条件end'''
            '''计算是否满足换道动机（即是否换道）begin'''
            if positionArray[i, j] == 1:
                if i == 1:
                    '''前车距离'''
                    drf_condition = True
                    if right_change_condition[i, j] == 1 and j + road.get_vmax(i + 1) + 1 < road.length:
                        drf = 0
                        for r in range(j + 1, j + road.get_vmax(i + 1) + 1):
                            if positionArray[i + 1, r] == 1 or positionArray[i + 1, r] == 2:
                                drf = r - j
                                break
                        if drf >= min(speedArray[i, j] + 1, vmax):
                            drf_condition = False
                    '''前车距离'''
                    if min(speedArray[i, j] + 1, vmax) > gap[i, j] and right_change_condition[
                        i, j] == 1 and random.uniform(
                            0, 1) < switch_lane_prob and drf_condition:
                        right_change_real[i, j] = 1
                elif 1 < i < lanes:
                    '''前车距离begin'''
                    drf_condition = True
                    if left_change_condition[i, j] == 1 and j + road.get_vmax(i + 1) + 1 < road.length:
                        drf = 0
                        for r in range(j + 1, j + road.get_vmax(i + 1) + 1):
                            if positionArray[i + 1, r] == 1 or positionArray[i + 1, r] == 2:
                                drf = r - j
                                break
                        if drf >= min(speedArray[i, j] + 1, vmax):
                            drf_condition = False
                    '''前车距离end'''
                    if min(speedArray[i, j] + 1, vmax) > gap[i, j] and right_change_condition[
                        i, j] == 1 and random.uniform(
                            0, 1) < switch_lane_prob and drf_condition:
                        right_change_real[i, j] = 1
                    '''1车道前车距离begin'''
                    dlf_condition = True
                    if left_change_condition[i, j] == 1 and j + road.get_vmax(i - 1) + 1 < road.length:
                        drf = 0
                        for r in range(j + 1, j + road.get_vmax(i - 1) + 1):
                            if positionArray[i - 1, r] == 1 or positionArray[i - 1, r] == 2:
                                drf = r - j
                                break
                        if drf >= min(speedArray[i, j] + 1, vmax):
                            dlf_condition = False
                    '''1车道前车距离end'''
                    if left_change_condition[
                        i, j] == 1 and random.uniform(
                            0, 1) < switch_lane_prob and dlf_condition:
                        left_change_real[i, j] = 1
                elif i == lanes:
                    '''前车距离'''
                    dlf_condition = True
                    if left_change_condition[i, j] == 1 and j + tempvmax2 + 1 < road.length:
                        drf = 0
                        for r in range(j + 1, j + tempvmax2 + 1):
                            if positionArray[i - 1, r] == 1 or positionArray[i - 1, r] == 2:
                                drf = r - j
                                break
                        if drf >= min(speedArray[i, j] + 1, vmax):
                            dlf_condition = False
                    '''前车距离'''
                    if left_change_condition[
                        i, j] == 1 and random.uniform(
                            0, 1) < switch_lane_prob and dlf_condition:
                        left_change_real[i, j] = 1
            '''计算是否满足换道动机（即是否换道）end'''
            '''进行换道begin'''
            if positionArray[i, j] == 1 and (left_change_real[i, j] == 1 or right_change_real[i, j] == 1):
                if i == 1:
                    if positionArray[i + 1, j] == 1:
                        print 'lane= %d' % i
                        print 'j= %d' % j
                        raise RuntimeError('switch error')
                    positionArray[i + 1, j] = 1
                    speedArray[i + 1, j] = speedArray[i, j]
                    speedCounter[i + 1, j] = speedCounter[i, j]
                    timeWaited[i + 1, j] = 0
                elif 1 < i < lanes:
                    if left_change_real[i, j] == 1 and right_change_real[i, j] != 1:
                        if positionArray[i - 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i - 1, j] = 1
                        speedArray[i - 1, j] = speedArray[i, j]
                        speedCounter[i - 1, j] = speedCounter[i, j]
                        timeWaited[i - 1, j] = 0
                    if right_change_real[i, j] == 1 and left_change_real[i, j] != 1:
                        if positionArray[i + 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i + 1, j] = 1
                        speedArray[i + 1, j] = speedArray[i, j]
                        speedCounter[i + 1, j] = speedCounter[i, j]
                        timeWaited[i + 1, j] = 0
                    if right_change_real[i, j] == 1 and left_change_real[i, j] == 1 and random.uniform(0, 1) < road.switch_left_prob:
                        if positionArray[i - 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i - 1, j] = 1
                        speedArray[i - 1, j] = speedArray[i, j]
                        speedCounter[i - 1, j] = speedCounter[i, j]
                        timeWaited[i - 1, j] = 0
                    elif right_change_real[i, j] == 1 and left_change_real[i, j] == 1:
                        if positionArray[i + 1, j] == 1:
                            print 'lane= %d' % i
                            print 'j= %d' % j
                            raise RuntimeError('switch error')
                        positionArray[i + 1, j] = 1
                        speedArray[i + 1, j] = speedArray[i, j]
                        speedCounter[i + 1, j] = speedCounter[i, j]
                        timeWaited[i + 1, j] = 0
                elif i == lanes:
                    if positionArray[i - 1, j] == 1:
                        print 'lane= %d' % i
                        print 'j= %d' % j
                        raise RuntimeError('switch error')
                    positionArray[i - 1, j] = 1
                    speedArray[i - 1, j] = speedArray[i, j]
                    speedCounter[i - 1, j] = speedCounter[i, j]
                    timeWaited[i - 1, j] = 0
                positionArray[i, j] = 0
                speedArray[i, j] = 0
                speedCounter[i, j] = 0
                road.switch_counter += 1
                timeWaited[i, j] = 0
            elif positionArray[i, j] == 1 and j != 0 and (left_change_real[i, j] != 1 and right_change_real[i, j] != 1):
                timeWaited[i, j] += 1
            '''进行换道end'''


