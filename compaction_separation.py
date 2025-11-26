"""
This module implements separation (remove overlaps) and compaction (shrink borders).
-----------------------------------
Created on Wed Dec 11, 2020
Authors: seanys, prinway
-----------------------------------
Note: This file will be updated soon; currently it contains known issues.
"""
from tools.geofunc import GeoFunc
from tools.show import PltFunc
from tools.lp import sovleLP,problem
from tools.lp_assistant import LPAssistant
import pandas as pd
import json
from shapely.geometry import Polygon,Point,mapping,LineString
from interval import Interval
import copy
import random
import math
    
class LPFunction(object):
    '''
    Reference: Solving Irregular Strip Packing problems by hybridising simulated annealing and linear programming
    Purpose: provide compaction and separation utilities
    '''
    def __init__(self,polys,poly_status,width,length,_type):
        self._type=_type
        self.all_nfp=pd.read_csv("/Users/sean/Documents/Projects/Data/fu_simplify.csv")
        self.poly_status=copy.deepcopy(poly_status)
        self.polys=copy.deepcopy(polys)
        self.WIDTH=width
        self.LENGTH=length
        self.DISTANCE=400
        self.main()
        
    def main(self):
        # initialize all parameters; target parameters are z,x1,y1,x2,y... etc.
        N=len(self.polys)
        if self._type=="separation":
            a,b,c=[[0]*(2*N+N*N) for _ in range(8*N+N*N)],[0 for _ in range(8*N+N*N)],[0 for _ in range(N*2+N*N)]
        else:
            # For compaction there are 2N+1 variables for z and xi/yi, and constraints for borders and pairwise separations
            a,b,c=[[0]*(2*N+1) for _ in range(9*N+N*N)],[0 for _ in range(9*N+N*N)],[0 for _ in range(N*2+1)]
        
        # get constants and pairwise edges
        self.getConstants()
        self.getTargetEdges()
        
        # constraints: limit total displacement OK
        for i in range(N):
            row=i*4
            a[row+0][i*2+0],b[row+0]=-1,-self.DISTANCE-self.Xi[i] # -xi >= -DISTANCE - Xi
            a[row+1][i*2+1],b[row+1]=-1,-self.DISTANCE-self.Yi[i] # -yi >= -DISTANCE - Yi
            a[row+2][i*2+0],b[row+2]= 1,-self.DISTANCE+self.Xi[i] # xi >= -DISTANCE + Xi
            a[row+3][i*2+1],b[row+3]= 1,-self.DISTANCE+self.Yi[i] # yi >= -DISTANCE + Yi
        
        # constraints: cannot move outside borders OK
        for i in range(N):
            row=4*N+i*4
            a[row+0][i*2+0],b[row+0]= 1,self.W_[i] # xi >= W_*
            a[row+1][i*2+1],b[row+1]= 1,self.H[i]  # yi >= Hi
            a[row+2][i*2+0],b[row+2]=-1,self.W[i]-self.LENGTH  # -xi >= Wi-Length
            a[row+3][i*2+1],b[row+3]=-1,-self.WIDTH  # -yi >= -Width

        # constraints: avoid overlaps (some known issues)
        for i in range(N):
            for j in range(N):
                row=8*N+i*N+j
                if self._type=="separation":
                    if i!=j:
                        a[row][i*2+0],a[row][i*2+1],a[row][j*2+0],a[row][j*2+1],b[row]=self.getOverlapConstrain(i,j)
                        a[row][2*N+i*N+j],c[2*N+i*N+j]=1,1 # objective variable
                    else:
                        a[row][2*N+i*N+j],c[2*N+i*N+j],b[row]=1,1,0
                else:
                    if i!=j:
                        a[row][i*2+0],a[row][i*2+1],a[row][j*2+0],a[row][j*2+1],b[row]=self.getOverlapConstrain(i,j)
        
        if self._type=="compaction":
            # z - xi >= w for all polygons OK
            for i in range(N):
                row=8*N+N*N+i
                a[row][2*N],a[row][i*2],b[row]=1,-1,self.W[i]
            c[2*N]=1

        # solve LP
        result,self.final_value=sovleLP(a,b,c,_type=self._type)

        # convert variables to coordinates; variable ordering is [a00,..,ann,x1,..,xn,y1,..,yn]
        placement_points=[]
        if self._type=="separation":
            for i in range(N*N,N*N+N):
                placement_points.append([result[i],result[i+N]])
        else:
            for i in range(len(result)//2):
                placement_points.append([result[i],result[i+N]])
        
        # get final placement
        self.getResult(placement_points)
    
    # update final placements and statuses
    def getResult(self,placement_points):
        self.final_polys,self.final_poly_status=[],copy.deepcopy(self.poly_status)
        for i,poly in enumerate(self.polys):
            self.final_polys.append(GeoFunc.getSlide(poly,placement_points[i][0]-self.Xi[i],placement_points[i][1]-self.Yi[i]))
            self.final_poly_status[i][1]=[placement_points[i][0],placement_points[i][1]]

    def getOverlapConstrain(self,i,j):
        # initialize parameters
        a_xi,a_yi,a_xj,a_yj,b=0,0,0,0,0
        
        # get reference point coordinates for stationary polygon
        Xi,Yi=self.Xi[i],self.Yi[i] 

        # get target edge
        edge=self.target_edges[i][j] 
        X1,Y1,X2,Y2=edge[0][0],edge[0][1],edge[1][0],edge[1][1]

        '''
        Non-overlap conditions
        Formula1: (y2-y1)*xj+(x1-x2)*yj+x2*y1-x1*y2>0  (right distance > 0)
        Formula2: (Y2-Y1)*xj+(X1-X2)*yj+X2*Y1-X1*Y2+(xi-Xi)*(Y1-Y2)+(yi-Yi)*(X2-X1)+>0
        Formula3: (Y2-Y1)*xj+(X1-X2)*yj+X2*Y1-X1*Y2+(Y1-Y2)*xi+(X2-X1)*yi-Xi*(Y1-Y2)-Yi*(X2-X1)>0
        Formula4: (Y1-Y2)*xi+(X2-X1)*yi+(Y2-Y1)*xj+(X1-X2)*yj>-X2*Y1+X1*Y2+Xi*(Y1-Y2)+Yi*(X2-X1)
        For overlaps we add a_ij to relax constraints. Parameter a_ij is binary in the original formulation.
        '''
        a_xi,a_yi,a_xj,a_yj,b=Y1-Y2,X2-X1,Y2-Y1,X1-X2,-X2*Y1+X1*Y2+Xi*(Y1-Y2)+Yi*(X2-X1)
        
        return a_xi,a_yi,a_xj,a_yj,b
    
    # get all constants and limits
    def getConstants(self):
        self.W=[] # max distance to the right placement
        self.W_=[] # max distance to the left placement
        self.H=[] # height extent
        self.Xi=[] # initial Xi position
        self.Yi=[] # initial Yi position
        self.PLACEMENTPOINT=[]
        for i,poly in enumerate(self.polys):
            left,bottom,right,top=LPAssistant.getBoundPoint(poly)
            self.PLACEMENTPOINT.append([top[0],top[1]])
            self.Xi.append(top[0])
            self.Yi.append(top[1])
            self.W.append(right[0]-top[0])
            self.W_.append(top[0]-left[0])
            self.H.append(top[1]-bottom[1])

    # get pairwise target edges
    def getTargetEdges(self):
        self.target_edges=[[0]*len(self.polys) for _ in range(len(self.polys))]
        for i in range(len(self.polys)):
            for j in range(len(self.polys)):
                if i==j:
                    continue
                nfp=self.getNFP(i,j)
                nfp_edges=GeoFunc.getPolyEdges(nfp)
                point=self.PLACEMENTPOINT[j]
                if Polygon(nfp).contains(Point(point)) and self._type=="separation":
                    # if contains and we are separating, pick the closest edge (left)
                    min_distance=99999999999999
                    for edge in nfp_edges:
                        left_distance=-self.getRightDistance(edge,point)
                        if left_distance<=min_distance:
                            min_distance=left_distance
                            self.target_edges[i][j]=copy.deepcopy(edge)
                else:
                    # otherwise (compaction) pick the farthest edge (right)
                    max_distance=-0.00001
                    for edge in nfp_edges:
                        right_distance=self.getRightDistance(edge,point)
                        if right_distance>=max_distance:
                            max_distance=right_distance
                            self.target_edges[i][j]=copy.deepcopy(edge)

    @staticmethod
    def getRightDistance(edge,point):
        A=edge[1][1]-edge[0][1]
        B=edge[0][0]-edge[1][0]
        C=edge[1][0]*edge[0][1]-edge[0][0]*edge[1][1]
        D=A*point[0]+B*point[1]+C
        dis=(math.fabs(A*point[0]+B*point[1]+C))/(math.pow(A*A+B*B,0.5))
        if D>0:
            return dis # positive for right side
        elif D==0:
            return 0 # on the line
        else:
            return -dis # negative for left side

    def getNFP(self,j,i):
        # j is stationary polygon index, i is moving polygon index
        row=j*192+i*16+self.poly_status[j][2]*4+self.poly_status[i][2]
        bottom_pt=LPAssistant.getBottomPoint(self.polys[j])
        delta_x,delta_y=bottom_pt[0],bottom_pt[1]
        nfp=GeoFunc.getSlide(json.loads(self.all_nfp["nfp"][row]),delta_x,delta_y)
        return nfp


def searchForBest(polys,poly_status,width,length):
    # record best result
    best_poly_status,best_polys=[],[]
    cur_length=length

    # iterate to search for feasible placement (polys need not change)
    while True:
        print("Allowed height:",cur_length)
        result_polys,result_poly_status,result_value=searchOneLength(polys,poly_status,width,cur_length,"separation")
        if result_value==0:
            best_polys=result_polys
            break
        cur_length=cur_length+4
    
    print("Begin exact search")
    # refine search around the found solution
    for i in range(3):
        cur_length=cur_length-1
        print("Allowed height:",cur_length)
        result_polys,result_poly_status,result_value=searchOneLength(polys,poly_status,width,cur_length,"separation")
        if result_value!=0:
            break
        best_polys=result_polys

    best_length=cur_length+1
    print("Final separation height:",best_length)

    # run compaction to update poly_status (only needed at the end)
    best_polys,best_poly_status,best_length=searchOneLength(best_polys,poly_status,width,best_length,"compaction")

    print("Final height:",best_length)
    return best_polys,poly_status,best_length


def searchOneLength(polys,poly_status,width,length,_type):
    '''
    Search whether a given height is feasible without changing order.
    Separation: test if a given height can reach zero overlap; return final polys, status, final overlap
    Compaction: test compaction at a given height; return final polys, status, computed height
    '''
    input_polys=copy.deepcopy(polys) # input polygons each iteration
    last_value=99999999999
    final_polys,final_poly_status=[],[]
    while True:
        res=LPFunction(input_polys,poly_status,width,length,_type)
        # if no overlap or converged
        if res.final_value==0 or abs(res.final_value-last_value)<0.001:
            last_value=res.final_value
            final_polys=copy.deepcopy(res.final_polys)
            final_poly_status=copy.deepcopy(res.final_poly_status)
            break
        # if changed, update status and retry
        input_polys=copy.deepcopy(res.final_polys)
        last_value=res.final_value
    return final_polys,final_poly_status,last_value

if __name__ == "__main__":
    blf = pd.read_csv("record/blf.csv")
    index = 7
    polys,poly_status,width=json.loads(blf["polys"][index]),json.loads(blf["poly_status"][index]),int(blf["width"][index])

    searchForBest(polys,poly_status,width,628.1533587455999)
