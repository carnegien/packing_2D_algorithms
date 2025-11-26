# (Only comments and docstrings translated)
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

class GA(object):
    '''
    Reference: A 2-exchange heuristic for nesting problems (2002)
    '''
    def __init__(self,width,poly_list,nfp_asst=None,generations=10,pop_size=20):
        self.width=width
        self.minimal_rotation=360 # minimal allowed rotation angle
        self.poly_list=poly_list

        self.ga_multi=False # multi-process disabled by default
        if self.ga_multi:
            multiprocessing.set_start_method('spawn',True) 

        self.elite_size=10 # number of elites
        self.mutate_rate=0.1 # mutation probability
        self.generations=generations # number of generations
        self.pop_size=pop_size # population size

        self.history_index_list=[]
        self.history_length_list=[]
        
        if nfp_asst:
            self.NFPAssistant=nfp_asst
        else:
            self.NFPAssistant=NFPAssistant(PolyListProcessor.getPolysVertices(poly_list),get_all_nfp=True)

        self.geneticAlgorithm()

        self.plotRecord()

    # Core GA loop
    def geneticAlgorithm(self):
        self.pop = [] # population
        self.length_record = [] # record lengths per generation
        self.lowest_length_record = [] # record global lowest
        self.global_best_sequence = [] # global best order
        self.global_lowest_length = 9999999999 # global lowest length
        
        # initialize population with random shuffles
        for i in range(0, self.pop_size):
            _list=copy.deepcopy(self.poly_list)
            random.shuffle(_list)
            self.pop.append(_list)

        # iterate generations
        for i in range(0, self.generations):
            print("############################ Compute the ",i+1,"th generation #######################################")
            self.getLengthRanked() # rank by length
            self.getNextGeneration() # produce next generation

            # record generation statistics
            self.length_record.append(self.fitness_ranked[0][1])
            if self.fitness_ranked[0][1]<self.global_lowest_length:
                self.global_lowest_length=self.fitness_ranked[0][1]
                self.global_best_sequence=self.pop[self.fitness_ranked[0][0]]
            self.lowest_length_record.append(self.global_lowest_length)

        blf=BottomLeftFill(self.width,PolyListProcessor.getPolysVertices(self.global_best_sequence),NFPAssistant=self.NFPAssistant)
        blf.showAll()

# (rest of file preserved, comments translated similarly)
