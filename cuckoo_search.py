'''
    Guided Cuckoo Search (GCS)
    Notes:
        - If two polygons have no movement then recomputation depth is not needed.
'''
import math
import random
import numpy as np
import matplotlib.pyplot as plt
from tools.nfp import NFP
from tools.geofunc import GeoFunc
from tools.show import PltFunc
from tools.packing import PackingUtil

class GCS(object):
    def __init__(self, polygons):
        self.polygons = polygons  # initial solution
        self.n_polys = len(self.polygons)
        self.r_dec = 0.1  # decrease ratio for rectangle height
        self.r_inc = 0.1  # increase ratio for rectangle height
        self.W = 1500  # rectangle width (fixed)
        self.n_c = 20  # number of cuckoos per generation
        self.n_mo = 20  # maximum iterations for MinimizeOverlap
        self.maxGen = 10  # max generations
        self.penalty = np.ones((self.n_polys, self.n_polys))  # penalty weight
        self.depth = np.zeros((self.n_polys, self.n_polys))  # penetration depth
        self.percentage = 0.5  # fraction to replace each generation
        self.bestF = 999999  # current best fitness
        print('GCS init:', self.n_polys, 'polygons')

    def GuidedCuckooSearch(self, H, N):
        '''
        H: initial rectangle height
        N: maximum iteration limit
        '''
        self.H = H
        H_best = self.H
        n_cur = 0
        while n_cur <= N:
            original_polygons = list(self.polygons)  # backup current solution
            it = self.MinimizeOverlap(0, 0, 0)
            if it < self.n_mo:  # feasible solution found
                H_best = self.H
                self.H = (1-self.r_dec)*self.H
                print('H--: ', self.H)
            else:
                # not feasible, revert and increase H
                self.polygons = original_polygons
                self.H = (1+self.r_inc)*self.H
                print('H++: ', self.H)
            n_cur = n_cur+1
            self.showAll()
        return H_best

    def CuckooSearch(self, poly_id, ori=''):
        '''
        poly_id: current polygon index
        ori: allowed rotation angle
        '''
        cuckoos = []
        poly = self.polygons[poly_id]
        R = PackingUtil.getInnerFitRectangle(poly,self.W, self.H)  # compute inner-fit rectangle for the polygon
        i = 0
        while i < self.n_c:  # generate initial population
            c = Cuckoo(R)
            if self.censorCuckoo(c) == False:
                continue
            cuckoos.append(c)
            print(c.getXY())
            i = i+1
        bestCuckoo = cuckoos[0]
        t = 0
        while t < self.maxGen:  # search loop
            c_i = random.choice(cuckoos)
            # generate new cuckoo by Levy flight
            newCuckooFlag = False
            while newCuckooFlag == False:
                newX, newY = self.getCuckoos_Levy(1, bestCuckoo)
                c_i.setXY(newX[0], newY[0])
                if self.censorCuckoo(c_i):
                    newCuckooFlag = True

