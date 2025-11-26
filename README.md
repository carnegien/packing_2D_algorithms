# 2D-Irregular-Packing-Algorithm

**This repository contains algorithms for 2D irregular packing and a simple tutorial to the algorithms. If you discover any issues with the code, you are welcome to fork the repository and initiate pull requests.**

## Introduction

Literature review: "A survey of nesting problems" (Chinese) https://seanys.github.io/2020/03/17/

Author: Shan Yang (https://github.com/seanys), Zilu Wang (https://github.com/Prinway) (Department of Science and Management, Tongji University)

Email: tjyangshan@gmail.com, prinway1226@gmail.com

Yang works in Dr. Xiaolei Wang's laboratory on optimization problems in urban transportation. Wang works in Dr. Zhaolin Hu's group.

## Dataset

EURO Dataset: https://www.euro-online.org/websites/esicup/data-sets/#1535972088237-bbcb74e3-b507

Data sets have been processed to csv in folder [data](data).

```python
import pandas as pd
import json
df = pd.read_csv("data/blaz1.csv")
all_polys = []
for i in range(df.shape[0]):
  all_polys.append(df['polygon'][i])
print(all_polys)
```

## Algorithms

- Bottom-Left-Fill.py: A 2-exchange heuristic for nesting problems (2002)
- genetic_algorithm.py: A 2-exchange heuristic for nesting problems (2002)
- nfp_test.py: Complete and robust no-fit polygon generation for the irregular stock cutting problem.
- Cuckoo_search.py: A guided cuckoo search and pairwise clustering approach for sheet nesting
- Fast_neighbor_search.py: Fast neighborhood search for two- and three-dimensional nesting problems (2004)
- simulating_annealing.py: Simulated annealing + Bottom Left Fill
- lp_algorithm.py: Solving Irregular Strip Packing problems by hybridising simulated annealing and linear programming (2006)
- lp_search.py: A new algorithm proposed by us. See https://github.com/seanys/Use-Modified-Penetration-Depth-and-Guided-Search-to-Solve-Nesting-Problem.
- C++ Nesting Problem: C++ Version

Most of them work. A very small overlap is allowed in lp_search to avoid endless search.

## Tutorial

Editing....

## Implementation status

### Core methods

- [x] No-fit Polygon: basic implementation. Start point portion is not fully implemented; see Burke E K, Hellier R S R, Kendall G, et al. "Complete and Robust No-Fit Polygon Generation for the Irregular Stock Cutting Problem" for reference.

### Sequencing / placement methods

- [x] Bottom Left Fill: implemented (see reference papers)
  a. Select a polygon to insert, compute the inner fit polygon (area where the polygon can be placed without crossing the bin boundary). The reference point P will form a rectangle in the inner fit region; if P is inside the rectangle then the placement is feasible.
  b. Select the leftmost feasible placement that can be folded (source image: https://github.com/Jack000/SVGnest)

- [x] TOPOS: implemented (see references)
- [x] GA/SA: both global optimization orders implemented

### Layout-based optimization

- [x] Fast Neighborhood Search: basic implementation; some bugs still need fixing
- [x] Cuckoo Search: basic implementation; needs further improvements
- [x] ~~ILSQN: not prepared, not significant~~
- [x] ~~Guided Local Search: same as above~~

### Linear programming based packing

- [x] Compaction: implemented (shrink borders)
- [x] Separation: implemented (remove overlaps)
- [ ] SHAH: Hybrid algorithm based on simulated annealing and the two algorithms above; not yet implemented

## Reference papers

(References list omitted here)