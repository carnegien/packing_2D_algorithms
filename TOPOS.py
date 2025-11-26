"""
This module implements a TOPOS-style sequential packing algorithm.
-----------------------------------
Created on Wed Dec 11, 2019
Authors: seanys, prinway
-----------------------------------
The TOPOS algorithm places polygons one by one and moves them as a whole. This implementation references Bennell's TOPOS Revised.
Note: mid-line cases and some edge cases may still have bugs.
"""
from tools.geofunc import GeoFunc
from tools.show import PltFunc
from tools.data import getData
import tools.packing as packing
from tools.nfp import NFP
from shapely.geometry import Polygon,mapping
from shapely import affinity
import numpy as np, random, operator, pandas as pd, matplotlib.pyplot as plt
import json
import csv
import time
import multiprocessing
import datetime
import random
import copy

class TOPOS(object):
    '''
    TOPOS greedy algorithm: insert polygons one by one and move the whole set.
    This implementation refers to Bennell's TOPOS (Revised).
    Note: some mid-line cases may contain bugs.
    '''
    def __init__(self,original_polys,width):
        self.polys=original_polys
        self.cur_polys=[]
        self.width=width
        self.NFPAssistant=packing.NFPAssistant(self.polys,store_nfp=False,get_all_nfp=True,load_history=True)
        
        self.run()

    def run(self):
        self.cur_polys.append(GeoFunc.getSlide(self.polys[0],1000,1000)) # insert the first polygon
        self.border_left,self.border_right,self.border_bottom,self.border_top=0,0,0,0 # initialize bounding box
        self.border_height,self.border_width=0,0
        for i in range(1,len(self.polys)):
            # update overall bounding box
            self.updateBound()

            # compute union of NFPs with current placed polygons
            feasible_border=Polygon(self.cur_polys[0])
            for fixed_poly in self.cur_polys:
                nfp=self.NFPAssistant.getDirectNFP(fixed_poly,self.polys[i])
                feasible_border=feasible_border.union(Polygon(nfp))
            
            # get all feasible placement points
            feasible_point=self.chooseFeasiblePoint(feasible_border)
            
            # get left/right/top/bottom extents of the polygon
            poly_left_pt,poly_bottom_pt,poly_right_pt,poly_top_pt=GeoFunc.checkBoundPt(self.polys[i])
            poly_left_width,poly_right_width=poly_top_pt[0]-poly_left_pt[0],poly_right_pt[0]-poly_top_pt[0]

            # iterate through feasible points and choose the one with minimal width change
            min_change=999999999999
            target_position=[]
            for pt in feasible_point:
                change=min_change
                if pt[0]-poly_left_width>=self.border_left and pt[0]+poly_right_width<=self.border_right:
                    # polygon does not exceed current borders; set min_change accordingly
                    change=min(self.border_left-pt[0],self.border_left-pt[0])
                elif min_change>0:
                    # polygon exceeds left or right border; compute required expansion
                    change=max(self.border_left-pt[0]+poly_left_width,pt[0]+poly_right_width-self.border_right)
                else:
                    # already exceeding and min_change <= 0, no change needed
                    pass

                if change<min_change:
                    min_change=change
                    target_position=pt
            
            # slide polygon to final position
            reference_point=self.polys[i][GeoFunc.checkTop(self.polys[i])]
            self.cur_polys.append(GeoFunc.getSlide(self.polys[i],target_position[0]-reference_point[0],target_position[1]-reference_point[1]))

        self.slideToBottomLeft()
        self.showResult()

    def updateBound(self):
        '''
        Update bounding box extents
        '''
        border_left,border_bottom,border_right,border_top=GeoFunc.checkBoundValue(self.cur_polys[-1])
        if border_left<self.border_left:
            self.border_left=border_left
        if border_bottom<self.border_bottom:
            self.border_bottom=border_bottom
        if border_right>self.border_right:
            self.border_right=border_right
        if border_top>self.border_top:
            self.border_top=border_top
        self.border_height=self.border_top-self.border_bottom
        self.border_width=self.border_right-self.border_left
    
    def chooseFeasiblePoint(self,border):
        '''Select feasible placement points from a polygonal border'''
        res=mapping(border)
        _arr=[]
        if res["type"]=="MultiPolygon":
            for poly in res["coordinates"]:
                _arr=_arr+self.feasiblePoints(poly)
        else:
            _arr=_arr+self.feasiblePoints(res["coordinates"][0])
        
        return _arr
    
    def feasiblePoints(self,poly):
        '''
        1. Convert a Polygon to a list of candidate points
        2. Remove points that exceed the width bounds
        3. Select intersection points between straight edges and the border
        '''
        result=[]
        for pt in poly:
            # (1) candidate is above current top and total height within allowed width
            feasible1=pt[1]-self.border_top>0 and pt[1]-self.border_top+self.border_height<=self.width
            # (2) candidate is below current bottom and total height within allowed width
            feasible2=self.border_bottom-pt[1]>0 and self.border_bottom-pt[1]+self.border_heigt<=self.width
            # (3) point is inside current top/bottom
            feasible3=pt[1]<=self.border_top and pt[1]>=self.border_bottom
            if feasible1==True or feasible2==True or feasible3==True:
                result.append([pt[0],pt[1]])
        return result

    def slideToBottomLeft(self):
        '''Slide the layout to the bottom-left origin'''
        for poly in self.cur_polys:
            GeoFunc.slidePoly(poly,-self.border_left,-self.border_bottom)

    def showResult(self):
        '''Display the placement result'''
        for poly in self.cur_polys:
            PltFunc.addPolygon(poly)
        PltFunc.showPlt(width=2000,height=2000)


if __name__=='__main__':
    # index from 0-15
    index=6
    polys=getData(index)
    starttime = datetime.datetime.now()
    topos = TOPOS(polys,760)
    endtime = datetime.datetime.now()
    print ("total time: ",endtime - starttime)