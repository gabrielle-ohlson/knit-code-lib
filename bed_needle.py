from __future__ import annotations #so we don't have to worry about situations that would require forward declarations
from typing import Optional, Union, Tuple, List
from copy import deepcopy
from multimethod import multimethod

from .knitout_helpers import getBedNeedle


class BedNeedle:
    init_row = 0 #check

    @multimethod
    def __init__(self, bed: str, needle: int):
        self.bed = bed
        self.needle = needle
        self.loop_ct = 1
        self.stitch_ct = 0

    @__init__.register
    def __init__(self, bn: Tuple[str,int]):
        self.bed, self.needle = bn
        self.loop_ct = 1
        self.stitch_ct = 0
    
    @__init__.register
    def __init__(self, bn: str):
        self.bed, self.needle = getBedNeedle(bn)
        self.loop_ct = 1
        self.stitch_ct = 0

    #copy constructor
    @__init__.register
    def __init__(self, bn: BedNeedle):
        self.__dict__ = deepcopy(bn.__dict__) #check

    @property
    def current_row(self):
        return self.init_row+self.stitch_ct

    @multimethod
    def isSame(self, other: str):
        return self.format() == other
    
    @isSame.register
    def isSame(self, other: BedNeedle):
        return self.isSame(other.format())
    
    @isSame.register
    def isSame(self, other: Tuple[str,int]):
        return self.isSame(f"{other[0]}{other[1]}")

    def format(self) -> str:
        return f"{self.bed}{self.needle}"


# class BedNeedleTracker:
#     def __init__(self):
#         self.loops = BedNeedleList()
#         self.stitches = BedNeedleList()

#     def getActiveBns(self, bed: str) -> List[str]:
#         active_bns = []
#         for bn in self.loops:
#             if bn.bed == bed:
#                 bn_str = f"{bn.bed}{bn.needle}"
#                 if bn_str not in active_bns: active_bns.append(bn_str)
#         return [f"{bn.bed}{bn.needle}" for bn in self.loop_cts if bn.bed == bed]
    
#     def getStackCt(self, value: Union[BedNeedle,Tuple[str,int],str]):
#         ct = 0
#         for bn in self:
#             if bn.isSame(value): ct += 1
#         #
#         return ct

class BedNeedleList(list):
    def __init__(self, *args):
        super().__init__(BedNeedle(item) for item in args)
        # self.row_ct = 0

    def get(self, item: Union[BedNeedle, Tuple[str,int], str]) -> BedNeedle:
        for bn in self:
            if bn.isSame(item): return bn
        #
        raise ValueError(f"'{item}' not in list")

    def getActiveBns(self, bed: str) -> List[str]:
        return [f"{bn.bed}{bn.needle}" for bn in self if bn.bed == bed]
    
    def getStackCt(self, item: Union[BedNeedle, Tuple[str,int], str]):
        bn = self.get(item)
        return bn.loop_ct
    
    def getStitchCt(self, item: Union[BedNeedle, Tuple[str,int], str]):
        bn = self.get(item)
        return bn.stitch_ct
    
    def getRowCt(self) -> int:
        return max([bn.stitch_ct for bn in self], default=0)
    
    # def getLastRow(self, item: Union[BedNeedle, Tuple[str,int], str]):
    #     bn = self.get(item)
    #     return bn.init_row+bn.stitch_ct #check #TODO: have current_row too #? 
    
    def getHeldRowCt(self, item: Union[BedNeedle, Tuple[str,int], str]):
        bn = self.get(item)
        return max(0, self.getRowCt()-bn.current_row) #check #TODO: have current_row too #? 

    def format(self) -> List[str]:
        return [bn.format() for bn in self]

    #
    def __contains__(self, item: Union[BedNeedle, Tuple[str,int], str]): #check
        for bn in self:
            if bn.isSame(item): return True
        #
        return False
    
    @multimethod
    def append(self, item: BedNeedle) -> None:
        item.init_row = self.getRowCt() #check
        super().append(item)

    @append.register
    def append(self, item: Union[str, Tuple[str,int]]) -> None:
        self.append(BedNeedle(item))

    @multimethod
    def remove(self, item: BedNeedle) -> None:
        super().remove(self.get(item))

    @remove.register
    def remove(self, item: Union[str, Tuple[str,int]]) -> None:
        self.remove(BedNeedle(item))

    @multimethod
    def increment(self, bn: BedNeedle, is_tuck=False) -> None:
        if bn not in self: self.append(bn)
        else:
            if is_tuck: bn.loop_ct += 1
            else:
                bn.loop_ct = 1 #since knitted thru
                bn.stitch_ct += 1

        # if is_tuck:
        #     if bn not in self: self.append(bn)
        #     bn.loop_ct += 1
        # else: #knit
        #     if bn not in self:
        #         self.append(bn)
        #         bn.loop_ct += 1
        #     else: bn.stitch_ct += 1

    @increment.register
    def increment(self, item: Union[Tuple[str,int], str], is_tuck=False) -> None:
        if item in self: bn = self.get(item)
        else:
            bn = BedNeedle(item)
        #
        self.increment(bn, is_tuck)


    @multimethod
    def xfer(self, bn_from: BedNeedle, bn_to: BedNeedle, is_split=False) -> None:
        bn_to.loop_ct += bn_from.loop_ct
        #
        if bn_from.stitch_ct < bn_to.stitch_ct: #?
            bn_to.stitch_ct = bn_from.stitch_ct
            bn_to.init_row = bn_from.init_row
        # from_info = deepcopy(bn_from.__dict__) #check
        # from_info.bed = bn_to.bed
        # from_info.needle = bn_to.needle
        #
        if is_split:
            bn_from.init_row = self.getRowCt()
            bn_from.loop_ct = 1
            bn_from.stitch_ct = 0
        else: self.remove(bn_from)

    @xfer.register
    def xfer(self, item_from: Union[Tuple[str,int], str], item_to: Union[Tuple[str,int], str], is_split=False) -> None:
        if item_from in self: bn_from = self.get(item_from) #TODO: allow xfers from empty needles?
        else:
            bn_from = BedNeedle(item_from)
            bn_from.loop_ct = 0 #since not necessarily a loop forming
            self.append(bn_from)
        #
        # bn_from = self.get(item_from) #TODO: allow xfers from empty needles?
        if item_to in self: bn_to = self.get(item_to)
        else:
            bn_to = BedNeedle(item_to)
            self.append(bn_to)
        #
        self.xfer(bn_from, bn_to, is_split)

    def sort(self, reverse=False) -> None:
        super().sort(key=lambda bn: (-bn.needle,bn.bed))
        if not reverse: super().reverse() # bed `f` comes first (so works for when knitting at e.g. `rack 0.25`)
    
    @multimethod
    def sorted(self, reverse=False) -> BedNeedleList:
        res = sorted(self, key=lambda bn: (-bn.needle,bn.bed))
        if not reverse: res.reverse()
        return BedNeedleList(*res)
    
    @sorted.register
    def sorted(self, bed: str, reverse=False) -> BedNeedleList:
        res = sorted([bn for bn in self if bn.bed == bed], key=lambda bn: (-bn.needle,bn.bed))
        if not reverse: res.reverse()
        return BedNeedleList(*res)
    
    def rackSorted(self, rack: int, reverse=False) -> BedNeedleList: #check
        res = [bn if bn.bed == "f" else BedNeedle(bn.bed, bn.needle+rack) for bn in self]
        res = sorted(res, key=lambda bn: (-bn.needle,bn.bed))
        if not reverse: res.reverse()
        #
        res = [bn if bn.bed == "f" else BedNeedle(bn.bed, bn.needle-rack) for bn in self]
        return BedNeedleList(*res)
    
    def min(self, bed: Optional[str]=None) -> BedNeedle:
        assert len(self) != 0
        return self.sorted(bed, reverse=False)[0]
    
    def max(self, bed: Optional[str]=None) -> BedNeedle:
        assert len(self) != 0
        return self.sorted(bed, reverse=False)[-1]
