from __future__ import annotations #so we don't have to worry about situations that would require forward declarations
from multimethod import multimethod
from collections.abc import MutableMapping
import warnings
# from functools import singledispatchmethod
from typing import Union, Optional, Dict, Tuple, List, Callable
from enum import Enum
from os import path
from copy import deepcopy

"""
TODO:
- [x] isEndNeedle
- [x] getNeedleRange
- [x] knitPass
- [x] twistedStitch
- [x] updateCarriers
- [x] caston
- [x] twistNeedleRanges
- [x] DEC_FUNCS/INC_FUNCS
- [x] findNextValidNeedle
- [x] xfer
- [x] rack

- [x] twist_bns
- [x] avoid_bns
- [x] active_bns (remove this)
- [x] min_n/max_n (remove and replace with function to bed min/max)
- [x] carriers
- [x] rack_value


add something for knitPass at a rack (or a "rackedSort" function)
- [ ] add check for when needle is holding loop and hasn't been knitting for a while
- [ ] add check for when skip over a lot of needles
- [ ] implement basketTubes using this
- [ ] fmt warnings
"""

from knitlib import altTuckCaston, altTuckClosedCaston, altTuckOpenTubeCaston, zigzagCaston, sheetBindoff, closedTubeBindoff, openTubeBindoff, dropFinish
from .helpers import gauged, toggleDirection
from .stitchPatterns import jersey, interlock, rib, garter, seed
# from .helpers import multidispatchmethod

from .knitout_helpers import getBedNeedle, rackedXfer, HeldLoopWarning #, findNextValidNeedle
from .shaping import decEdge, decSchoolBus, decBindoff, incEdge, incSchoolBus, incCaston, incSplit


class StitchPattern(Enum):
    JERSEY = 0
    INTERLOCK = 1
    RIB = 2
    GARTER = 3
    SEED = 4
    #
    @classmethod
    def parse(self, val):
        if isinstance(val, self): return val
        elif isinstance(val, int): return self._value2member_map_[val]
        else: raise ValueError


class CastonMethod(Enum):
    ALT_TUCK_CLOSED = 0
    ALT_TUCK_OPEN = 1
    ZIGZAG = 2
    #TODO: add e-wrap/twisted stitch
    #
    @classmethod
    def parse(self, val):
        if isinstance(val, self): return val
        elif isinstance(val, int): return self._value2member_map_[val]
        else: raise ValueError


class BindoffMethod(Enum):
    CLOSED = 0
    OPEN = 1
    DROP = 2
    #
    @classmethod
    def parse(self, val):
        if isinstance(val, self): return val
        elif isinstance(val, int): return self._value2member_map_[val]
        else: raise ValueError


#TODO: have a rack limit
class DecreaseMethod(Enum):
    DEFAULT = 0
    EDGE = 1
    SCHOOL_BUS = 2
    BINDOFF = 3
    #
    @classmethod
    def parse(self, val):
        if isinstance(val, self): return val
        elif isinstance(val, int): return self._value2member_map_[val]
        else: raise ValueError


class IncreaseMethod(Enum):
    DEFAULT = 0
    EDGE = 1
    SCHOOL_BUS = 2
    CASTON = 3
    SPLIT = 4
    #
    @classmethod
    def parse(self, val):
        if isinstance(val, self): return val
        elif isinstance(val, int): return self._value2member_map_[val]
        else: raise ValueError


DEC_FUNCS = {
    DecreaseMethod.EDGE: decEdge,
    DecreaseMethod.SCHOOL_BUS: decSchoolBus,
    DecreaseMethod.BINDOFF: decBindoff
}


INC_FUNCS = {
    IncreaseMethod.EDGE: incEdge,
    IncreaseMethod.SCHOOL_BUS: incSchoolBus,
    IncreaseMethod.CASTON: incCaston,
    IncreaseMethod.SPLIT: incSplit
}


class KnitObject:
    def __init__(self, k, gauge=1, machine="swgn2"):
        rack_value_op = getattr(k, "rack_value", None)
        print(type(k)) #remove #debug
        assert rack_value_op is not None, "'k' must come from the 'knitlib_knitout' module" #debug
        #
        self.k = k
        self.gauge = gauge
        self.machine = machine
        #
        # self.min_n = {"f": float("inf"), "b": float("inf")}
        # self.max_n = {"f": float("-inf"), "b": float("-inf")}
        #
        self.active_carrier = None #TODO #*
        self.avoid_bns = {"f": [], "b": []} #, "fs": [], "bs": []}
        self.twist_bns = list()
        # self.st_cts = {} #?
        #
        self._row_ct = 0 #TODO
        #
        self.pat_args = {
            "k": None,
            "start_n": None,
            "end_n": None,
            "passes": 1,
            "c": None,
            "bed": None,
            "gauge": self.gauge, #will *not* be a reference (should be updated each time in case it changes)
            # "sequence": None,
            # "bn_locs"
            # "avoid_bns": {"f": [], "b": []}
        }

        # SETTINGS/CONSTANTS:
        self.MAX_RACK = 4

    def getMinNeedle(self, bed=None) -> Union[int,float]:
        try:
            return self.k.bns.min(bed).needle
        except AssertionError: #?
            return float("inf")

    def getMaxNeedle(self, bed=None) -> Union[int,float]:
        try:
            return self.k.bns.max(bed).needle
        except AssertionError:
            return float("-inf")

    @property
    def row_ct(self):
        return self._row_ct

    @row_ct.setter
    def row_ct(self, value: int):
        self.k.comment(f"row: {value}")
        self._row_ct = value

    def caston(self, method: Union[CastonMethod, int], bed: Optional[str], needle_range: Tuple[int, int], *cs: str) -> None:
        method = CastonMethod.parse(method) #check
        #
        not_in_cs = [c for c in cs if c not in self.k.carrier_map.keys()] #check
        if len(not_in_cs):
            self.k.inhook(*not_in_cs)
        #
        if method == CastonMethod.ALT_TUCK_CLOSED:
            if bed != "f" and bed != "b": altTuckClosedCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge)
            else: altTuckCaston(self.k, needle_range[0], needle_range[1], c=cs, bed=bed, gauge=self.gauge)
        elif method == CastonMethod.ALT_TUCK_OPEN:
            assert bed != "f" and bed != "b", "`CastonMethod.ALT_TUCK_OPEN` only valid for double bed knitting."
            altTuckOpenTubeCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge)
        elif method == CastonMethod.ZIGZAG:
            zigzagCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge)
            if needle_range[1] > needle_range[0]: xfer_range = range(needle_range[0], needle_range[1]+1)
            else: xfer_range = range(needle_range[0], needle_range[1]-1, -1)
            if bed == "f":
                for n in xfer_range:
                    self.rackedXfer("f", gauged("f", n//self.gauge, self.gauge), "b", gauged("b", n//self.gauge, self.gauge), reset_rack=False)
                self.k.rack(0)
            elif bed == "b":
                for n in xfer_range:
                    self.rackedXfer("b", gauged("b", n//self.gauge, self.gauge), "f", gauged("f", n//self.gauge, self.gauge), reset_rack=False)
                self.k.rack(0)
        else: raise ValueError("unsupported caston method")
        #
        if len(not_in_cs): self.k.releasehook(*not_in_cs)

    # def knitPass(self, cs: Union[str, Carrier, List[Carrier], CarrierSet, CarrierMap], bed: Optional[str], needle_range: Optional[Tuple[int,int]]=None, pattern: Union[StitchPattern, int, Callable]=StitchPattern.JERSEY, **kwargs) -> None:
    @multimethod
    def knitPass(self, pattern: Union[StitchPattern, int, Callable], bed: Optional[str], needle_range: Optional[Tuple[int,int]], *cs: str, **kwargs) -> None: #TODO: make sure still works with *cs before pattern
        if needle_range is None: needle_range = self.getNeedleRange(bed, *cs)
        #
        if needle_range[1] > needle_range[0]: d = "+"
        else: d = "-"

        func_args = deepcopy(self.pat_args) # pat_args

        func_args["k"] = self.k
        func_args["c"] = cs
        func_args["bed"] = bed
        func_args["gauge"] = self.gauge
        func_args["init_direction"] = d
        #
        func = None
        if isinstance(pattern, StitchPattern) or isinstance(pattern, int):
            pattern = StitchPattern.parse(pattern) #check
            #
            if pattern == StitchPattern.JERSEY:
                assert bed is not None, "'bed' is a required parameter for the 'jersey' function."
                func = jersey
            elif pattern == StitchPattern.INTERLOCK:
                if "sequence" in kwargs: assert kwargs["sequence"] == "01" or kwargs["sequence"] == "10", f"'{kwargs['sequence']}' is an invalid sequence value for the 'interlock' function (must be either '01' or '10')."
                func = interlock
            elif pattern == StitchPattern.RIB:
                if "sequence" in kwargs: assert all(char == "f" or char == "b" for char in kwargs["sequence"]), f"'{kwargs['sequence']}' is an invalid sequence value for the 'rib' function (must contain only 'f' and 'b' characters)."
                func = rib
            elif pattern == StitchPattern.GARTER:
                if "sequence" in kwargs: assert all(char == "f" or char == "b" for char in kwargs["sequence"]), f"'{kwargs['sequence']}' is an invalid sequence value for the 'garter' function (must contain only 'f' and 'b' characters)."
                func = garter
            elif pattern == StitchPattern.SEED:
                if "sequence" in kwargs: assert all(char == "f" or char == "b" for char in kwargs["sequence"]), f"'{kwargs['sequence']}' is an invalid sequence value for the 'seed' function (must contain only 'f' and 'b' characters)."
                func = seed
            else: raise ValueError("unsupported stitch pattern")
        else:
            assert callable(pattern)
            func = pattern
            #
            for key in func_args.keys():
                assert key in func.__code__.co_varnames, f"'{func.__name__}' function does not use required parameter, '{key}'."
        #
        for key, val in kwargs.items():
            if key in func.__code__.co_varnames: func_args[key] = val
            else: warnings.warn(f"kwarg '{key}' not a valid parameter for '{func.__name__}' function.")

        if "avoid_bns" in func.__code__.co_varnames:
            func_args["avoid_bns"] = deepcopy(self.avoid_bns)
        #
        needle_ranges, twisted_stitches = self.twistNeedleRanges(needle_range, bed)
        for n_range, twisted_stitch in zip(needle_ranges, twisted_stitches):
            func_args["start_n"] = n_range[0]
            func_args["end_n"] = n_range[1]
            #
            func(**func_args)
            #
            self.twistedStitch(d, twisted_stitch, *cs) #TODO: handle splits too

    @knitPass.register
    def knitPass(self, bed: Optional[str], *cs: str, **kwargs) -> None: #TODO: make sure still works with *cs before pattern
        self.knitPass(StitchPattern.JERSEY, bed, None, *cs, **kwargs)

    @knitPass.register
    def knitPass(self, pattern: Union[StitchPattern, int, Callable], bed: Optional[str], *cs: str, **kwargs) -> None: #TODO: make sure still works with *cs before pattern
        self.knitPass(pattern, bed, None, *cs, **kwargs)

    @knitPass.register
    def knitPass(self, bed: Optional[str], needle_range: Optional[Tuple[int,int]], *cs: str, **kwargs) -> None: #TODO: make sure still works with *cs before pattern
        self.knitPass(StitchPattern.JERSEY, bed, needle_range, *cs, **kwargs)
    
    @multimethod
    def bindoff(self, method: Union[BindoffMethod, int], bed: Optional[str], needle_range: Optional[Tuple[int, int]], *cs: str) -> None: #TODO
        method = BindoffMethod.parse(method) #check
        #
        if needle_range is None: needle_range = self.getNeedleRange(bed, *cs)
        #
        if method == BindoffMethod.CLOSED:
            if bed == "f" or bed == "b": sheetBindoff(self.k, needle_range[0], needle_range[1], cs, bed, self.gauge)
            else: closedTubeBindoff(self.k, needle_range[0], needle_range[1], cs, self.gauge)
        elif method == BindoffMethod.OPEN:
            assert bed != "f" and bed != "b", "`BindoffMethod.OPEN` only valid for double bed knitting."
            openTubeBindoff(self.k, needle_range[0], needle_range[1], cs, self.gauge)
        elif method == BindoffMethod.DROP:
            if bed == "b": front_needle_ranges = []
            else: front_needle_ranges = sorted(self.getNeedleRange("f", *cs))
            #
            if bed == "f": back_needle_ranges = []
            else: back_needle_ranges = sorted(self.getNeedleRange("b", *cs))
            #
            dropFinish(self.k, front_needle_ranges=front_needle_ranges, back_needle_ranges=back_needle_ranges)
            # if needle_range[1] > needle_range[0]: left_n, right_n = needle_range[0], needle_range[1]
            # else: left_n, right_n = needle_range[1], needle_range[0]
            # #
            # dropFinish(self.k, front_needle_ranges=([] if bed == "b" else [left_n,right_n]), back_needle_ranges=([] if bed == "f" else [left_n,right_n]))
        else: raise ValueError("unsupported bindoff method")
    
    @bindoff.register
    def bindoff(self, method: Union[BindoffMethod, int], bed: Optional[str], *cs: str) -> None: #TODO
        self.bindoff(method, bed, None, *cs)

    def isEndNeedle(self, direction: str, bed: str, needle: int) -> bool:
        if direction == "-": #
            min_n = self.getMinNeedle(bed[0])
            return (gauged(bed, needle//self.gauge, self.gauge) <= gauged(bed, min_n//self.gauge, self.gauge))
        elif direction == "+":
            max_n = self.getMaxNeedle(bed[0])
            return (gauged(bed, needle//self.gauge, self.gauge) >= gauged(bed, max_n//self.gauge, self.gauge))
        else: return False

    def setRowCount(self) -> None:
        ct = self.k.row_ct
        if ct > self.row_ct: self.row_ct = ct #check
        # cts = list(set(list(self.st_cts.values())))
        # if len(cts):
        #     ct = max(cts)
        #     if ct > self.row_ct:
        #         # res = dict(reversed(sorted(self.st_cts.items(), key=lambda item: (-int(item[0][1:]),item[0][0])))) #debug
        #         self.row_ct = ct

    # @multimethod
    def updateCarriers(self, direction: str, bed: str, needle: int, *cs: str) -> None:
        row_counted = direction is None
        #
        for c in cs:
            if not row_counted and self.k.carrier_map[c].direction != direction:
                self.setRowCount()
                row_counted = True
            self.k.carrier_map[c].update(direction, bed, needle)
    
    """
    @multimethod
    def getNeedleRange(self, bed: Optional[str], *cs: str) -> Tuple[int, int]:
        for c in cs:
            carrier = self.k.carrier_map[c]
            #
            if type(bed) == str and (bed[0] == "f" or bed[0] == "b"):
                other_bed = "b" if bed[0] == "f" else "f"
                if self.min_n[other_bed] < self.min_n[bed[0]] and self.min_n[bed[0]]-self.min_n[other_bed] < self.gauge: min_n = self.min_n[other_bed] #TODO: #check
                else: min_n = self.min_n[bed[0]]
                #
                if self.max_n[other_bed] > self.max_n[bed[0]] and self.max_n[other_bed]-self.max_n[bed[0]] < self.gauge: max_n = self.max_n[other_bed] #TODO: #check
                else: max_n = self.max_n[bed[0]]
            else: min_n, max_n = min(self.min_n["f"], self.min_n["b"]), max(self.max_n["f"], self.max_n["b"])
            #
            if self.isEndNeedle(carrier.direction, carrier.bed, carrier.needle):
                self.updateCarriers(c, toggleDirection(carrier.direction))
                if carrier.direction == "-":
                    if bed is not None and c.position.bed != bed and 0 < max_n-c.position.needle < self.gauge: self.k.miss("+", bed, max_n, c) #TODO: #check
                    return min(carrier.needle, max_n), min_n
                elif carrier.direction == "+":
                    if bed is not None and carrier.bed != bed and 0 < carrier.needle-min_n < self.gauge: self.k.miss("-", bed, min_n, c) #TODO: #check
                    return max(carrier.needle, min_n), max_n
                else: raise ValueError(f"cannot getNeedleRange for carrier '{c}' with no recorded direction.")
            else:
                if carrier.direction == "-": return min(carrier.needle-1, max_n), min_n
                elif carrier.direction == "+": return max(carrier.needle+1, min_n), max_n
                else: raise ValueError(f"cannot getNeedleRange for carrier '{c}' with no recorded direction.")

    @getNeedleRange.register
    """
    def getNeedleRange(self, bed: Optional[str], *cs: str) -> Tuple[int, int]:
        min_n = self.getMinNeedle()
        max_n = self.getMaxNeedle()
        #
        bed_min_n, bed_max_n = None, None
        # if type(bed) == str and (bed[0] == "f" or bed[0] == "b"):
        if bed is not None:
            bed_min_n = self.getMinNeedle(bed[0])
            if bed_min_n-min_n >= self.gauge: min_n = bed_min_n
            #
            bed_max_n = self.getMaxNeedle(bed[0])
            if max_n-bed_max_n >= self.gauge: max_n = bed_max_n
        #
        d = None
        # NOTE: if d is "-": we want min start_n
        start_n = None
        for c in cs:
            carrier = self.k.carrier_map[c]
            if self.isEndNeedle(carrier.direction, carrier.bed, carrier.needle):
                self.updateCarriers(toggleDirection(carrier.direction), None, None, c)
                if carrier.direction is not None:
                    d = carrier.direction
                    if d == "-" and (start_n is None or carrier.needle < start_n):
                        if bed is not None and carrier.bed != bed and 0 < bed_max_n-carrier.needle < self.gauge: self.k.miss("+", bed, bed_max_n, c) #TODO: #check
                        start_n = carrier.needle
                    elif d == "+" and (start_n is None or carrier.needle > start_n):
                        if bed is not None and carrier.bed != bed and 0 < carrier.needle-bed_min_n < self.gauge: self.k.miss("-", bed, bed_min_n, c) #TODO: #check
                        start_n = carrier.needle
            elif carrier.direction is not None:
                d = carrier.direction
                if d == "-" and (start_n is None or carrier.needle-1 < start_n): start_n = carrier.needle-1
                elif d == "+" and (start_n is None or carrier.needle+1 > start_n): start_n = carrier.needle+1
        #
        assert all([self.k.carrier_map[c].direction == d or self.k.carrier_map[c].direction is None for c in cs])
        #
        if d == "-":
            start_n = min(start_n, max_n)
            end_n = min_n
        elif d == "+":
            start_n = max(start_n, min_n)
            end_n = max_n
        else: raise ValueError(f"cannot getNeedleRange for carrier set with no recorded direction.")
        #
        return start_n, end_n

    def twistNeedleRanges(self, needle_range: Tuple[int, int], bed: Union[str, None]=None) -> Tuple[List[Tuple[int, int]], List[Union[None, str, List[str]]]]:
        n_ranges = []
        twisted_stitches = []
        if needle_range[1] > needle_range[0]:
            n0 = needle_range[0]
            for n in range(needle_range[0], needle_range[1]+1):
                done = False
                if bed != "b" and f"f{n}" in self.twist_bns:
                    twisted_stitches.append(f"f{n}")
                    done = True
                    n_ranges.append((n0, n-1))
                    n0 = n+1
                #
                if bed != "f" and f"b{n}" in self.twist_bns:
                    if done:
                        twisted_stitches[-1] = [twisted_stitches[-1], f"b{n}"]
                    else:
                        twisted_stitches.append(f"b{n}")
                        done = True
                        n_ranges.append((n0, n-1))
                        n0 = n+1
                #
                if not done and n == needle_range[1]:
                    n_ranges.append((n0, n))
                    twisted_stitches.append(None)
        else:
            n0 = needle_range[0]
            for n in range(needle_range[0], needle_range[1]-1, -1):
                done = False
                if bed != "b" and f"f{n}" in self.twist_bns:
                    twisted_stitches.append(f"f{n}")
                    done = True
                    n_ranges.append((n0, n+1))
                    n0 = n-1
                #
                if bed != "f" and f"b{n}" in self.twist_bns:
                    if done:
                        twisted_stitches[-1] = [twisted_stitches[-1], f"b{n}"]
                    else:
                        twisted_stitches.append(f"b{n}")
                        done = True
                        n_ranges.append((n0, n+1))
                        n0 = n-1
                #
                if not done and n == needle_range[1]:
                    n_ranges.append((n0, n))
                    twisted_stitches.append(None)
        #
        if not len(n_ranges):
            n_ranges.append(needle_range)
            twisted_stitches.append(None)
        #
        return n_ranges, twisted_stitches
    
    @multimethod
    def twistedStitch(self, d: str, bn: str, *cs: str) -> None:
        self.k.comment("begin twisted stitch")
        d2 = toggleDirection(d)
        #
        self.k.miss(d, bn, *cs)
        self.k.knit(d2, bn, *cs)
        self.k.miss(d, bn, *cs)
        self.k.comment("end twisted stitch")
        #
        bed, needle = getBedNeedle(bn) #TODO: move this to updateCarriers instead #?
        self.updateCarriers(d, bed, needle, *cs)
        # #
        # if bn not in self.st_cts: self.st_cts[bn] = 0 #means there is a loop there, but not a full stitch #remove
        # else: self.st_cts[bn] += 1
        #
        self.twist_bns.remove(bn) #TODO: decide what should go in twist_bns (str or tuple?)

    @twistedStitch.register
    def twistedStitch(self, d: str, bns: List[str], *cs: str) -> None:
        d2 = toggleDirection(d)
        for bn in bns:
            self.k.comment("begin twisted stitch")
            self.k.miss(d, bn, *cs)
            self.k.knit(d2, bn, *cs)
            self.k.miss(d, bn, *cs)
            self.k.comment("end twisted stitch")
            #
            # bed, needle = getBedNeedle(bn)
            # self.updateCarriers(d, bed, needle, *cs) #go back! #?
            #
            # if bn not in self.st_cts: self.st_cts[bn] = 0 #means there is a loop there, but not a full stitch #remove
            # else: self.st_cts[bn] += 1
            #
            self.twist_bns.remove(bn)

    @twistedStitch.register
    def twistedStitch(self, d: str, bn: None, *cs: str) -> None:
        return
        
    @multimethod
    def rackedXfer(self, from_bed: str, from_needle: int, to_bed: str, to_needle: int, reset_rack: bool=True):
        rackedXfer(self, from_bed, from_needle, to_bed, to_needle, reset_rack)
        #
        #remove #v
        # from_bn_key = f"{from_bed}{from_needle}"
        # to_bn_key = f"{to_bed}{to_needle}"
        # #
        # if from_bn_key in self.st_cts:
        #     if to_bn_key not in self.st_cts:
        #         self.st_cts[to_bn_key] = self.st_cts[from_bn_key]
        #     else: self.st_cts[to_bn_key] = max(self.st_cts[to_bn_key], self.st_cts[from_bn_key]) #TODO: #check
        #     #
        #     del self.st_cts[from_bn_key]
    
    @rackedXfer.register
    def rackedXfer(self, from_bn: Tuple[str,int], to_bn: Tuple[str,int], reset_rack: bool=True):
        self.rackedXfer(*from_bn, *to_bn, reset_rack)

    @rackedXfer.register
    def rackedXfer(self, from_bn: str, to_bn: str, reset_rack: bool=True):
        self.rackedXfer(*getBedNeedle(from_bn), *getBedNeedle(to_bn), reset_rack)

    def write(self, out_fn: str):
        if len(self.k.carrier_map.keys()):
            _carriers = list(self.k.carrier_map.keys())
            for c in _carriers:
                self.k.outhook(c)
        self.k.write(path.join(path.dirname(path.dirname( path.abspath(__file__))), f"knitout_files/{out_fn}.k"))
    
    @multimethod
    def decrease(self, method: Union[DecreaseMethod, int], from_bn: Tuple[str, int], to_bn: Tuple[str, int]):
        method = DecreaseMethod.parse(method) #check
        assert method != DecreaseMethod.DEFAULT, "TODO: deal with this"
        DEC_FUNCS[method](self, from_bn, to_bn)

    @decrease.register
    def decrease(self, method: Union[DecreaseMethod, int], from_bn: str, to_bn: str):
        self.decrease(method, getBedNeedle(from_bn), getBedNeedle(to_bn))
    
    @multimethod
    def decreaseLeft(self,  method: Union[DecreaseMethod, int], bed: str, count: int):
        method = DecreaseMethod.parse(method) #check
        min_n = self.getMinNeedle(bed[0])
        max_n = self.getMaxNeedle(bed[0])
        #
        if method == DecreaseMethod.DEFAULT:
            if min_n-count > max_n: method = DecreaseMethod.BINDOFF #check
            elif count <= self.gauge: method = DecreaseMethod.EDGE
            else: method = DecreaseMethod.SCHOOL_BUS
        #
        self.decrease(method, (bed, min_n), (bed, min_n+count))

    @decreaseLeft.register
    def decreaseLeft(self, bed: str, count: int):
        self.decreaseLeft(DecreaseMethod.DEFAULT, bed, count)

    @multimethod
    def decreaseRight(self, method: Union[DecreaseMethod, int], bed: str, count: int): #TODO: add default method stuff
        method = DecreaseMethod.parse(method) #check
        max_n = self.getMaxNeedle(bed[0])
        min_n = self.getMinNeedle(bed[0])
        #
        if method == DecreaseMethod.DEFAULT:
            if max_n-count < min_n: method = DecreaseMethod.BINDOFF #check
            elif count <= self.gauge: method = DecreaseMethod.EDGE
            else: method = DecreaseMethod.SCHOOL_BUS
        #
        self.decrease(method, (bed, max_n), (bed, max_n-count))

    @decreaseRight.register
    def decreaseRight(self, bed: str, count: int):
        self.decreaseRight(DecreaseMethod.DEFAULT, bed, count)

    @multimethod
    def increase(self, method: Union[IncreaseMethod, int], from_bn: Tuple[str, int], to_bn: Tuple[str, int]):
        method = IncreaseMethod.parse(method) #check
        assert method != IncreaseMethod.DEFAULT, "TODO: deal with this"
        #
        if method != IncreaseMethod.CASTON and method != IncreaseMethod.SPLIT:
            for c, info in self.k.carrier_map.items():
                if info.needle == from_bn[1]: self.k.miss(info.direction, f"{info.bed}{to_bn[1]}", c) #check
        #
        INC_FUNCS[method](self, from_bn, to_bn)

    @increase.register
    def increase(self, method: Union[IncreaseMethod, int], from_bn: str, to_bn: str):
        self.increase(method, getBedNeedle(from_bn), getBedNeedle(to_bn))

    @multimethod
    def increaseLeft(self, method: Union[IncreaseMethod, int], bed: str, count: int):
        method = IncreaseMethod.parse(method) #check
        min_n = self.getMinNeedle(bed[0])
        max_n = self.getMaxNeedle(bed[0])
        #
        # for c, info in self.k.carrier_map.items():
        #     if info.needle == min_n: self.k.miss("-", f"{info.bed}{min_n-count}", c)
        #
        if method == IncreaseMethod.DEFAULT:
            if min_n+count > max_n: method = IncreaseMethod.CASTON
            elif count <= self.gauge: method = IncreaseMethod.EDGE
            else: method = IncreaseMethod.SCHOOL_BUS
        #
        self.increase(method, (bed, min_n), (bed, min_n-count))

    @increaseLeft.register
    def increaseLeft(self, bed: str, count: int):
        self.increaseLeft(IncreaseMethod.DEFAULT, bed, count)

    @multimethod
    def increaseRight(self, method: Union[IncreaseMethod, int], bed: str, count: int):
        method = IncreaseMethod.parse(method) #check
        max_n = self.getMaxNeedle(bed[0])
        min_n = self.getMinNeedle(bed[0])
        #
        # for c, info in self.k.carrier_map.items():
        #     if info.needle == max_n: self.k.miss("+", f"{info.bed}{max_n+count}", c)
        #
        if method == IncreaseMethod.DEFAULT:
            if max_n-count < min_n: method = IncreaseMethod.CASTON
            elif count <= self.gauge: method = IncreaseMethod.EDGE
            else: method = IncreaseMethod.SCHOOL_BUS
        #
        self.increase(method, (bed, max_n), (bed, max_n+count))
    
    @increaseRight.register
    def increaseRight(self, bed: str, count: int):
        self.increaseRight(IncreaseMethod.DEFAULT, bed, count)
    
    # findNextValidNeedle = findNextValidNeedle
    """
    def findNextValidNeedle(self, bed: Optional[str], needle: int, d: str=None, in_limits: bool=True) -> Tuple[str, int]: #TODO: add code for in_limits=False (aka can search outside of limits with min_n and max_n)

        min_ns = {"f": self.getMinNeedle("f"), "b": self.getMinNeedle("b")}
        max_ns = {"f": self.getMaxNeedle("f"), "b": self.getMaxNeedle("b")}
        if bed is not None: min_n, max_n = min_ns[bed[0]], max_ns[bed[0]]
        else: min_n, max_n = min(min_ns["f"], min_ns["b"]), max(max_ns["f"], max_ns["b"])
        #
        n_1, n1 = needle, needle
        if d is None:
            for n_1, n1 in zip(range(needle, min_n-1, -1), range(needle, max_n+1)):
                if bed != "f" and n_1 >= min_ns["b"] and not n_1 in self.avoid_bns["b"]:
                    return ("b", n_1)
                elif bed != "b" and n_1 >= min_ns["f"] and not n_1 in self.avoid_bns["f"]:
                    return ("f", n_1)
                elif bed != "b" and n1 <= max_ns["f"] and not n1 in self.avoid_bns["f"]:
                    return ("f", n1)
                elif bed != "f" and n1 <= max_ns["b"] and not n1 in self.avoid_bns["b"]:
                    return ("b", n1)
        else: assert d == "-" or d == "+"
        #
        if d == "-" or n_1 != min_n:
            for n_1 in range(n_1, min_n-1, -1):
                if bed != "f" and n_1 >= min_ns["b"] and not n_1 in self.avoid_bns["b"]:
                    return ("b", n_1)
                elif bed != "b" and n_1 >= min_ns["f"] and not n_1 in self.avoid_bns["f"]:
                    return ("f", n_1)
        #
        if d == "+" or n1 != max_n:
            for n1 in range(n1, max_n+1):
                if bed != "b" and n1 <= max_ns["f"] and not n1 in self.avoid_bns["f"]:
                    return ("f", n1)
                elif bed != "f" and n1 <= max_ns["b"] and not n1 in self.avoid_bns["b"]:
                    return ("b", n1)
        #
        return (None, None)
    """
    

#===============================================================================






