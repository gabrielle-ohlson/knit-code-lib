from __future__ import annotations #so we don't have to worry about situations that would require forward declarations
from multimethod import multimethod
from collections.abc import MutableMapping
import warnings
# from functools import singledispatchmethod
from typing import Union, Optional, Dict, Tuple, List, Callable
from enum import Enum
from os import path
from copy import deepcopy
import math

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

from knitlib import altTuckCaston, altTuckClosedCaston, altTuckOpenTubeCaston, zigzagCaston, sheetBindoff, closedTubeBindoff, openTubeBindoff, dropFinish, wasteSection
from .helpers import gauged, toggleDirection, bnValid, getNeedleRanges
from .stitch_patterns import jersey, interlock, rib, garter, seed
# from .helpers import multidispatchmethod

from .knitout_helpers import getBedNeedle, rackedXfer
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


class RangeOp(Enum):
	PATTERN = 0
	TWIST = 1
	SPLIT = 2
	#
	@classmethod
	def parse(self, val):
		if isinstance(val, self): return val
		elif isinstance(val, int): return self._value2member_map_[val]
		else: raise ValueError


class FuncRange:
	def __init__(self, op, *args):
		self.op = RangeOp.parse(op)
		self.args = args

	# needle_ranges, twisted_stitches = self.twistNeedleRanges(needle_range, bed)
	# 	for n_range, twisted_stitch in zip(needle_ranges, twisted_stitches):
	# 		func_args["start_n"] = n_range[0]
	# 		func_args["end_n"] = n_range[1]
	# 		#
	# 		func(**func_args)
	# 		#
	# 		self.twistedStitch(d, twisted_stitch, *cs) #TODO: handle splits too


class Settings:
	def __init__(self, stitch_number=None, caston_stitch_number=None, xfer_stitch_number=None, tuck_stitch_number=None, speed_number=None):
		# extensions:
		self.stitch_number = stitch_number
		self.caston_stitch_number = caston_stitch_number
		self.xfer_stitch_number = xfer_stitch_number #TODO: make knitlib_knitout do these for xfer/tuck operations (and then reset) #v
		self.tuck_stitch_number = tuck_stitch_number

		self.speed_number = speed_number

		# SETTINGS/CONSTANTS:
		self.machine = "swgn2"
		self.max_rack = 4


class KnitObject:
	def __init__(self, k, gauge=1, **settings_kwargs):
		rack_value_op = getattr(k, "rack_value", None)
		assert rack_value_op is not None, "'k' must come from the 'knitlib_knitout' module" #debug
		#
		self.k = k
		self.gauge = gauge
		self.mod = {"f": 0, "b": gauge//2} #TODO: add function to change this
		self.settings = Settings()
		self.setSettings(**settings_kwargs)
		#
		# self.min_n = {"f": float("inf"), "b": float("inf")}
		# self.max_n = {"f": float("-inf"), "b": float("-inf")}
		#
		self.active_carrier = None #TODO #*
		self.draw_carrier = None
		self.waste_carrier = None
		self.avoid_bns = {"f": [], "b": []} #, "fs": [], "bs": []}
		self.SPLIT_ON_EMPTY = True
		self.twist_bns = list()
		self.split_bns = list()
		# self.st_cts = {} #?
		#
		self._row_ct = 0
		#
		self.pat_args = {
			"k": None,
			"start_n": None,
			"end_n": None,
			"passes": 1,
			"c": None,
			"bed": None,
			"gauge": self.gauge, #will *not* be a reference (should be updated each time in case it changes)
			"xfer_bns_setup": True,
			"xfer_bns_back": True,
			"machine": None,
			"init_direction": None
			# "sequence": None,
			# "bn_locs"
			# "avoid_bns": {"f": [], "b": []}
		}
	
	@property
	def row_ct(self):
		return self._row_ct

	@row_ct.setter
	def row_ct(self, value: int):
		self.k.comment(f"row: {value}")
		self._row_ct = value

	def setSettings(self, **kwargs):
		# self.settings.__dict__.update((k, v) for k, v in kwargs.items() if k in self.settings.__dict__)
		for key, val in kwargs.items():
			if key in self.settings.__dict__: self.settings.__dict__[key] = val
			else: warnings.warn(f"'{key}' is not a valid knitout settings. skipping.")

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
	
	def wasteSection(self, bed: Optional[str], needle_range: Tuple[int, int], waste_c: Optional[str], draw_c: Optional[str], other_cs: Union[List[str], Tuple[str]]):
		if waste_c is not None: self.waste_carrier = waste_c
		if draw_c is not None: self.draw_carrier = draw_c

		if self.waste_carrier is None:
			for c in range(6, 0, -1):
				if f"{c}" not in self.k.carrier_map.keys() and f"{c}" not in other_cs:
					self.waste_carrier = f"{c}"
					break
			#
			assert self.waste_carrier is not None, "No available carriers to use for the waste section."
			print(f"WARNING: setting carrier '{self.waste_carrier}' as `self.waste_carrier`, since it was not manually assigned a value.")
		if self.draw_carrier is None:
			for c in range(6, 0, -1):
				if self.waste_carrier != f"{c}" and f"{c}" not in self.k.carrier_map.keys() and f"{c}" not in other_cs:
					self.draw_carrier = f"{c}"
					break
			assert self.draw_carrier is not None, "No available carriers to use for the draw string."
			print(f"WARNING: setting carrier '{self.draw_carrier}' as `self.draw_carrier`, since it was not manually assigned a value.")

		# assert self.waste_carrier is not None and self.draw_carrier is not None

		if needle_range[0] > needle_range[1]: left_n, right_n = needle_range[::-1]
		else: left_n, right_n = needle_range

		initial = not len(self.k.carrier_map.keys())

		all_cs = list(set(list(other_cs) + [self.waste_carrier, self.draw_carrier]))
		in_cs = [c for c in all_cs if c not in self.k.carrier_map.keys()]
		wasteSection(self.k, left_n, right_n, caston_bed=bed, waste_c=self.waste_carrier, draw_c=self.draw_carrier, in_cs=in_cs, gauge=self.gauge, initial=initial, draw_middle=(not initial), machine=self.settings.machine) #end_on_right=[self.draw_carrier], initial=True, draw_middle=False, machine=self.settings.machine)


	def caston(self, method: Union[CastonMethod, int], bed: Optional[str], needle_range: Tuple[int, int], *cs: str, **kwargs) -> None:
		if self.settings.caston_stitch_number is not None:
			if self.settings.stitch_number is not None: reset_stitch_number = self.settings.stitch_number
			else: reset_stitch_number = self.k.stitch_number
			self.k.stitchNumber(self.settings.caston_stitch_number) #check
		else:
			if self.settings.stitch_number is not None: reset_stitch_number = self.settings.stitch_number
			else: reset_stitch_number = None

		method = CastonMethod.parse(method)
		#
		not_in_cs = [c for c in cs if c not in self.k.carrier_map.keys()]
		init_caston = False
		if len(not_in_cs):
			init_caston = True
			#
			if self.settings.machine == "kniterate":
				self.k.incarrier(*not_in_cs)
				#
				"""
				if needle_range[0] > needle_range[1]: left_n, right_n = needle_range[::-1]
				else: left_n, right_n = needle_range
				# tube = (bed != "f" and bed != "b")
				#
				if self.waste_carrier is None:
					for c in range(6, 0, -1):
						if f"{c}" not in self.k.carrier_map.keys():
							self.waste_carrier = f"{c}"
							break
					#
					assert self.waste_carrier is not None, "No available carriers to use for the waste section."
					print(f"WARNING: setting carrier '{self.waste_carrier}' as `self.waste_carrier`, since it was not manually assigned a value.")
				if self.draw_carrier is None:
					for c in range(6, 0, -1):
						if self.waste_carrier != f"{c}" and f"{c}" not in self.k.carrier_map.keys():
							self.draw_carrier = f"{c}"
							break
					assert self.draw_carrier is not None, "No available carriers to use for the draw string."
					print(f"WARNING: setting carrier '{self.draw_carrier}' as `self.draw_carrier`, since it was not manually assigned a value.")
				#
				wasteSection(self.k, left_n, right_n, caston_bed=bed, waste_c=self.waste_carrier, draw_c=self.draw_carrier, in_cs=[self.draw_carrier], gauge=self.gauge, end_on_right=[self.draw_carrier], initial=True, draw_middle=False, machine=self.settings.machine) #, interlock_passes=20) #TODO: get waste_c and draw_c
				"""
			else: self.k.inhook(*not_in_cs)
		#
		knit_after = kwargs.get("knit_after", init_caston)
		#
		#
		if method == CastonMethod.ALT_TUCK_CLOSED:
			if bed != "f" and bed != "b":
				altTuckClosedCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge, tuck_pattern=init_caston, stitch_number=self.settings.caston_stitch_number)
				#
				if reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check
			else:
				altTuckCaston(self.k, needle_range[0], needle_range[1], c=cs, bed=bed, gauge=self.gauge, tuck_pattern=init_caston, stitch_number=self.settings.caston_stitch_number, knit_after=knit_after, knit_stitch_number=reset_stitch_number)
				#
				if not init_caston and reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check
		elif method == CastonMethod.ALT_TUCK_OPEN:
			assert bed != "f" and bed != "b", "`CastonMethod.ALT_TUCK_OPEN` only valid for double bed knitting."
			altTuckOpenTubeCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge, tuck_pattern=init_caston, stitch_number=self.settings.caston_stitch_number, knit_after=knit_after, knit_stitch_number=reset_stitch_number)
			#
			if not init_caston and reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check
		elif method == CastonMethod.ZIGZAG:
			zigzagCaston(self.k, needle_range[0], needle_range[1], c=cs, gauge=self.gauge, tuck_pattern=init_caston, stitch_number=self.settings.caston_stitch_number)
			#
			if reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check
			#
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
		if len(not_in_cs) and self.settings.machine != "kniterate": self.k.releasehook(*not_in_cs)
	

	@multimethod
	def knitPass(self, pattern: Union[StitchPattern, int, Callable], bed: Optional[str], needle_range: Optional[Tuple[int,int]], *cs: str, **kwargs) -> None: #TODO: make sure still works with *cs before pattern
		if self.settings.stitch_number is not None and self.k.stitch_number != self.settings.stitch_number: self.k.stitchNumber(self.settings.stitch_number) #check

		do_releasehook = False
		init_cs = False
		if needle_range is None:
			try:
				needle_range = self.getNeedleRange(bed, *cs)
			except KeyError:
				min_n = self.getMinNeedle(bed)
				max_n = self.getMaxNeedle(bed)
				needle_range = (max_n, min_n)
				init_cs = True
		else:
			not_in_cs = [c for c in cs if c not in self.k.carrier_map.keys()]
			if len(not_in_cs):
				init_cs = True
				assert len(not_in_cs) == len(cs), f"Plaited pattern pass with only some carriers already in not supported yet"
		#
		if needle_range[1] > needle_range[0]: d = "+"
		else: d = "-"

		func_args = deepcopy(self.pat_args) # pat_args

		func_args["k"] = self.k
		func_args["c"] = cs
		func_args["bed"] = bed
		func_args["gauge"] = self.gauge
		func_args["machine"] = self.settings.machine
		func_args["init_direction"] = d
		#
		if init_cs:
			func_args["inhook"] = True
			func_args["releasehook"] = True
			func_args["tuck_pattern"] = True
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
			if init_cs and "inhook" not in func.__code__.co_varnames:
				if self.settings.machine == "kniterate": self.k.incarrier(*cs)
				else: self.k.inhook(*cs)
				#
				do_releasehook = True
				del func_args["inhook"]
				del func_args["releasehook"]
				del func_args["tuck_pattern"]

		#
		for key in list(func_args.keys()).copy():
			if key == "passes" and key not in func.__code__.co_varnames and "iters" in func.__code__.co_varnames: #* #temp fix
				func_args["iters"] = func_args["passes"]
				del func_args["passes"]
			elif key == "bed" and key not in func.__code__.co_varnames and "main_bed" in func.__code__.co_varnames: #* #temp fix
				func_args["main_bed"] = func_args["bed"]
				del func_args["bed"]
			elif key not in func.__code__.co_varnames:
				warnings.warn(f"WARNING: '{func.__name__}' function does not use suggested parameter, '{key}'.")
				del func_args[key]
				# assert key in func.__code__.co_varnames, f"'{func.__name__}' function does not use required parameter, '{key}'."
		#
		for key, val in kwargs.items():
			if key in func.__code__.co_varnames: func_args[key] = val
			else: warnings.warn(f"kwarg '{key}' not a valid parameter for '{func.__name__}' function.")

		if "avoid_bns" in func.__code__.co_varnames:
			func_args["avoid_bns"] = deepcopy(self.avoid_bns)
		#
		func_ranges = self.funcRanges(needle_range, bed)
		for func_range in func_ranges:
			if func_range.op == RangeOp.TWIST:
				self.twistedStitch(d, func_range.args, *cs)
			elif func_range.op == RangeOp.SPLIT: self.splitStitch(d, func_range.args, *cs)
			else:
				func_args["start_n"] = func_range.args[0]
				func_args["end_n"] = func_range.args[1]
				#
				func(**func_args)
		if self.settings.machine != "kniterate" and do_releasehook: self.k.releasehook(*cs)
		"""
		needle_ranges, twisted_stitches = self.twistNeedleRanges(needle_range, bed)
		for n_range, twisted_stitch in zip(needle_ranges, twisted_stitches):
			func_args["start_n"] = n_range[0]
			func_args["end_n"] = n_range[1]
			#
			func(**func_args)
			#
			self.twistedStitch(d, twisted_stitch, *cs) #TODO: handle splits too
		"""

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
	def bindoff(self, method: Union[BindoffMethod, int], bed: Optional[str], needle_range: Optional[Tuple[int, int]], *cs: str, **kwargs) -> None:
		if "outhook" in kwargs: outhook = kwargs["outhook"]
		else: outhook = False
		#
		method = BindoffMethod.parse(method) #check
		#
		if needle_range is None: needle_range = self.getNeedleRange(bed, *cs)
		#
		if method == BindoffMethod.CLOSED:
			if bed == "f" or bed == "b": sheetBindoff(self.k, needle_range[0], needle_range[1], cs, bed, self.gauge, outhook=outhook)
			else: closedTubeBindoff(self.k, needle_range[0], needle_range[1], cs, self.gauge, outhook=outhook, machine=self.settings.machine)
		elif method == BindoffMethod.OPEN:
			assert bed != "f" and bed != "b", "`BindoffMethod.OPEN` only valid for double bed knitting."
			openTubeBindoff(self.k, needle_range[0], needle_range[1], cs, self.gauge, outhook=outhook, machine=self.settings.machine)
		elif method == BindoffMethod.DROP:
			if bed == "b": front_needle_ranges = []
			else: front_needle_ranges = sorted(self.getNeedleRange("f", *cs))
			#
			if bed == "f": back_needle_ranges = []
			else: back_needle_ranges = sorted(self.getNeedleRange("b", *cs))
			#
			dropFinish(self.k, front_needle_ranges=front_needle_ranges, back_needle_ranges=back_needle_ranges, out_carriers=cs if outhook else [], machine=self.settings.machine)
		else: raise ValueError("unsupported bindoff method")
		#
		if "out_cs" in kwargs:
			for c in kwargs["out_cs"]:
				if self.settings.machine == "kniterate": self.k.outcarrier(c)
				else: self.k.outhook(c)
			#
			self.k.pause("cut yarns")

		if "roll_out" in kwargs:
			self.rollerAdvance(1000) #TODO: #check if good value
			n_range1 = getNeedleRanges(needle_range[1], needle_range[0], return_direction=False)
			n_range2 = getNeedleRanges(needle_range[0], needle_range[1], return_direction=True)
			
			for i in range(4): #TODO: #check if good value
				for n in n_range1:
					self.k.drop(f"f{n}")
				
				for n in n_range1:
					self.k.drop(f"b{n}")

	@bindoff.register
	def bindoff(self, method: Union[BindoffMethod, int], bed: Optional[str], *cs: str, **kwargs) -> None:
		self.bindoff(method, bed, None, *cs, **kwargs)

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
		# 	ct = max(cts)
		# 	if ct > self.row_ct:
		# 		# res = dict(reversed(sorted(self.st_cts.items(), key=lambda item: (-int(item[0][1:]),item[0][0])))) #debug
		# 		self.row_ct = ct

	# @multimethod
	def updateCarriers(self, direction: str, bed: str, needle: int, *cs: str) -> None:
		row_counted = direction is None
		#
		for c in cs:
			if not row_counted and self.k.carrier_map[c].direction != direction:
				self.setRowCount()
				row_counted = True
			self.k.carrier_map[c].update(direction, bed, needle)
	
	@multimethod
	def rackedXfer(self, from_bed: str, from_needle: int, to_bed: str, to_needle: int, reset_rack: bool=True):
		rackedXfer(self, from_bed, from_needle, to_bed, to_needle, reset_rack=reset_rack)
	
	@rackedXfer.register
	def rackedXfer(self, from_bn: Tuple[str,int], to_bn: Tuple[str,int], reset_rack: bool=True):
		self.rackedXfer(*from_bn, *to_bn, reset_rack=reset_rack)

	@rackedXfer.register
	def rackedXfer(self, from_bn: str, to_bn: str, reset_rack: bool=True):
		self.rackedXfer(*getBedNeedle(from_bn), *getBedNeedle(to_bn), reset_rack=reset_rack)

	@multimethod
	def rackedSplit(self, d: str, from_bed: str, from_needle: int, to_bed: str, to_needle: int, cs: Union[List[str], Tuple[str]], reset_rack: bool=True):
		rackedXfer(self, from_bed, from_needle, to_bed, to_needle, d=d, cs=cs, reset_rack=reset_rack)
	
	@rackedSplit.register
	def rackedSplit(self, d: str, from_bn: Tuple[str,int], to_bn: Tuple[str,int], cs: Union[List[str], Tuple[str]], reset_rack: bool=True):
		self.rackedSplit(d, *from_bn, *to_bn, cs, reset_rack=reset_rack)

	@rackedSplit.register
	def rackedSplit(self, d: str, from_bn: str, to_bn: str, cs: Union[List[str], Tuple[str]], reset_rack: bool=True):
		self.rackedSplit(d, *getBedNeedle(from_bn), *getBedNeedle(to_bn), cs, reset_rack=reset_rack)

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
						if bed is not None and carrier.bed != bed and 0 < bed_max_n-carrier.needle < self.gauge:
							self.k.miss("+", bed, bed_max_n, c)
							self.updateCarriers(toggleDirection(carrier.direction), None, None, c) #update it again to account for toggling #TODO: improve this #* #temp fix
						start_n = carrier.needle
					elif d == "+" and (start_n is None or carrier.needle > start_n):
						if bed is not None and carrier.bed != bed and 0 < carrier.needle-bed_min_n < self.gauge:
							self.k.miss("-", bed, bed_min_n, c)
							self.updateCarriers(toggleDirection(carrier.direction), None, None, c) #update it again to account for toggling #TODO: improve this #* #temp fix
						start_n = carrier.needle
			elif carrier.direction is not None:
				d = carrier.direction
				if d == "-" and (start_n is None or carrier.needle-1 < start_n): start_n = carrier.needle-1
				elif d == "+" and (start_n is None or carrier.needle+1 > start_n): start_n = carrier.needle+1
		#
		assert all([self.k.carrier_map[c].direction == d or self.k.carrier_map[c].direction is None for c in cs]), f"d: {d}, cs: {cs}, directions: {[self.k.carrier_map[c].direction for c in cs]}"
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

	def findNextLoop(self, bed: Optional[str], needle: int, d: str=None):
		if d == "+":
			for n in range(needle+1, self.getMaxNeedle(bed)+1):
				if (bed == "f" or bed is None) and f"f{n}" in self.k.bns and f"f{n}" not in self.twist_bns and f"f{n}" not in self.split_bns: return ("f", n)
				elif (bed == "b" or bed is None) and f"b{n}" in self.k.bns and f"b{n}" not in self.twist_bns and f"b{n}" not in self.split_bns: return ("b", n)
		elif d == "-":
			for n in range(needle-1, self.getMinNeedle(bed)-1, -1):
				if (bed == "f" or bed is None) and f"f{n}" in self.k.bns and f"f{n}" not in self.twist_bns and f"f{n}" not in self.split_bns: return ("f", n)
				elif (bed == "b" or bed is None) and f"b{n}" in self.k.bns and f"b{n}" not in self.twist_bns and f"b{n}" not in self.split_bns: return ("b", n)
		else: # d is None
			for n_1, n1 in zip(range(needle-1, self.getMinNeedle(bed)-1, -1), range(needle+1, self.getMaxNeedle(bed)+1)):
				if bed == "f" or bed is None:
					if f"f{n_1}" in self.k.bns and f"f{n_1}" not in self.twist_bns and f"f{n_1}" not in self.split_bns: return ("f", n_1)
					elif f"f{n1}" in self.k.bns and f"f{n1}" not in self.twist_bns and f"f{n1}" not in self.split_bns: return ("f", n1)
				
				if bed == "b" or bed is None:
					if f"b{n_1}" in self.k.bns and f"b{n_1}" not in self.twist_bns and f"b{n_1}" not in self.split_bns: return ("b", n_1)
					elif f"b{n1}" in self.k.bns and f"b{n1}" not in self.twist_bns and f"b{n1}" not in self.split_bns: return ("b", n1)
		#
		return (None, None)

	def funcRanges(self, needle_range: Tuple[int, int], bed: Union[str, None]=None) -> Tuple[List[Tuple[int, int]], List[Union[None, str, List[str]]]]:
		res = []
		#
		if needle_range[1] > needle_range[0]:
			d = "+"
			shift = 1
		else:
			d = "-"
			shift = -1
		#
		n0 = needle_range[0]
		for n in range(needle_range[0], needle_range[1]+shift, shift):
			# done = False
			twisted_stitches = []
			split_stitches = []
			if bed != "b":
				if f"f{n}" in self.twist_bns:
					twisted_stitches.append(f"f{n}")
					#
					res.append(FuncRange(RangeOp.PATTERN, n0, n-shift))
					n0 = n+shift
				elif f"f{n}" in self.split_bns:
					split_stitches.append(f"f{n}")
					res.append(FuncRange(RangeOp.PATTERN, n0, n-shift))
					_, n0 = self.findNextLoop(bed="f", needle=n, d=d)
					n0 += shift
			
			if bed != "f":
				if f"b{n}" in self.twist_bns:
					if not len(twisted_stitches) and not len(split_stitches):
						res.append(FuncRange(RangeOp.PATTERN, n0, n-shift))
						n0 = n+shift
					#
					twisted_stitches.append(f"b{n}")
				elif f"b{n}" in self.split_bns:
					if not len(twisted_stitches) and not len(split_stitches):
						res.append(FuncRange(RangeOp.PATTERN, n0, n-shift))
						_, n0 = self.findNextLoop(bed="f", needle=n, d=d)
						n0 += shift
					#
					split_stitches.append(f"b{n}")

			if n == needle_range[1] and not len(twisted_stitches) and not len(split_stitches): res.append(FuncRange(RangeOp.PATTERN, n0, n))
			else:
				if len(twisted_stitches): res.append(FuncRange(RangeOp.TWIST, *twisted_stitches))
				if len(split_stitches): res.append(FuncRange(RangeOp.SPLIT, *split_stitches))
		# # n_ranges = []
		# # twisted_stitches = []
		# if needle_range[1] > needle_range[0]:
		# 	n0 = needle_range[0]
		# 	for n in range(needle_range[0], needle_range[1]+1):
		# 		# done = False
		# 		twist_bns = []
		# 		split_bns = []
		# 		if bed != "b":
		# 			if f"f{n}" in self.twist_bns:
		# 				twist_bns.append(f"f{n}")
		# 				#
		# 				res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 				# done = True
		# 				n0 = n+1
		# 			elif f"f{n}" in self.split_bns:
		# 				split_bns.append(f"f{n}")
		# 				res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 				n0 = n+1
				

		# 		if bed != "f":
		# 			if f"b{n}" in self.twist_bns:
		# 				twist_bns.append(f"b{n}")
		# 				#
		# 				if not len(twist_bns) and not len(split_bns):
		# 					res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 					n0 = n+1
		# 			elif f"b{n}" in self.split_bns:
		# 				split_bns.append(f"b{n}")
		# 				#
		# 				if not len(twist_bns) and not len(split_bns):
		# 					res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 					n0 = n+1

		# 		if n == needle_range[1] and not len(twist_bns) and not len(split_bns): res.append(FuncRange(RangeOp.PATTERN, n0, n))
		# 		else:
		# 			if len(twist_bns): res.append(FuncRange(RangeOp.TWIST, *twist_bns))
		# 			if len(split_bns): res.append(FuncRange(RangeOp.SPLIT, *split_bns))
		# 		"""
		# 		if bed != "b" and f"f{n}" in self.twist_bns:
		# 			twist_bns.append(f"f{n}")
		# 			#
		# 			res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 			# done = True
		# 			n0 = n+1
					
		# 			# res.append(FuncRange(RangeOp.TWIST, f"f{n}"))
					
		# 		#
		# 		if bed != "f" and f"b{n}" in self.twist_bns:
		# 			if not len(twist_bns):
		# 				res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 				n0 = n+1
		# 			#
		# 			twist_bns.append(f"b{n}")
		# 			# if not done:
		# 			# 	res.append(FuncRange(RangeOp.PATTERN, n0, n-1))
		# 			# 	# n_ranges.append((n0, n-1))
		# 			# 	done = True
		# 			# 	n0 = n+1
		# 		#
		# 		if len(twist_bns): res.append(FuncRange(RangeOp.TWIST, *twist_bns))
		# 		elif n == needle_range[1]:
		# 			res.append(FuncRange(RangeOp.PATTERN, n0, n))
		# 			# n_ranges.append((n0, n))
		# 			# twisted_stitches.append(None)
		# 		"""
		# else:
		# 	n0 = needle_range[0]
		# 	for n in range(needle_range[0], needle_range[1]-1, -1):
		# 		twist_bns = []
		# 		split_bns = []
		# 		# done = False

		# 		if bed != "b":
		# 			if f"f{n}" in self.twist_bns:
		# 				twist_bns.append(f"f{n}")
		# 				#
		# 				res.append(FuncRange(RangeOp.PATTERN, n0, n+1))
		# 				# done = True
		# 				n0 = n-1
		# 			elif f"f{n}" in self.split_bns:
		# 				split_bns.append(f"f{n}")
		# 				res.append(FuncRange(RangeOp.PATTERN, n0, n+1))
		# 				n0 = n-1
				

		# 		if bed != "f":
		# 			if f"b{n}" in self.twist_bns:
		# 				twist_bns.append(f"b{n}")
		# 				#
		# 				if not len(twist_bns) and not len(split_bns):
		# 					res.append(FuncRange(RangeOp.PATTERN, n0, n+1))
		# 					n0 = n-1
		# 			elif f"b{n}" in self.split_bns:
		# 				split_bns.append(f"b{n}")
		# 				#
		# 				if not len(twist_bns) and not len(split_bns):
		# 					res.append(FuncRange(RangeOp.PATTERN, n0, n+1))
		# 					n0 = n-1

		# 		if n == needle_range[1] and not len(twist_bns) and not len(split_bns): res.append(FuncRange(RangeOp.PATTERN, n0, n))
		# 		else:
		# 			if len(twist_bns): res.append(FuncRange(RangeOp.TWIST, *twist_bns))
		# 			if len(split_bns): res.append(FuncRange(RangeOp.SPLIT, *split_bns))




		# 		# if bed != "b" and f"f{n}" in self.twist_bns:
		# 		# 	twisted_stitches.append(f"f{n}")
		# 		# 	done = True
		# 		# 	n_ranges.append((n0, n+1))
		# 		# 	n0 = n-1
		# 		# #
		# 		# if bed != "f" and f"b{n}" in self.twist_bns:
		# 		# 	if done:
		# 		# 		twisted_stitches[-1] = [twisted_stitches[-1], f"b{n}"]
		# 		# 	else:
		# 		# 		twisted_stitches.append(f"b{n}")
		# 		# 		done = True
		# 		# 		n_ranges.append((n0, n+1))
		# 		# 		n0 = n-1
		# 		# #
		# 		# if not done and n == needle_range[1]:
		# 		# 	n_ranges.append((n0, n))
		# 		# 	twisted_stitches.append(None)
		#
		if not len(res):
			res.append(RangeOp.PATTERN, *needle_range)
		#
		return res
		# if not len(n_ranges):
		# 	n_ranges.append(needle_range)
		# 	twisted_stitches.append(None)
		# #
		# return n_ranges, twisted_stitches
	
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
		if self.settings.caston_stitch_number is not None:
			reset_stitch_number = self.k.stitch_number
			self.k.stitchNumber(self.settings.caston_stitch_number) #check
		else: reset_stitch_number = None

		d2 = toggleDirection(d)
		#
		assert not bn in self.k.bns, f"requesting twisted stitch on needle that already has a loop, '{bn}'" #debug
		#
		self.k.miss(d, bn, *cs)
		self.k.knit(d2, bn, *cs)
		self.k.miss(d, bn, *cs)
		self.k.comment("end twisted stitch")
		if reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check

		#
		bed, needle = getBedNeedle(bn) #TODO: move this to updateCarriers instead #?
		self.updateCarriers(d, bed, needle, *cs)
		# #
		# if bn not in self.st_cts: self.st_cts[bn] = 0 #means there is a loop there, but not a full stitch #remove
		# else: self.st_cts[bn] += 1
		#
		self.twist_bns.remove(bn) #TODO: decide what should go in twist_bns (str or tuple?)

	@twistedStitch.register
	def twistedStitch(self, d: str, bns: Union[Tuple[str], List[str]], *cs: str) -> None:
		if self.settings.caston_stitch_number is not None:
			reset_stitch_number = self.k.stitch_number
			self.k.stitchNumber(self.settings.caston_stitch_number) #check
		else: reset_stitch_number = None

		d2 = toggleDirection(d)
		for bn in bns:
			#
			assert not bn in self.k.bns, f"requesting twisted stitch on needle that already has a loop, '{bn}'" #debug
			#
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
		#
		if reset_stitch_number is not None: self.k.stitchNumber(reset_stitch_number) #check

	@twistedStitch.register
	def twistedStitch(self, d: str, bn: None, *cs: str) -> None:
		return
	
	#TODO: add something similar to twist_bns for splits (during school bus increase)
	def splitStitch(self, d: str, bns: Union[Tuple[str], List[str]], *cs: str) -> None:
		for bn in bns:
			assert not bn in self.k.bns, f"requesting split stitch on needle that already has a loop, '{bn}'" #debug
			#
			bed, needle = getBedNeedle(bn) #TODO: move this to updateCarriers instead
			bed2 = "b" if bed == "f" else "f"
			#
			_, next_n = self.findNextLoop(bed=bed, needle=needle, d=d)
			self.rackedSplit(d, f"{bed}{next_n}", f"{bed2}{needle}", cs, reset_rack=True)
			self.k.xfer(f"{bed2}{needle}", f"{bed}{needle}")
			#
			self.split_bns.remove(bn) #TODO: decide what should go in twist_bns (str or tuple?)

	def write(self, out_fn: str):
		if len(self.k.carrier_map.keys()):
			_carriers = list(self.k.carrier_map.keys())
			for c in _carriers:
				if self.settings.machine == "kniterate": self.k.outcarrier(c)
				else: self.k.outhook(c)
		self.k.write(path.join(path.dirname(path.dirname( path.abspath(__file__))), f"knitout_files/{out_fn}.k"))
	
	# @multimethod
	# def decrease(self, method: Union[DecreaseMethod, int], from_bn: Tuple[str, int], to_bn: Tuple[str, int]):
	def decrease(self, method: Union[DecreaseMethod, int], from_needle: int, to_needle: int, bed: Optional[str]=None):
		method = DecreaseMethod.parse(method)
		#
		if method == DecreaseMethod.BINDOFF:
			min_dist = None

			for c, carrier in self.k.carrier_map.items():
				dist = abs(from_needle[1]-carrier.needle)
				if min_dist is None or dist < min_dist:
					self.active_carrier = c
					min_dist = dist
			#
			assert min_dist is not None, "no active carriers to use for decBindoff"
		#
		assert method != DecreaseMethod.DEFAULT, "TODO: deal with this"
		DEC_FUNCS[method](self, from_needle, to_needle, bed)

	"""
	@decrease.register
	def decrease(self, method: Union[DecreaseMethod, int], from_bn: str, to_bn: str):
		self.decrease(method, getBedNeedle(from_bn), getBedNeedle(to_bn))
	"""

	@multimethod
	def decreaseLeft(self, method: Union[DecreaseMethod, int], bed: Optional[str], count: int):
		method = DecreaseMethod.parse(method)
		#
		#
		min_n = self.getMinNeedle(bed)
		if math.isinf(min_n): raise RuntimeError("No more needle to decrease")
		else: assert min_n+count <= self.getMaxNeedle(bed), f"Not enough needles to decrease by {count}" #TODO: #check
		#
		if method == DecreaseMethod.DEFAULT:
			if min_n-count > self.getMaxNeedle(bed): method = DecreaseMethod.BINDOFF #check
			elif count <= self.gauge: method = DecreaseMethod.EDGE
			else: method = DecreaseMethod.SCHOOL_BUS
		#
		self.decrease(method, min_n, min_n+count, bed)

		"""
		min_n = None #for now
		bed2 = None #for now
		if bed is None: #double bed
			min_n = self.getMinNeedle()
			if math.isinf(min_n): raise RuntimeError("No more needle to decrease")
			#
			if method == DecreaseMethod.DEFAULT:
				if min_n-count > self.getMaxNeedle(): method = DecreaseMethod.BINDOFF #check
				elif count <= self.gauge: method = DecreaseMethod.EDGE
				else: method = DecreaseMethod.SCHOOL_BUS
			#
			if bnValid("f", min_n, self.gauge, mod=self.mod["f"]):
				bed = "f"
				if method == DecreaseMethod.SCHOOL_BUS or bnValid("f", min_n+count, self.gauge, mod=self.mod["f"]): bed2 = "f"
				elif bnValid("b", min_n+count, self.gauge, mod=self.mod["b"]): bed2 = "b"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
			else:
				bed = "b"
				if method == DecreaseMethod.SCHOOL_BUS or bnValid("b", min_n+count, self.gauge, mod=self.mod["b"]): bed2 = "b"
				elif bnValid("f", min_n+count, self.gauge, mod=self.mod["f"]): bed2 = "f"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
		else:
			min_n = self.getMinNeedle(bed[0])
			if math.isinf(min_n): raise RuntimeError("No more needle to decrease")
			#
			if method == DecreaseMethod.DEFAULT:
				if min_n-count > self.getMaxNeedle(bed[0]): method = DecreaseMethod.BINDOFF #check
				elif count <= self.gauge: method = DecreaseMethod.EDGE
				else: method = DecreaseMethod.SCHOOL_BUS
			#
			if method == DecreaseMethod.SCHOOL_BUS or bnValid(bed[0], min_n+count, self.gauge, mod=self.mod[bed[0]]): bed2 = bed
			else:
				bed2 = "b" if bed[0] == "f" else "f"
				if not bnValid(bed2, min_n+count, self.gauge, mod=self.mod[bed2]): raise NotImplementedError("TODO: decrease count until valid needle")
		#
		self.decrease(method, (bed, min_n), (bed2, min_n+count))
	"""

	@decreaseLeft.register
	def decreaseLeft(self, bed: Optional[str], count: int):
		self.decreaseLeft(DecreaseMethod.DEFAULT, bed, count)

	@multimethod
	def decreaseRight(self, method: Union[DecreaseMethod, int], bed: Optional[str], count: int): #TODO: add default method stuff
		method = DecreaseMethod.parse(method)
		#
		max_n = self.getMaxNeedle(bed)
		if math.isinf(max_n): raise RuntimeError("No more needle to decrease")
		else: assert max_n-count >= self.getMinNeedle(bed), f"Not enough needles to decrease by {count}" #TODO: #check
		#
		if method == DecreaseMethod.DEFAULT:
			if max_n-count < self.getMinNeedle(): method = DecreaseMethod.BINDOFF #check
			elif count <= self.gauge: method = DecreaseMethod.EDGE
			else: method = DecreaseMethod.SCHOOL_BUS
		#
		self.decrease(method, max_n, max_n-count, bed)

		"""
		max_n = None #for now
		bed2 = None #for now
		#
		if bed is None: #double bed
			max_n = self.getMaxNeedle()
			if math.isinf(max_n): raise RuntimeError("No more needle to decrease")
			#
			if method == DecreaseMethod.DEFAULT:
				if max_n-count < self.getMinNeedle(): method = DecreaseMethod.BINDOFF #check
				elif count <= self.gauge: method = DecreaseMethod.EDGE
				else: method = DecreaseMethod.SCHOOL_BUS
			#
			if bnValid("f", max_n, self.gauge, mod=self.mod["f"]):
				bed = "f"
				if method == DecreaseMethod.SCHOOL_BUS or bnValid("f", max_n-count, self.gauge, mod=self.mod["f"]): bed2 = "f"
				elif bnValid("b", max_n-count, self.gauge, mod=self.mod["b"]): bed2 = "b"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
			else:
				bed = "b"
				if method == DecreaseMethod.SCHOOL_BUS or bnValid("b", max_n-count, self.gauge, mod=self.mod["b"]): bed2 = "b"
				elif bnValid("f", max_n-count, self.gauge, mod=self.mod["f"]): bed2 = "f"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
		else:
			max_n = self.getMaxNeedle(bed[0])
			if math.isinf(max_n): raise RuntimeError("No more needle to decrease")
			#
			if method == DecreaseMethod.DEFAULT:
				if max_n-count < self.getMinNeedle(bed[0]): method = DecreaseMethod.BINDOFF #check
				elif count <= self.gauge: method = DecreaseMethod.EDGE
				else: method = DecreaseMethod.SCHOOL_BUS
			#
			if method == DecreaseMethod.SCHOOL_BUS or bnValid(bed[0], max_n-count, self.gauge, mod=self.mod[bed[0]]): bed2 = bed
			else:
				bed2 = "b" if bed[0] == "f" else "f"
				if not bnValid(bed2, max_n-count, self.gauge, mod=self.mod[bed2]): raise NotImplementedError("TODO: decrease count until valid needle")
		#
		self.decrease(method, (bed, max_n), (bed2, max_n-count))
	"""
	
	@decreaseRight.register
	def decreaseRight(self, bed: Optional[str], count: int):
		self.decreaseRight(DecreaseMethod.DEFAULT, bed, count)

	@multimethod
	def increase(self, method: Union[IncreaseMethod, int], from_bn: Tuple[str, int], to_bn: Tuple[str, int]):
		#TODO: make sure valid gauge for to_bn
		method = IncreaseMethod.parse(method) #check
		#
		if method == IncreaseMethod.CASTON or method == IncreaseMethod.SPLIT:
			min_dist = None

			for c, carrier in self.k.carrier_map.items():
				dist = abs(from_bn[1]-carrier.needle)
				if min_dist is None or dist < min_dist:
					self.active_carrier = c
					min_dist = dist
			#
			assert min_dist is not None, f"no active carriers to use for increase (using method: {method})"
		#
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
	def increaseLeft(self, method: Union[IncreaseMethod, int], bed: Optional[str], count: int):
		method = IncreaseMethod.parse(method) #check
		#
		min_n, x2n = None, None #for now
		bed2 = None #for now
		#
		if bed is None: #double bed
			min_n = self.getMinNeedle()
			if math.isinf(min_n): raise RuntimeError("No more needle to increase")
			#
			x2n = min_n-count
			#
			if method == IncreaseMethod.DEFAULT:
				if min_n+count > self.getMaxNeedle(): method = IncreaseMethod.CASTON
				elif count <= self.gauge: method = IncreaseMethod.EDGE
				else: method = IncreaseMethod.SCHOOL_BUS
			#
			#
			if bnValid("f", min_n, self.gauge, mod=self.mod["f"]):
				bed = "f"
				if method == IncreaseMethod.SCHOOL_BUS or bnValid("f", x2n, self.gauge, mod=self.mod["f"]): bed2 = "f"
				elif bnValid("b", x2n, self.gauge, mod=self.mod["b"]): bed2 = "b"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
			else:
				bed = "b"
				if method == IncreaseMethod.SCHOOL_BUS or bnValid("b", x2n, self.gauge, mod=self.mod["b"]): bed2 = "b"
				elif bnValid("f", x2n, self.gauge, mod=self.mod["f"]): bed2 = "f"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
		else:
			min_n = self.getMinNeedle(bed[0])
			if math.isinf(min_n): raise RuntimeError("No more needle to increase")
			#
			x2n = min_n-count
			#
			if method == IncreaseMethod.DEFAULT:
				if min_n+count > self.getMaxNeedle(bed[0]): method = IncreaseMethod.CASTON
				elif count <= self.gauge: method = IncreaseMethod.EDGE
				else: method = IncreaseMethod.SCHOOL_BUS
			#
			if method == IncreaseMethod.SCHOOL_BUS or bnValid(bed[0], x2n, self.gauge, mod=self.mod[bed[0]]): bed2 = bed
			else:
				bed2 = "b" if bed[0] == "f" else "f"
				if not bnValid(bed2, x2n, self.gauge, mod=self.mod[bed2]): raise NotImplementedError("TODO: decrease count until valid needle")
		#
		self.increase(method, (bed, min_n), (bed2, x2n))

	@increaseLeft.register
	def increaseLeft(self, bed: Optional[str], count: int):
		self.increaseLeft(IncreaseMethod.DEFAULT, bed, count)

	@multimethod
	def increaseRight(self, method: Union[IncreaseMethod, int], bed: Optional[str], count: int):
		method = IncreaseMethod.parse(method) #check
		#
		max_n, x2n = None, None #for now
		bed2 = None #for now
		#
		if bed is None: #double bed
			max_n = self.getMaxNeedle()
			if math.isinf(max_n): raise RuntimeError("No more needle to increase")
			#
			x2n = max_n+count
			#
			if method == IncreaseMethod.DEFAULT:
				if max_n-count < self.getMinNeedle(): method = IncreaseMethod.CASTON #TODO: #check
				elif count <= self.gauge: method = IncreaseMethod.EDGE
				else: method = IncreaseMethod.SCHOOL_BUS
			#
			if bnValid("f", max_n, self.gauge, mod=self.mod["f"]):
				bed = "f"
				if method == IncreaseMethod.SCHOOL_BUS or bnValid("f", x2n, self.gauge, mod=self.mod["f"]): bed2 = "f"
				elif bnValid("b", x2n, self.gauge, mod=self.mod["b"]): bed2 = "b"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
			else:
				bed = "b"
				if method == IncreaseMethod.SCHOOL_BUS or bnValid("b", x2n, self.gauge, mod=self.mod["b"]): bed2 = "b"
				elif bnValid("f", x2n, self.gauge, mod=self.mod["f"]): bed2 = "f"
				else: raise NotImplementedError("TODO: decrease count until valid needle")
		else:
			max_n = self.getMaxNeedle(bed[0])
			if math.isinf(max_n): raise RuntimeError("No more needle to increase")
			#
			x2n = max_n+count
			#
			if method == IncreaseMethod.DEFAULT:
				if max_n-count < self.getMinNeedle(bed[0]): method = IncreaseMethod.CASTON #TODO: #check
				elif count <= self.gauge: method = IncreaseMethod.EDGE
				else: method = IncreaseMethod.SCHOOL_BUS
			#
			if method == IncreaseMethod.SCHOOL_BUS or bnValid(bed[0], x2n, self.gauge, mod=self.mod[bed[0]]): bed2 = bed
			else:
				bed2 = "b" if bed[0] == "f" else "f"
				if not bnValid(bed2, x2n, self.gauge, mod=self.mod[bed2]): raise NotImplementedError("TODO: decrease count until valid needle")
		#
		self.increase(method, (bed, max_n), (bed2, x2n))
	
	@increaseRight.register
	def increaseRight(self, bed: Optional[str], count: int):
		self.increaseRight(IncreaseMethod.DEFAULT, bed, count)
	

#===============================================================================
