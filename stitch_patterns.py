from typing import Union, Optional, Tuple, List, Dict
from abc import ABC, abstractmethod
from copy import deepcopy
import warnings

import numpy as np
from multimethod import multimethod

# if __name__ == "__main__":
#     from helpers import c2cs, tuckPattern
#     from knitout_helpers import getBedNeedle, rackedXfer
# else:
#     from .helpers import c2cs, tuckPattern
#     from .knitout_helpers import getBedNeedle, rackedXfer


import sys
from pathlib import Path

## Standalone boilerplate before relative imports
if not __package__: #remove #?
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name


from .helpers import c2cs, tuckPattern
from .knitout_helpers import getBedNeedle, rackedXfer


KNIT = 1
TUCK = 2
MISS = 3


class StitchPattern(ABC):
    def __init__(self, k, left_n: int, right_n: int, c: Union[str, Tuple[str], List[str]], home_bed: Optional[str], gauge: int=1, avoid_bns={"f": [], "b": []}, init_direction: str="-", xfer_back_after: bool=False, inhook: bool=False, *args, **kwargs):
        rack_value_op = getattr(k, "rack_value", None)
        print(type(k)) #remove #debug
        assert rack_value_op is not None, "'k' must come from the 'knitlib_knitout' module" #debug
        #
        self.k = k
        self.left_n = left_n
        self.right_n = right_n
        self.cs = c2cs(c)
        self.home_bed = home_bed #TODO: deal with if no home bed
        self.gauge = gauge
        self.avoid_bns = avoid_bns
        self.direction = init_direction
        #
        self.xfer_back_after = xfer_back_after
        self.inhook = inhook
        self.tuck_pat_args = None
        #
        # self.avoid_bns = {"f": [], "b": []}
        #
        self.n_passes = 0
        #
        # self.bn_locs = {"f": [], "b": [], "fs": [], "bs": []}
        self.xbns = {"f": [], "b": []} #new
        self.knit_anyway = {"f": [], "b": []} #new
        #
        self.speedNumber = None
        self.stitchNumber = None
        self.xfer_speedNumber = None
        self.xfer_stitchNumber = None
        #
        self.beds = np.array(["b", "f"])
        self.ops = {
            # 0: self.k.miss,
            1: self.k.knit,
            2: self.k.tuck,
            3: self.k.miss
        }
        #
        self.sequence = self.initSequence(*args, **kwargs)
        assert len(self.sequence.shape) == 3, "sequence must be a 3D array"
        self.exclude_edge_ns = False #when to exclude the edge-most needles from xfer_sequence
        self.xfer_sequence = self.initXferSequence(*args, **kwargs)
        # assert len(self.xfer_sequence.shape) == 3, f"xfer_sequence must be a 3D array (got shape: {self.xfer_sequence.shape})" #go back! #?
        # assert self.xfer_sequence.dtype == "<U1", "xfer_sequence must be an array of bed-needle strings indicating which bn to transfer to in the sequence"

    @abstractmethod
    def initSequence(self, *args, **kwargs) -> np.ndarray: #TODO: ensure sequence is 3D
        pass

    # @abstractmethod #optional
    def initXferSequence(self, *args, **kwargs) -> np.ndarray: #TODO: ensure sequence is 3D
        # 
        return np.empty((1,1,0), dtype=str) #TODO: deal with all of this

    def getMinNeedle(self, bed=None) -> Union[int,float]:
        m = self.n_passes % self.sequence.shape[0] #check
        row = self.sequence[m]
        #
        if bed is not None:
            bed_idx = np.where(self.beds == bed[0])[0]
            for n in range(self.left_n, self.right_n+1):
                ops = row[n//self.gauge % len(row)]
                if self.gaugeValid(n) and (ops[bed_idx] != 0 or n in self.knit_anyway[bed[0]]): return n
            # return min(self.k.bn_locs[bed], default=float("inf"))
        else:
            for n in range(self.left_n, self.right_n+1):
                ops = row[n//self.gauge % len(row)]
                if self.gaugeValid(n) and (len(np.where(ops)[0]) != 0 or n in self.knit_anyway["b"] or n in self.knit_anyway["f"]): return n
            # return min(min(self.k.bn_locs[b], default=float("inf")) for b in self.k.bn_locs.keys())
        #
        return float("inf") #if no needle that matches

    def getMaxNeedle(self, bed=None) -> Union[int,float]:
        m = self.n_passes % self.sequence.shape[0] #check
        row = self.sequence[m]
        #
        if bed is not None:
            bed_idx = np.where(self.beds == bed[0])[0]
            for n in range(self.right_n, self.left_n-1, -1):
                ops = row[n//self.gauge % len(row)]
                if self.gaugeValid(n) and (ops[bed_idx] != 0 or n in self.knit_anyway[bed[0]]): return n
            # return max(self.k.bn_locs[bed], default=float("-inf"))
        else:
            for n in range(self.right_n, self.left_n-1, -1):
                ops = row[n//self.gauge % len(row)]
                if self.gaugeValid(n) and (len(np.where(ops)[0]) != 0 or n in self.knit_anyway["b"] or n in self.knit_anyway["f"]): return n
            # return max(max(self.k.bn_locs[b], default=float("-inf")) for b in self.k.bn_locs.keys())
        #
        return float("-inf") #if no needle that matches

    def ensureEmpty(self, bed, needle, n_range) -> bool: #returns whether it was empty (or in avoid_bns) to start with
        row = self.sequence[self.n_passes % self.sequence.shape[0]]
        #
        # if needle in self.k.bn_locs[bed] and needle not in self.avoid_bns.get(bed[0], []): #*
        if (bed,needle) in self.k.bns and needle not in self.avoid_bns.get(bed[0], []): #new #check
            bed_idx = np.where(self.beds == bed)[0]
            bed2_idx = bed_idx-1
            bed2 = self.beds[bed2_idx][0]
            # b, b2 = self.beds[bed_idx][0], self.beds[bed_idx-1][0]
            #
            done = False
            # for n in n_range[n_range.index(needle)+1:]:
            for n in n_range[n_range.index(needle):]:
                if self.gaugeValid(n):
                    ops = row[n//self.gauge % len(row)]
                    #
                    if ops[bed2_idx] != 0 and n not in self.avoid_bns.get(bed2, []):
                        self.rackedXfer(bed, needle, bed2, n)
                        done = True
                        break
                    elif ops[bed_idx] != 0 and n not in self.avoid_bns.get(bed, []):
                        self.rackedXfer(bed, needle, bed, n)
                        done = True
                        break

                    # if ops[bed_idx] != 0 and n not in self.avoid_bns.get(b, []):
                    #     self.rackedXfer(b, needle, f"{b2}s", n)
                    #     # self.rackedXfer(b, needle, f"{b2}s", n)
                    #     # self.rackedXfer(f"{b2}s", n, b, n)
                    #     done = True
                    #     break
                    # elif ops_[bed_idx-1] != 0 and n not in self.avoid_bns.get(b2, []):
                    #     self.rackedXfer((b, n), (b2, n_))
                    #     done = True
                    #     break
            #
            if not done: self.knit_anyway[bed].append(needle) #new #check
            return False
        else: return True

    # def ensurePopulated(self, bed, needle, n_range) -> bool: #returns whether it was empty (or in avoid_bns) to start with
    #     if needle not in self.k.bn_locs[bed] and needle not in self.avoid_bns.get(bed[0], []):
    #         row = self.sequence[self.n_passes % self.sequence.shape[0]]
    #         #
    #         bed_idx = np.where(self.beds == bed)[0]
    #         bed2_idx = bed_idx-1
    #         bed2 = self.beds[bed2_idx][0]
    #         # b, b2 = self.beds[bed_idx][0], self.beds[bed_idx-1][0]
    #         #
    #         done = False
    #         # for n in n_range[n_range.index(needle)+1:]:
    #         for n in n_range[n_range.index(needle):]:
    #             if self.gaugeValid(n):
    #                 ops = row[n//self.gauge % len(row)]
    #                 #
    #                 if ops[bed2_idx] != 0 and n not in self.avoid_bns.get(bed2, []):
    #                     self.rackedXfer(bed, needle, bed2, n)
    #                     done = True
    #                     break
    #                 elif ops[bed_idx] != 0 and n not in self.avoid_bns.get(bed, []):
    #                     self.rackedXfer(bed, needle, bed, n)
    #                     done = True
    #                     break

    #                 # if ops[bed_idx] != 0 and n not in self.avoid_bns.get(b, []):
    #                 #     self.rackedXfer(b, needle, f"{b2}s", n)
    #                 #     # self.rackedXfer(b, needle, f"{b2}s", n)
    #                 #     # self.rackedXfer(f"{b2}s", n, b, n)
    #                 #     done = True
    #                 #     break
    #                 # elif ops_[bed_idx-1] != 0 and n not in self.avoid_bns.get(b2, []):
    #                 #     self.rackedXfer((b, n), (b2, n_))
    #                 #     done = True
    #                 #     break
    #         #
    #         if not done: self.knit_anyway[bed].append(needle) #new #check
    #         return False
    #     else: return True

    @classmethod
    def getXferSeqBn(self, needle_idx: int, needle: int, to_bn: str):
        (to_bed, needle2_idx) = getBedNeedle(to_bn)
        #
        # n = needle//self.gauge % len(xrow)
        #
        diff = needle2_idx-needle_idx
        to_needle = needle+diff #check
        return to_bed, to_needle

    def setup(self, p, n_range):
        self.knit_anyway = {"f": [], "b": []} #reset
        #
        row = self.sequence[self.n_passes % self.sequence.shape[0]]
        #
        xrow = self.xfer_sequence[self.n_passes % self.xfer_sequence.shape[0]] #new #check

        for n in n_range:
            if self.gaugeValid(n):
                if xrow.size and (not self.exclude_edge_ns or (n != self.left_n and n != self.right_n)):
                    xn_idx = n//self.gauge % len(xrow)
                    xops = xrow[xn_idx]
                    #
                    for bed, to_bn in zip(self.beds, xops):
                        if len(to_bn) and n not in self.avoid_bns.get(bed, []):
                            (to_bed, to_needle) = self.getXferSeqBn(xn_idx, n, str(to_bn)) #check
                            #
                            if to_needle not in self.avoid_bns.get(to_bed, []) and self.left_n <= to_needle <= self.right_n:
                                self.rackedXfer(bed, n, to_bed, to_needle)
                                if p == 0 and self.xfer_back_after: self.xbns[bed].append(n)
                #
                ops = row[n//self.gauge % len(row)]
                #
                for bed, op in zip(self.beds, ops):
                    if n not in self.avoid_bns.get(bed, []):
                        if op == 0:
                            # if self.exclude_edge_ns and (n == self.left_n or n == self.right_n) and n in self.k.bn_locs[bed]: #*
                            if self.exclude_edge_ns and (n == self.left_n or n == self.right_n) and (bed,n) in self.k.bns: #new #check
                                self.knit_anyway[bed].append(n)
                            else:
                                was_empty = self.ensureEmpty(bed, n, n_range)
                                if p == 0 and not was_empty and self.xfer_back_after: self.xbns[bed].append(n)
                            # elif n not in self.k.bn_locs[bed]: self.ensurePopulated(bed, n)
            """
            # ops, x = np.divmod(ops, 1) #go back! #?
            idxs = np.where(ops)[0]
            #
            if self.gaugeValid(n):
                if len(idxs) == 1:
                    idx = idxs[0]
                    b, b2 = self.beds[idx], self.beds[idx-1]
                    # op = ops[idx]
                    #
                    if n not in self.avoid_bns.get(b, []) and n not in self.bn_locs[b] and n in self.bn_locs[b2]:
                        self.rackedXfer(b2, n, b, n)
                        # self.bn_locs[b2].remove(n)
                        # self.bn_locs[b].append(n) #don't actually need this because will be taken care of #*
                        #
                        if p == 0 and self.xfer_back_after: self.xbns[b2].append(n)
                    # if x[idx]: #indicates transfer to

                    # #
                    # if op == KNIT:
                    #     if n not in self.avoid_bns[b] and n in self.bn_locs[b2] and n not in self.bn_locs[b]:
                    #         self.rackedXfer((b2, n), (b, n))
                    #         # self.bn_locs[b2].remove(n)
                    #         # self.bn_locs[b].append(n) #don't actually need this because will be taken care of
                    #         #
                    #         if p == 0 and self.xfer_back_after: self.xbns[b2].append(n)
                    # elif op == MISS: # miss past NON empty needle
                    #     if n in self.bn_locs[b2]: # need to transfer it away to get it empty
                    #         if n not in self.bn_locs[b]:
                    #             self.rackedXfer((b2, n), (b, n))
                    #             #
                    #             if p == 0 and self.xfer_back_after: self.xbns[b2].append(n)
                elif len(idxs) == 0:
                    self.ensureEmpty("f", n)
                    self.ensureEmpty("b", n)
                    #
                    # if n not in self.avoid_bns.get(self.home_bed, []) and n in self.bn_locs[self.home_bed]:
                    #     bed_idx = np.where(self.beds == self.home_bed)[0]
                    #     b, b2 = self.beds[bed_idx][0], self.beds[bed_idx-1][0]
                    #     #
                    #     for n_ in n_range[n_range.index(n)+1:]:
                    #         if self.gaugeValid(n_):
                    #             done = False
                    #             #
                    #             ops_ = row[n_//self.gauge % len(row)]
                    #             if ops_[bed_idx] != 0 and n_ not in self.avoid_bns.get(b, []):
                    #                 self.rackedXfer((b, n), (f"{b2}s", n_))
                    #                 self.rackedXfer((f"{b2}s", n_), (b, n_))
                    #                 done = True
                    #                 break
                    #             elif ops_[bed_idx-1] != 0 and n not in self.avoid_bns.get(b2, []):
                    #                 self.rackedXfer((b, n), (b2, n_))
                    #                 done = True
                    #                 break
                    #             #
                    #             if not done: self.knit_anyway[b].append(n) #new #check
                    #
                else:
                    if n not in self.avoid_bns.get("b", []) and n not in self.avoid_bns.get("f", []) and (n not in self.bn_locs["f"] or n not in self.bn_locs["b"]): raise AssertionError("TODO: handle this")


                # if n not in self.avoid_bns["b"]:
                #     if ops[0] == 0:
                #         if n in self.bn_locs["b"]: print("TODO: xfer to other valid location")
                #     elif ops[1] < 3: # knit or tuck
                #         if n not in self.bn_locs["b"] and n in self.bn_locs["f"] and ops[1] == 0:
                #             self.rackedXfer(("f", n), ("b", n))
                #             # self.bn_locs["f"].remove(n)
                #             # self.bn_locs["b"].append(n) #don't actually need this because will be taken care of
                #             #
                #             if self.xfer_back_after: self.xbns["f"].append(n)
            """


    def doPass(self, n_range): #TODO: think of a better name for this #?
        m = self.n_passes % self.sequence.shape[0] #check
        row = np.copy(self.sequence[m])
        #
        last_ns = n_range[-self.gauge:-1]
        #
        for n in n_range:
            if self.gaugeValid(n):
                ops = np.copy(row[n//self.gauge % len(row)])
                # if n in last_ns and any(ops[i] == 0 and n in self.bn_locs[self.beds[i]] for i in range(2)):
                if n in self.knit_anyway["b"]: ops[0] = KNIT
                if n in self.knit_anyway["f"]: ops[1] = KNIT

                idxs = np.where((ops != 0) & (ops < 3))[0]
                #
                if len(idxs) == 2:
                    # if self.k.rack_value == 0: self.k.rack(0.25)
                    self.k.rack(0.25)
                    if self.direction == "+": idxs = idxs[::-1] #start with f 
                    #
                    for idx in idxs:
                        # if ops[idx] == MISS: continue
                        if n in last_ns and ops[idx] == TUCK:
                            warnings.warn("skipping tuck on edge needle") #check
                            continue
                        b = self.beds[idx]
                        self.ops[ops[idx]](self.direction, f"{b}{n}", *self.cs)
                        # if n not in self.bn_locs[b]: self.bn_locs[b].append(n) #go back! #?
                elif len(idxs) == 1:
                    idx = idxs[0]
                    b = self.beds[idx]
                    self.ops[ops[idx]](self.direction, f"{b}{n}", *self.cs)
                    # if n not in self.bn_locs[b]: self.bn_locs[b].append(n) #go back! #?
                else: self.k.miss(self.direction, f"f{n}", *self.cs) #TODO: disallow tucks on the edges (miss instead #?)
            elif n == n_range[-1]: self.k.miss(self.direction, f"f{n}", *self.cs) #miss last needle

    # def postPassUpdate(self, pass_idx: int, n_range, *args, **kwargs): #remove #?
    #     m1 = (self.n_passes+1) % self.sequence.shape[0] #check
    #     row = self.sequence[m1-1] #so it can be -1, which is fine
    #     next_row = self.sequence[m1]
    #     pass

    def generate(self, passes: int, start_n: Optional[int]=None, end_n: Optional[int]=None):
        if self.speedNumber is not None: self.k.speedNumber(self.speedNumber)
        if self.stitchNumber is not None: self.k.stitchNumber(self.stitchNumber)
        # left_n, right_n = self.left_n, self.right_n #for now
        #
        if start_n is None: #defaults
            if self.direction == "+": start_n = self.left_n
            else: start_n = self.right_n
        
        if end_n is None: #defaults
            if self.direction == "+": end_n = self.right_n
            else: end_n = self.left_n

        if end_n > start_n: # pass is pos
            self.direction = "+"
        elif start_n > end_n: # pass is neg
            self.direction = "-"

        if self.direction == "+":
            left_n, right_n = start_n, end_n
            n_range = range(start_n, end_n+1)
        else:
            left_n, right_n = end_n, start_n
            n_range = range(start_n, end_n-1, -1)
        #
        #update each time:
        self.left_n = min(self.left_n, left_n)
        self.right_n = max(self.right_n, right_n)
        # if left_n < self.left_n: self.left_n = left_n #remove
        # if right_n > self.right_n: self.right_n = right_n #remove

        if self.inhook:
            self.k.inhook(*self.cs)
            #
            self.tuck_pat_args = {"first_n": start_n, "direction": self.direction}
            tuckPattern(self.k, c=self.cs, **self.tuck_pat_args)

        # self.setup(n_range)
        #
        for p in range(passes):
            self.setup(p, n_range)
            self.doPass(n_range)
            # self.postPassUpdate(p, n_range, *args, **kwargs)
            #
            self.n_passes += 1
            self.toggleDirection()
            n_range = n_range[::-1] #reversed(n_range)
            #
            if self.tuck_pat_args is not None and self.n_passes > 1:
                self.k.releasehook(*self.cs)
                tuckPattern(self.k, c=None, **self.tuck_pat_args) # drop it
                self.tuck_pat_args = None
        #
        self.k.rack(0) #reset
        #
        if self.xfer_back_after: self.xferBack()

    #===========================================================================
    #--------------------------------- SETTERS: --------------------------------
    #===========================================================================
    #concrete method
    def setExtensions(self, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None):
        if speedNumber is not None: self.speedNumber = speedNumber
        if stitchNumber is not None: self.stitchNumber = stitchNumber
        if xfer_speedNumber is not None: self.xfer_speedNumber = xfer_speedNumber
        if xfer_stitchNumber is not None: self.xfer_stitchNumber = xfer_stitchNumber

    # #concrete method
    # def setAvoidBns(self, bns={"f": [], "b": []}) -> None: #TODO: think of a better name for this
    #     self.avoid_bns = deepcopy(bns) #?
    
    # #concrete method
    # def appendAvoidBns(self, bns={"f": [], "b": []}) -> None: #TODO: think of a better name for this
    #     for bed, needles in bns.keys():
    #         self.avoid_bns[bed].extend(deepcopy(needles)) #?

    #===========================================================================
    #--------------------------------- HELPERS: --------------------------------
    #===========================================================================
    def gaugeValid(self, n: int):
        return (self.home_bed == "f" and n % self.gauge == 0) or (self.home_bed == "b" and n % self.gauge == (self.gauge//2))
    
    # @classmethod
    # def bnValid(self, b: str, n: int):
    #     return n not in self.avoid_bns[b] and ((b == "f" and n % self.gauge == 0) or (b == "b" and n % self.gauge == (self.gauge//2)))

    @multimethod
    def rackedXfer(self, from_bed: str, from_needle: int, to_bed: str, to_needle: int, reset_rack: bool=True) -> None:
        rackedXfer(self, from_bed, from_needle, to_bed, to_needle, reset_rack)
    
    """
    def rackedXfer(self, from_bn: Tuple[str,int], to_bn: Tuple[str,int], reset_rack=True) -> None: #TODO: just use regular xfer instead #?
        from_bed, from_needle = from_bn
        to_bed, to_needle = to_bn
        #
        assert from_bed[0] != to_bed[0], "cannot xfer to/from the same bed"
        #
        r = 0
        if from_bed[0] == "f": r = from_needle-to_needle
        else: r = to_needle-from_needle
        #
        self.k.rack(r)
        self.k.xfer(from_bn, to_bn)
        if reset_rack: self.k.rack(0)
        #
        return r
    """
    
    @rackedXfer.register
    def rackedXfer(self, from_bn: Tuple[str, int], to_bn: Tuple[str, int], reset_rack=True) -> int:
        return self.rackedXfer(*from_bn, *to_bn, reset_rack)
    
    @rackedXfer.register
    def rackedXfer(self, from_bn: str, to_bn: str, reset_rack: bool=True):
        self.rackedXfer(*getBedNeedle(from_bn), *getBedNeedle(to_bn), reset_rack)

    def toggleDirection(self) -> None:
        if self.direction == "-": self.direction = "+"
        else: self.direction = "-"

    def xferBack(self):
        f_xbns = sorted(self.xbns["f"].copy()) #TODO: see if need to do deepcopy
        b_xbns = sorted(self.xbns["b"].copy())
        #
        for n in f_xbns:
            self.rackedXfer("b", n, "f", n, reset_rack=False)
            # self.bn_locs["b"].remove(n)
            # self.bn_locs["f"].append(n)
        #
        for n in b_xbns:
            self.rackedXfer("f", n, "b", n, reset_rack=False)
            # self.bn_locs["f"].remove(n)
            # self.bn_locs["b"].append(n)



#===============================================================================
class SeqHelpers:
    @classmethod
    def rowFlip(self, row: np.ndarray) -> np.ndarray:
        assert len(row.shape) == 2 and row.shape[1] == 2, "row must be a n x 2 array"
        return np.flip(row)

    @classmethod
    def bedFlip(self, row: np.ndarray) -> np.ndarray:
        assert len(row.shape) == 2 and row.shape[1] == 2, "row must be a n x 2 array"
        return np.flip(row, axis=1)
"""
KEY:
(rows x columns x 2) matrix -> (m x n x b), where m is the number of rows (vertical repeats), n is the number of needles in a horizontal repeat, and b is for back and front bed (first number is back bed op, second is front bed op)

OPS:
0: empty needle
1: knit
2: tuck
3: miss
TODO: xfer and split
"""
# # rib
# rib_fb = np.array([
#     [[0, 1], [1, 0]]
# ])


# rib_ffb = np.array([
#     [[0, 1], [0, 1], [1, 0]]
# ])

# # garter ffb
# garter_ffb = np.array([
#     [[0, 1]],
#     [[0, 1]],
#     [[1, 0]]
# ])

# # seed fb
# seed_fb = np.array([
#     [[0, 1], [1, 0]],
#     [[1, 0], [0, 1]]
# ])

# # seed ffb
# seed_fb = np.array([
#     [[0, 1], [0, 1], [1, 0]],
#     [[1, 0], [1, 0], [0, 1]]
# ])

class Rib1x1(StitchPattern): #for example purposes
    def initSequence(self) -> np.ndarray:
        return np.array([
            [[0, 1], [0, 1]]
        ])

#

class Jersey(StitchPattern):
    def initSequence(self) -> np.ndarray:
        if self.home_bed == "b": sequence = np.array([[[1, 0]]])
        else: sequence = np.array([[[0, 1]]])
        #
        print(sequence) #remove #debug
        return sequence



class Rib(StitchPattern):
    def initSequence(self, bed_seq: str="fb") -> np.ndarray:
        sequence = np.empty((1, len(bed_seq), 2))
        for i in range(len(bed_seq)):
            if bed_seq[i] == "f": sequence[0][i] = [0, 1] #TODO: #check
            else: sequence[0][i] = [1, 0]
        #
        print(sequence) #remove #debug
        return sequence


class Garter(StitchPattern):
    def initSequence(self, bed_seq: str="fb") -> np.ndarray:
        sequence = np.empty((len(bed_seq), 1, 2))
        for i in range(len(bed_seq)):
            if bed_seq[i] == "f": sequence[i][0] = [0, 1] #TODO: #check
            else: sequence[i][0] = [1, 0]
        #
        print(sequence) #remove #debug
        return sequence

        
class Seed(StitchPattern):
    def initSequence(self, bed_seq: str="fb") -> np.ndarray:
        sequence = np.empty((2, len(bed_seq), 2))
        for i in range(len(bed_seq)):
            if bed_seq[i] == "f": sequence[0][i] = [0, 1] #TODO: #check
            else: sequence[0][i] = [1, 0]
        #
        sequence[1] = SeqHelpers.bedFlip(sequence[0])
        #
        print(sequence) #remove #debug
        return sequence
    

class Lace(StitchPattern):
    def initSequence(self) -> np.ndarray:
        if self.home_bed == "b": sequence = np.array([[[1, 0]]])
        else: sequence = np.array([[[0, 1]]])
        return sequence
    
    def initXferSequence(self, seq: str="01") -> np.ndarray:
        #0 indicates xfer, 1 indicates no xfer (aka receive)
        assert seq[-1] != "0", "sequence shouldn't end with an xfer"
        self.exclude_edge_ns = True #TODO: make it secure_edge_ns instead #?
        #
        # bn of who to xfer to
        sequence = []
        for i in range(len(seq)):
            if seq[i] == "0":
                for j in range(i+1, len(seq)):
                    if seq[j] == "1":
                        sequence.append(f"{self.home_bed}{j}")
                        break
            else: sequence.append("")
        #
        if self.home_bed == "b": return np.array([
                np.empty((1,0)),
                np.array([[s, ""] for s in sequence])
        ], dtype=object)
        else: return np.array([
                # np.array([[]], dtype=str),
                np.empty((1,0)),
                np.array([["", s] for s in sequence]) #, dtype=str)
        ], dtype=object)
        # return super().initXferSequence(*args, **kwargs)
    

        # if self.home_bed == "b": seq = [1, 0]
        # else: seq = [0, 1]
        # return np.array([
        #     [seq, seq],
        #     [seq, [0,0]]
        # ])





# import knitout
import knitlib_knitout
k = knitlib_knitout.Writer("1 2 3 4 5 6 7 8 9 10")

# pat = Lace(k, left_n=0, right_n=10, c="3", home_bed="f", gauge=1, inhook=True) #, bed_seq="fb")

pat = Rib(k, left_n=0, right_n=10, c="3", home_bed="f", gauge=1, inhook=True) #, bed_seq="fb")

pat.generate(passes=10)

k.write("pat_test.k")