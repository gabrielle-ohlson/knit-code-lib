from __future__ import annotations #so we don't have to worry about situations that would require forward declarations
from typing import Optional, Union, Tuple, List
# from copy import deepcopy
from multimethod import multimethod

#======
import sys
from pathlib import Path

## Standalone boilerplate before relative imports
if not __package__: #remove #?
	DIR = Path(__file__).resolve().parent
	sys.path.insert(0, str(DIR.parent))
	__package__ = DIR.name


from .knitout_helpers import getBedNeedle
#======


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
		self.bed = bn.bed
		self.needle = bn.needle
		self.loop_ct = bn.loop_ct
		self.stitch_ct = bn.stitch_ct

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


class BedNeedleList(list):
	def __init__(self, *args):
		for item in args:
			bn = BedNeedle(item)
			self.__dict__[bn.format()] = bn
		#
		super().__init__(BedNeedle(item) for item in args) #TODO: consolidate this into above for loop

	@multimethod
	def get(self, item: str):
		try:
			return self.__dict__[item]
		except KeyError:
			return None
	
	@get.register
	def get(self, item: Tuple[str,int]) -> BedNeedle:
		try:
			return self.__dict__[f"{item[0]}{item[1]}"]
		except KeyError:
			return None

	@get.register
	def get(self, item: BedNeedle) -> BedNeedle:
		try:
			return self.__dict__[item.format()]
		except KeyError:
			return None

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
	
	def getHeldRowCt(self, item: Union[BedNeedle, Tuple[str,int], str]):
		bn = self.get(item)
		return max(0, self.getRowCt()-bn.current_row) #TODO: have current_row too #? 

	def format(self) -> List[str]:
		return [bn.format() for bn in self]

	@multimethod
	def __contains__(self, item: str):
		return item in self.__dict__
	
	@__contains__.register
	def __contains__(self, item: BedNeedle):
		return item.format() in self.__dict__
	
	@__contains__.register
	def __contains__(self, item: Tuple[str,int]):
		return f"{item[0]}{item[1]}" in self.__dict__
	
	def copy(self): #new
		return BedNeedleList(*[bn for bn in self])
	
	@multimethod
	def append(self, item: BedNeedle) -> None:
		item.init_row = self.getRowCt() #check
		super().append(item)
		self.__dict__[item.format()] = item #new

	@append.register
	def append(self, item: Union[str, Tuple[str,int]]) -> None:
		self.append(BedNeedle(item))

	@multimethod
	def remove(self, item: BedNeedle) -> None:
		super().remove(self.get(item))
		del self.__dict__[item.format()]

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
			bn_to.loop_ct = 0 #since not necessarily a loop forming #new #check
			self.append(bn_to)
		#
		self.xfer(bn_from, bn_to, is_split)

	def sort(self, reverse=False) -> None:
		super().sort(key=lambda bn: (-bn.needle,bn.bed))
		if not reverse: super().reverse() # bed `f` comes first (so works for when knitting at e.g. `rack 0.25`)
	
	def sorted(self, bed: Optional[str], reverse=False) -> BedNeedleList:
		if bed is None: res = sorted(self, key=lambda bn: (-bn.needle,bn.bed))
		else: res = sorted([bn for bn in self if bn.bed == bed], key=lambda bn: (-bn.needle,bn.bed))
		#
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
