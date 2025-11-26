''' 
Naming convention: class names in PascalCase, other functions and variable names in snake_case.
Shape assumptions: computing NFP and BottomLeftFill should not modify the original polygons.
'''
from tools.geofunc import GeoFunc
from tools.data import getData
from tools.show import PltFunc
from tools.packing import PolyListProcessor,NFPAssistant,BottomLeftFill
import pandas as pd
import json
from shapely.geometry import Polygon,Point,mapping,LineString
from interval import Interval
import copy
import random

precision_error=0.000000001

class FNS():
    '''
    Reference: 2004 Fast neighborhood search for two- and three-dimensional nesting problems
    Summary: Using a quadratic formulation to separate motion in x and y axes and locate positions that minimize intersection area.
    To do: rotation support; apply horizontal/vertical translation and rotation in sequence to reduce layout height
    '''
    def __init__(self,polys):
        self.polys = polys # original input polygons
        self.cur_polys=polys # current polygons
        self.poly_list=[] # stores polygon parameters and changes with cur_polys
        self.width = 1000
        self.height = 999999999
        self.initial()
        self.main()

    def main(self):
        self.shrink()
        self.showResult(current=True)

        self.guidedLocalSearch()

        for i in range(10):
            self.shrink()
            self.guidedLocalSearch()
        
        self.showResult(current=True)
        
    # obtain initial solution and determine top/angle positions
    def initial(self):
        blf = BottomLeftFill(self.width,self.cur_polys)
        self.height = blf.length
        self.updatePolyList()

    # shrink layout height; note cur_polys and poly_list differ!
    def shrink(self):
        self.new_height = self.height*0.95
        print("Shrinking border to %s" % self.new_height)
        for poly in self.cur_polys:
            top_index = GeoFunc.checkTop(poly)
            delta = self.new_height-poly[top_index][1]
            # if overlap occurs, slide vertically
            if delta < 0:
                GeoFunc.slidePoly(poly,0,delta)
        self.updatePolyList()
    
    # display final result
    def showResult(self,**kw):
        if "current" in kw and kw["current"]==True:
            for poly in self.cur_polys:
                PltFunc.addPolygonColor(poly)
            PltFunc.addLine([[0,self.new_height],[self.width,self.new_height]],color="blue")
        if "initial" in kw and kw["initial"]==True:
            for poly in self.polys:
                PltFunc.addPolygon(poly)
            PltFunc.addLine([[0,self.height],[self.width,self.height]],color="blue")
        print(self.polys[0])
        PltFunc.showPlt()

    # ... (rest of file preserved, comments translated similarly)

class ILSQN():
    '''
    Reference: 2009 An iterated local search algorithm based on nonlinear programming for the irregular strip packing problem
    '''
    def __init__(self,poly_list):
        # initial settings
        self.width=1500

        # initialize data and NFP assistant
        polys=PolyListProcessor.getPolysVertices(poly_list)
        self.NFPAssistant=NFPAssistant(polys,get_all_nfp=False)

        # get best solution from BottomLeftFill
        blf=BottomLeftFill(self.width,polys,NFPAssistant=self.NFPAssistant)
        self.best_height=blf.contain_height
        self.cur_height=blf.contain_height

        # current poly_list is assumed to be a placed layout
        self.best_poly_list=copy.deepcopy(poly_list)
        self.cur_poly_list=copy.deepcopy(poly_list)

        self.run()

    # ... rest preserved
