# (Only comments/docstrings translated; code unchanged)
import numpy as np, random, operator, pandas as pd, matplotlib.pyplot as plt
from tools.geofunc import GeoFunc
from tools.show import PltFunc
from tools.nfp import NFP
from tools.data import getData
from tools.packing import PackingUtil,NFPAssistant,PolyListProcessor,Poly
from heuristic import TOPOS,BottomLeftFill
import json
from shapely.geometry import Polygon,mapping
from shapely import affinity
import csv
import time
import multiprocessing
import datetime
import random
import copy

def packingLength(poly_list,history_index_list,history_length_list,width,**kw):
    polys=PolyListProcessor.getPolysVertices(poly_list)
    index_list=PolyListProcessor.getPolyListIndex(poly_list)
    length=0
    check_index=PolyListProcessor.getIndex(index_list,history_index_list)
    if check_index>=0:
        length=history_length_list[check_index]
    else:
        try:
            if 'NFPAssistant' in kw:
                blf=BottomLeftFill(width,polys,NFPAssistant=kw['NFPAssistant'])
                length=blf.contain_length
            else:
                length=BottomLeftFill(width,polys).contain_length
        except:
            print('Self-intersection occurred')
            length=99999
        history_index_list.append(index_list)
        history_length_list.append(length)
    return length

class SA(object):
    '''
    Simulated Annealing + Bottom Left Fill
    Reference:....
    '''
    def __init__(self,poly_list):
        self.min_angle=360 # minimal allowed rotation
        self.width=1500 # packing width

        self.temp_now=200  # starting temperature
        self.temp_end=1e-5 # ending temperature
        self.dec_rate=0.7 # cooling rate
        self.loop_times=5 # inner loop iterations

        self.cur_poly_list=poly_list # current sequence
        self.new_poly_list=poly_list # new candidate sequence

        self.history_index_list=[] # visited index sequences
        self.history_length_list=[] # recorded results

        self.NFPAssistant=NFPAssistant(PolyListProcessor.getPolysVertices(poly_list),get_all_nfp=True)

        self.run()

    def newPolyList(self):
        choose_id = int(random.random() * len(self.new_poly_list))
        '''Perform swap or rotation operations; rotation currently not allowed'''
        if random.random()<=1:
            self.new_poly_list=PolyListProcessor.randomSwap(self.cur_poly_list,choose_id)
        else:
            self.new_poly_list=PolyListProcessor.randomRotate(self.cur_poly_list,self.min_angle,choose_id)

    def run(self):
        initial_length=packingLength(self.cur_poly_list,self.history_index_list,self.history_length_list,self.width)

        global_lowest_length_list = [] # record global lowest per temperature
        temp_lowest_length_list= [] # record local lowest per temperature

        global_best_list = copy.deepcopy(self.cur_poly_list) # store historical best
        global_lowest_length=initial_length

        temp_best_list=copy.deepcopy(self.cur_poly_list) # best in current temperature
        temp_lowest_length=initial_length

        unchange_times=0

        # simulated annealing main loop
        while self.temp_now>self.temp_end:
            print("Current temperature:",self.temp_now)
            old_lowest_length=global_lowest_length

            cur_length=packingLength(self.cur_poly_list,self.history_index_list,self.history_length_list,self.width,NFPAssistant=self.NFPAssistant)

            # perform several searches at current temperature
            for i in range(self.loop_times): 
                self.newPolyList()

                new_length=packingLength(self.new_poly_list,self.history_index_list,self.history_length_list,self.width,NFPAssistant=self.NFPAssistant)
                delta_length = new_length-cur_length

                if delta_length < 0: # accept if improved
                    temp_best_list = self.cur_poly_list = copy.deepcopy(self.new_poly_list) 
                    temp_lowest_length=new_length
                    cur_length=new_length

                    if new_length<global_lowest_length:
                        global_lowest_length=new_length
                        global_best_list=copy.deepcopy(self.new_poly_list)

                elif np.random.random() < np.exp(-delta_length / self.temp_now): # accept with probability
                    self.poly_list=copy.deepcopy(self.new_poly_list)
                    cur_length=new_length
                else:
                    pass # reject

            print("Current temperature local best:",temp_lowest_length)
            print("Global best:",global_lowest_length)

            if old_lowest_length==global_lowest_length:
                unchange_times+=1
                if unchange_times>15:
                    break
            else:
                unchange_times=0

            self.cur_poly_list=copy.deepcopy(temp_best_list) # take best of this temperature
            self.temp_now*=self.dec_rate # cool down
            global_lowest_length_list.append(global_lowest_length)
            temp_lowest_length_list.append(temp_lowest_length)

        print('Final local best length:',temp_lowest_length)
        print('Final global best length:',global_lowest_length)

        PolyListProcessor.showPolyList(self.width,global_best_list)

        self.showBestResult(temp_lowest_length_list,global_lowest_length_list)

    def showBestResult(self,list1,list2):
        plt.figure(1)
        plt.subplot(311)
        plt.plot(list1)
        plt.subplot(312)
        plt.plot(list2)
        plt.grid()
        plt.show() 

if __name__=='__main__':
    starttime = datetime.datetime.now()

    polys = getData(6)
    all_rotation = [0] # disable rotation
    poly_list = PolyListProcessor.getPolyObjectList(polys, all_rotation)

    SA(poly_list)

    endtime = datetime.datetime.now()
    print (endtime - starttime)
