from __future__ import annotations #so we don't have to worry about situations that would require forward declarations
from typing import Optional, Union, Tuple, List
import re
# from multimethod import multimethod

from collections import UserList

#===============================================================================
import sys
from pathlib import Path

## Standalone boilerplate before relative imports
if not __package__: #remove #?
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name
#===============================================================================
    
from .ansi import Ansi, fmt


class IncList(UserList):
	def __init__(self, iterable=None):
		if iterable is not None:
			if hasattr(iterable, "__iter__") and not isinstance(iterable, str): self.increment(len(iterable))
			else: self.increment(1)
		#
		super().__init__(iterable)

	@staticmethod
	def increment(n):
		pass

	# def __setitem__(self, i, item):
	# 	self.data[i] = item

	def insert(self, i, item):
		self.increment(1)
		#
		super().insert(i, item)


	def append(self, item):
		self.increment(1)
		#
		super().append(item)

	def extend(self, other):
		self.increment(len(other))
		#
		super().extend(other)

	# def __add__(self, other): # This is for something like `IncList([1, 2, 3]) + list([4, 5, 6])`...
	# 	return super().__add__(other)

	def __iadd__(self, other): # This is for something like `l = IncList(); l += [1, 2, 3]`
		self.increment(len(other))
		#
		return super().__iadd__(other)
	
	def remove(self, item):
		self.increment(-1)
		#
		super().remove(item)

	def pop(self, i):
		self.increment(-1)
		#
		super().pop(i)


class Carrier:
	def __init__(self, direction=None, bed=None, needle=None):
		self.direction = direction
		self.bed = bed
		self.needle = needle
	#
	def update(self, direction=None, bed=None, needle=None):
		if direction is not None: self.direction = direction
		if bed is not None: self.bed = bed
		if needle is not None: self.needle = needle


def getBedNeedle(bn: str):
	res = re.match(r"^([f|b]s?)(-?\d+)$", bn)
	if res is not None:
		bed, needle = res.group(1), int(res.group(2))
		return bed, needle
	else: raise ValueError(f"'{bn}' is not a valid bed-needle string.")


def findNextValidNeedle(obj, bed: Optional[str], needle: int, d: str=None, in_limits: bool=True) -> Tuple[str, int]: #TODO: add code for in_limits=False (aka can search outside of limits with min_n and max_n)
	min_ns = {"f": obj.getMinNeedle("f"), "b": obj.getMinNeedle("b")} #NOTE: must have `getMinNeedle` and `getMaxNeedle` attributes to use this method
	max_ns = {"f": obj.getMaxNeedle("f"), "b": obj.getMaxNeedle("b")}
	if bed is not None: min_n, max_n = min_ns[bed[0]], max_ns[bed[0]]
	else: min_n, max_n = min(min_ns["f"], min_ns["b"]), max(max_ns["f"], max_ns["b"])
	#
	n_1, n1 = needle, needle
	if d is None:
		for n_1, n1 in zip(range(needle, min_n-1, -1), range(needle, max_n+1)):
			if bed != "f" and n_1 >= min_ns["b"] and not n_1 in obj.avoid_bns.get("b", []):
				return ("b", n_1)
			elif bed != "b" and n_1 >= min_ns["f"] and not n_1 in obj.avoid_bns.get("f", []):
				return ("f", n_1)
			elif bed != "b" and n1 <= max_ns["f"] and not n1 in obj.avoid_bns.get("f", []):
				return ("f", n1)
			elif bed != "f" and n1 <= max_ns["b"] and not n1 in obj.avoid_bns.get("b", []):
				return ("b", n1)
	else: assert d == "-" or d == "+"
	#
	if d == "-" or n_1 != min_n:
		for n_1 in range(n_1, min_n-1, -1):
			if bed != "f" and n_1 >= min_ns["b"] and not n_1 in obj.avoid_bns.get("b", []):
				return ("b", n_1)
			elif bed != "b" and n_1 >= min_ns["f"] and not n_1 in obj.avoid_bns.get("f", []):
				return ("f", n_1)
	#
	if d == "+" or n1 != max_n:
		for n1 in range(n1, max_n+1):
			if bed != "b" and n1 <= max_ns["f"] and not n1 in obj.avoid_bns.get("f", []):
				return ("f", n1)
			elif bed != "f" and n1 <= max_ns["b"] and not n1 in obj.avoid_bns.get("b", []):
				return ("b", n1)
	#
	return (None, None)


def rackedXfer(obj, from_bed: str, from_needle: int, to_bed: str, to_needle: int, d=None, cs=None, reset_rack: bool=True): #TODO: deal with if no sliders on machine
	ct = from_needle-to_needle
	if from_bed.startswith("f"):
		par = 1
		if to_needle in obj.avoid_bns.get("b", []): #NOTE: must have `avoid_bns` attribute to use this method
			assert to_bed != "b", f"requesting to transfer to an invalid needle, '{to_needle}' (specified as to-avoid on to_bed, '{to_bed}')"
			xto_bed = "bs"
			if to_bed is None:
				assert to_needle not in obj.avoid_bns.get("f", []), f"requesting to transfer to an invalid needle, '{to_needle}' (specified as to-avoid on both beds)"
				to_bed = "f"
		else:
			if to_bed is None:
				to_bed = "b"
				xto_bed = "b"
			elif to_bed == "bs" or to_bed.startswith("f"): xto_bed = "bs"
			else: xto_bed = "b"
	else: #startswith("b")
		par = -1
		if to_needle in obj.avoid_bns.get("f", []):
			assert to_bed != "f", f"requesting to transfer to an invalid needle, '{to_needle}' (specified as to-avoid on to_bed, '{to_bed}')"
			xto_bed = "fs"
			if to_bed is None:
				assert to_needle not in obj.avoid_bns.get("b", []), f"requesting to transfer to an invalid needle, '{to_needle}' (specified as to-avoid on both beds)"
				to_bed = "b"
		else:
			if to_bed is None:
				to_bed = "f"
				xto_bed = "f"
			elif to_bed == "fs" or to_bed.startswith("b"): xto_bed = "fs"
			else: xto_bed = "f"
	#
	obj.k.rack(par*ct)
	if cs is not None:
		assert d is not None
		obj.k.split(d, from_bed, from_needle, xto_bed, to_needle, *cs) #new #check
	else: obj.k.xfer(from_bed, from_needle, xto_bed, to_needle)
	if reset_rack: obj.k.rack(0)
	#
	# if to_bed is None: to_bed = next_bed
	#
	if xto_bed != to_bed:
		assert xto_bed[0] != to_bed[0] #sanity check
		if not reset_rack: obj.k.rack(0)
		obj.k.xfer(xto_bed, to_needle, to_bed, to_needle)


class AlreadyActiveCarrierWarning(UserWarning): #*#* #TODO: add this in
	ENABLED = True
	ERROR = False

	def __init__(self, c: str, op: str, ln: int):
		self.message = f"[@ line #{ln}] Attempting to {op} carrier '{c}', which has already been brought in."
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
		# return repr(self.message)
	
	@classmethod
	def check(self, k, warnings, carrier_map, c, op="use", line_number=None) -> bool:
		if c in carrier_map:
			if line_number is None: line_number = k.line_number
			# if self.ENABLED: k.comment(f"already active carrier warning (carrier: {c})")
			warnings.warn(AlreadyActiveCarrierWarning(c, op, line_number))
			return True
		else: return False

class InactiveCarrierWarning(UserWarning):
	ENABLED = True
	ERROR = False

	def __init__(self, c: str, op: str, ln: int):
		self.message = f"[@ line #{ln}] Attempting to {op} carrier '{c}', which hasn't been brought in yet."
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, carrier_map, c, op="use", line_number=None) -> bool:
		if c not in carrier_map:
			if line_number is None: line_number = k.line_number
			# if self.ENABLED: k.comment(f"inactive carrier warning (carrier: {c})")
			warnings.warn(InactiveCarrierWarning(c, op, line_number))
			return True
		else: return False


class UnalignedNeedlesWarning(UserWarning):
	ENABLED = True
	ERROR = False

	def __init__(self, r: int, bn: str, bn2: str, ln: str):
		self.message = f"[@ line #{ln}] '{bn}' and '{bn2}' are unaligned at rack {r}."
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, rack_value, bed, needle, bed2, needle2, line_number=None) -> bool:
		if line_number is None: line_number = k.line_number
		if bed[0] == bed2[0]:
			# if self.ENABLED: k.comment(f"unaligned needles warning: can't xfer to/from same bed ({bed}{needle} -> {bed2}{needle2})")
			print(f"can't xfer to/from to same bed ({bed} -> {bed2})")
			warnings.warn(UnalignedNeedlesWarning(rack_value, f"{bed}{needle}", f"{bed2}{needle2}", line_number))
			return True
		elif (bed[0] == "f" and needle-needle2 != rack_value) or (bed[0] == "b" and needle2-needle != rack_value):
			# if self.ENABLED: k.comment(f"unaligned needles warning: invalid rack value ({bed}{needle} -> {bed2}{needle2} at rack {rack_value})")
			warnings.warn(UnalignedNeedlesWarning(rack_value, f"{bed}{needle}", f"{bed2}{needle2}", line_number))
			return True
		else: return False


class FloatWarning(UserWarning):
	ENABLED = True
	ERROR = False
	MAX_FLOAT_LEN = 6 #TODO: add option to adjust

	def __init__(self, c: str, prev_needle: int, needle: int, ln: int):
		self.message = f"[@ line #{ln}] Float of length {abs(needle-prev_needle)} formed bringing carrier '{c}' from previous position, needle {prev_needle}, to needle {needle}." #TODO: phrase this better
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, carrier_map, c, needle, line_number=None) -> bool:
		prev_needle = carrier_map[c].needle
		if prev_needle is None or abs(needle-prev_needle) <= self.MAX_FLOAT_LEN: return False
		else:
			if line_number is None: line_number = k.line_number
			# if self.ENABLED: k.comment(f"float warning (carrier: {c}, length: {abs(needle-prev_needle)})")
			warnings.warn(FloatWarning(c, prev_needle, needle, line_number))
			return True


class StackedLoopWarning(UserWarning):
	ENABLED = True
	ERROR = False
	MAX_STACK_CT = 2

	def __init__(self, bn: str, count: int, ln: int):
		self.bn = bn
		self.count = count
		#
		self.message = f"[@ line #{ln}] {count} loops stacked on '{bn}'"
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, bn, bed, needle, MAX_STACK_CT=None, line_number=None) -> bool:
		if MAX_STACK_CT is None: MAX_STACK_CT = self.MAX_STACK_CT
		stack_ct = bn.loop_ct
		#
		if stack_ct > self.MAX_STACK_CT:
			if line_number is None: line_number = k.line_number
			# if self.ENABLED: k.comment(f"stacked loop warning ({stack_ct} on {bed}{needle})")
			warnings.warn(StackedLoopWarning(f"{bed}{needle}", stack_ct, line_number))
			return True
		else: return False


class HeldLoopWarning(UserWarning):
	ENABLED = True
	ERROR = False
	MAX_HOLD_ROWS = 10 #TODO: see what this value is on shima

	def __init__(self, bn: str, n_rows: int, ln: int):
		self.message = f"[@ line #{ln}] '{bn}' has been holding an unknit loop for {n_rows} rows." #TODO: phrase this better
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, row_ct, bn, bed, needle, line_number=None) -> bool:
		if bn is None: return False
		held_ct = max(0, row_ct-bn.current_row) #check #TODO: have current_row too #? 
		#
		if held_ct > self.MAX_HOLD_ROWS:
			if line_number is None: line_number = k.line_number
			# if self.ENABLED: k.comment(f"held loop warning ({held_ct} rows on {bed}{needle})")
			warnings.warn(HeldLoopWarning(f"{bed}{needle}", held_ct, line_number))
			return True
		else: return False


class UnstableLoopWarning(UserWarning):
	ENABLED = True
	ERROR = False

	def __init__(self, bn: str, ln: int):
		self.message = f"[@ line #{ln}] Attempting to knit on '{bn}', which does not yet have a stable loop formed." #TODO: phrase this better
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, bns, bed, needle, line_number=None) -> bool:
		raise NotImplementedError
	

class EmptyXferWarning(UserWarning):
	ENABLED = True
	ERROR = False

	def __init__(self, bn: str, ln: int):
		self.message = f"[@ line #{ln}] Attempting to xfer from '{bn}', which is empty." #TODO: phrase this better
		#
		if self.ENABLED:
			if self.ERROR: self.message = fmt(self.message, Ansi.red)
			else: self.message = fmt(self.message, Ansi.yellow)

	def __str__(self):
		return self.message
	
	@classmethod
	def check(self, k, warnings, bn, bed, needle, line_number=None) -> bool:
		if line_number is None: line_number = k.line_number
		#
		if bn is None:
			# if self.ENABLED: k.comment(f"empty xfer warning ({bed}{needle})")
			warnings.warn(EmptyXferWarning(f"{bed}{needle}", line_number))
			return True
		else:
			if bn.loop_ct > 0: return False
			else:
				# if self.ENABLED: k.comment(f"empty xfer warning ({bed}{needle})") #go back! #?
				warnings.warn(EmptyXferWarning(f"{bed}{needle}", line_number))
				return True

