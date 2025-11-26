"""
This module implements a Bottom-Left Fill placement algorithm.
-----------------------------------
Created on Wed Dec 11, 2019
Authors: seanys, prinway
-----------------------------------
"""
from tools.geofunc import GeoFunc
from tools.show import PltFunc
from tools.data import getData
import tools.packing as packing
from tools.nfp import NFP
from shapely.geometry import Polygon,mapping
from shapely import affinity
from decimal import Decimal
import numpy as np, random, operator, pandas as pd, matplotlib.pyplot as plt
import json
import csv
import time
import multiprocessing
import datetime
import random
import copy

class BottomLeftFill(object):
    def __init__(self,width,original_polygons,**kw):
        self.choose_nfp=False
        self.width=width
        self.length=150000 # represents a very large length
        self.contain_length=2000
        self.polygons=original_polygons
        self.NFPAssistant=None
        if 'NFPAssistant' in kw:
            self.NFPAssistant=kw["NFPAssistant"]
        self.vertical=False
        if 'vertical' in kw:
            self.vertical=kw['vertical']
        
        print("Total Num:", len(original_polygons))
        self.placeFirstPoly()
        for i in range(1,len(self.polygons)):
            print("############################## Place the ",i+1,"th shape #################################")
            self.placePoly(i)
        
        self.getLength()

    def placeFirstPoly(self):
        poly=self.polygons[0]
        left_index,bottom_index,right_index,top_index=GeoFunc.checkBound(poly) # get bounds
        GeoFunc.slidePoly(poly,-poly[left_index][0],-poly[bottom_index][1]) # slide to bottom-left origin

    def placePoly(self,index):
        adjoin=self.polygons[index]
        # vertical orientation?
        if self.vertical==True:
            ifr=packing.PackingUtil.getInnerFitRectangle(self.polygons[index],self.width,self.length)
        else:
            ifr=packing.PackingUtil.getInnerFitRectangle(self.polygons[index],self.length,self.width)            
        differ_region=Polygon(ifr)

        for main_index in range(0,index):
            main=self.polygons[main_index]
            if self.NFPAssistant==None:
                nfp=NFP(main,adjoin).nfp
            else:
                nfp=self.NFPAssistant.getDirectNFP(main,adjoin)
            nfp_poly=Polygon(nfp)
            try:
                differ_region=differ_region.difference(nfp_poly)
            except:
                print('NFP failure, areas of polygons are:')
                self.showAll()
                for poly in main,adjoin:
                    print(Polygon(poly).area)
                self.showPolys([main]+[adjoin]+[nfp])
                print('NFP loaded from: ',self.NFPAssistant.history_path)

        differ=GeoFunc.polyToArr(differ_region)
        differ_index=self.getBottomLeft(differ)
        refer_pt_index=GeoFunc.checkTop(adjoin)
        GeoFunc.slideToPoint(self.polygons[index],adjoin[refer_pt_index],differ[differ_index])        

    def getBottomLeft(self,poly):
        '''
        Get the bottom-most (priority left) point. If multiple leftmost points exist choose the lower one.
        '''
        bl=[] # all bottom-left candidate points
        _min=999999
        # choose the leftmost point
        for i,pt in enumerate(poly):
            pt_object={
                    "index":i,
                    "x":pt[0],
                    "y":pt[1]
            }
            if self.vertical==True:
                target=pt[1]
            else:
                target=pt[0]
            if target<_min:
                _min=target
                bl=[pt_object]
            elif target==_min:
                bl.append(pt_object)
        if len(bl)==1:
            return bl[0]["index"]
        else:
            if self.vertical==True:
                target="x"                
            else:
                target="y"
            _min=bl[0][target]
            one_pt=bl[0]
            for pt_index in range(1,len(bl)):
                if bl[pt_index][target]<_min:
                    one_pt=bl[pt_index]
                    _min=one_pt["y"]
            return one_pt["index"]

    def showAll(self):
        for i in range(0,len(self.polygons)):
            PltFunc.addPolygon(self.polygons[i])
        length=max(self.width,self.contain_length)
        PltFunc.showPlt(width=max(length,self.width),height=max(length,self.width),minus=100)    

    def showPolys(self,polys):
        for i in range(0,len(polys)-1):
            PltFunc.addPolygon(polys[i])
        PltFunc.addPolygonColor(polys[len(polys)-1])
        length=max(self.width,self.contain_length)
        PltFunc.showPlt(width=max(length,self.width),height=max(length,self.width),minus=200)    

    def getLength(self):
        _max=0
        for i in range(0,len(self.polygons)):
            if self.vertical==True:
                extreme_index=GeoFunc.checkTop(self.polygons[i])
                extreme=self.polygons[i][extreme_index][1]
            else:
                extreme_index=GeoFunc.checkRight(self.polygons[i])
                extreme=self.polygons[i][extreme_index][0]
            if extreme>_max:
                _max=extreme
        self.contain_length=_max
        return _max

if __name__=='__main__':

    """
    df = pd.read_csv("data/christmas_trees.csv")
    all_polys = []
    for i in range(0,df.shape[0]):
        for j in range(0,df['num'][i]):
            poly=json.loads(df['polygon'][i])
            GeoFunc.normData(poly,Decimal('1e15'))
            all_polys.append(poly)
    """

    nfp_ass=packing.NFPAssistant(all_polys,store_nfp=True,get_all_nfp=True,load_history=False)
    # nfp_ass=packing.NFPAssistant(polys,store_nfp=False,get_all_nfp=True,load_history=True)
    # nfp_ass=packing.NFPAssistant(polys,store_nfp=False,get_all_nfp=False,load_history=False)

    starttime = datetime.datetime.now()
    # bfl=BottomLeftFill(2000,polys,vertical=False)
    bfl=BottomLeftFill(760,polys,vertical=False,NFPAssistant=nfp_ass)
    
    endtime = datetime.datetime.now()
    print ("total time: ",endtime - starttime)
    bfl.showAll()

