"""
This version begins performance optimizations and attempts to use direct geometric computations where possible.
-----------------------------------
Created on Wed June 10, 2020
Authors: seanys, prinway
-----------------------------------
"""
from tools.show import PltFunc
from tools.assistant import OutputFunc
from tools.lp_assistant import GeometryAssistant
from shapely.geometry import Polygon,Point,mapping,LineString
import pandas as pd
import numpy as np
from copy import deepcopy
from random import randint
import time
import csv # write csv
import json
import operator
import cProfile

compute_bias = 0.000001
pd_range = 5

grid_precision = 10
# digital_precision = 0.001
digital_precision = 1

zfill_num = 5

class LPSearch(object):
    def __init__(self, **kw):
        self.line_index = 0
        self.max_time = 7200
        self.loadKey = False

        if "line_index" in kw:
            self.line_index = kw["line_index"]
        if "max_time" in kw:
            self.max_time = kw["max_time"]

        self.initialProblem(self.line_index) # load problem
        self.ration_dec, self.ration_inc = 0.04, 0.01
        self.TEST_MODEL = True
        print("Test model (timeout 60s):%s"%self.TEST_MODEL)

        _str = "Initial utilization ratio: " + str(self.total_area/(self.cur_length*self.width))
        OutputFunc.outputAttention(self.set_name,_str)
        
        self.recordStatus("record/lp_result/" + self.set_name + "_result_success.csv")
        self.recordStatus("record/lp_result/" + self.set_name + "_result_fail.csv")
        self.main()

    def main(self):
        '''Core algorithm steps'''
        self.shrinkBorder() # shrink placement border and update width/length
        if self.TEST_MODEL == True:
            self.max_time = 60
        self.start_time = time.time()
        search_status = 0
        search_times = 0

        while time.time() - self.start_time < self.max_time:
            self.showPolys()
            self.updateAllPairPD() # update current overlaps
            feasible = self.minimizeOverlap() # try to minimize overlap
            if feasible == True or search_times == 5:
                search_status = 0
                _str = "Current utilization ratio: " + str(self.total_area/(self.cur_length*self.width))
                OutputFunc.outputInfo(self.set_name,_str)
                self.best_orientation = deepcopy(self.orientation) # update orientation
                self.best_polys = deepcopy(self.polys) # update polygons
                self.best_length = self.cur_length # update best length
                with open("record/lp_result/" + self.set_name + "_result_success.csv","a+") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows([[time.asctime( time.localtime(time.time()) ),self.line_index,search_times, feasible,self.best_length,self.total_area/(self.best_length*self.width),self.orientation]])
                self.shrinkBorder() # shrink border and move polygons inside
                search_times = 0
            else:
                search_times = search_times + 1
                OutputFunc.outputWarning(self.set_name, "Result infeasible, retrying search")
                with open("record/lp_result/" + self.set_name + "_result_fail.csv","a+") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows([[time.asctime( time.localtime(time.time()) ),self.line_index,feasible,self.cur_length,self.total_area/(self.cur_length*self.width),self.orientation,self.polys]])
                if search_status == 1:
                    self.shrinkBorder()
                    search_status = 0
                else:
                    self.extendBorder() # extend border and retry
                    search_status = 1    
            if self.total_area/(self.best_length*self.width) > 0.995:
                break

    # (rest of file preserved, comments translated similarly)
