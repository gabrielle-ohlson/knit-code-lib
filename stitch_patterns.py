from typing import Union, Optional, Tuple, List, Dict

from .helpers import c2cs, modsHalveGauge, bnValid, toggleDirection, bnEdges, tuckPattern, knitPass

pattern_names = ["jersey", "interlock", "rib", "seed", "garter", "tuckGarter", "tuckStitch", "altKnitTuck"]

patterns_TODO = ["moss", "bubble", "lace"]

#TODO: add `mod` param to stitch pattern functions
# --------------------------------
# --- STITCH PATTERN FUNCTIONS ---
# --------------------------------
# if doing gauge == 2, want width to be odd so *actually* have number of stitches
def jersey(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: str="f", gauge: int=1, mod={"f": None, "b": None}, bn_locs={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str:
	'''
	Jersey stitch pattern: Plain knit on specified bed

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): number of rows.
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): bed to do the knitting on. Defaults to `"f"`.
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles indices for working loops that are currently on the given bed. Value of `None` indicates we should cast-on first. Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so we need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `tuck_pattern` (bool, optional): whether to include a tuck pattern for extra security when bringing in the carrier (only applicable if `inhook` or `releasehook` == `True`). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment("begin jersey")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+":
		d1, d2 = "+", "-"
		step = 1
	else:
		d1, d2 = "-", "+"
		step = -1

	bed2 = "f" if bed == "b" else "b"

	if bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in range(start_n, end_n+step, step):
			if bnValid(bed, n, gauge, mod=mod[bed]) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed2}{n}", f"{bed}{n}")

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	if bn_locs is None: print("TODO: add caston") #debug

	for p in range(passes):
		if p % 2 == 0:
			pass_start_n = start_n
			pass_end_n = end_n
		else:
			pass_start_n = end_n
			pass_end_n = start_n

		knitPass(k, start_n=pass_start_n, end_n=pass_end_n, c=c, bed=bed, gauge=gauge, mod=mod[bed], avoid_bns=avoid_bns, init_direction=init_direction)

		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

	if xfer_bns_back and bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in range(start_n, end_n+step, step):
			if bnValid(bed, n, gauge, mod=mod[bed]) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed}{n}", f"{bed2}{n}")

	k.comment("end jersey")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2


"""
tube (single bed) example:
-------------------------
e.g. for gauge 2:
if mod == 0
"""
def interlock(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]=None, gauge: int=1, sequence: str="01", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_setup: bool=True, xfer_bns_back: bool=True, secure_start_n: bool=False, secure_end_n: bool=False, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, xfer_speed_number: Optional[int]=None, xfer_stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str: #TODO: add `xfer_bns_setup` to other stitchPattern functions
	'''
	Interlock stitch pattern: knits every other needle on alternating beds, mirroring this pattern with alternating passes. Starts on side indicated by which needle value is greater.
	In this function, passes is the number of total passes knit, so if you want an interlock segment that is 20 courses long on each bed set passes to 40.  Useful if you want to have odd passes of interlock.

	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed interlock).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): mod sequence for consecutive interlock passes (indicates whether to reverse the needle sequence we start with for interlock passes).  Valid values are "01" and "10".  This is useful for when calling this function one pass at a time, e.g., for open tubes, toggling knitting on either bed (so you might, for example, knit on the front bed and start with `passes=1, c=carrier, bed="f", gauge=2, sequence="01"`, then do a pass on the back bed, and then call `passes=1, c=carrier, bed="f", gauge=2, sequence="10"`). Otherwise, you can just ignore this.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles indices for working loops that are currently on the given bed. Value of `None` indicates we should cast-on first. Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so we will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `secure_start_n` and ...
	* `secure_end_n` are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it]).
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	assert sequence == "01" or sequence == "10", f"Invalid sequence argument, '{sequence}' (must be '01' or '10')."

	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment("begin interlock")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+": #first pass is pos
		d1, d2 = "+", "-"
		left_n = start_n
		right_n = end_n
		seq1_idx, seq2_idx = int(sequence[1]), int(sequence[0])
		# if reverse_seq: seq1_idx, seq2_idx = 0, 1
		# else: seq1_idx, seq2_idx = 1, 0 #this ensures that if `passes=1` (e.g., when knitting open tubes and switching between beds), we are still toggling which sequence we start with for the first pass in the function
	else: #first pass is neg
		d1, d2 = "-", "+"
		left_n = end_n
		right_n = start_n
		seq1_idx, seq2_idx = int(sequence[0]), int(sequence[1])
		# if reverse_seq: seq1_idx, seq2_idx = 1, 0
		# else: seq1_idx, seq2_idx = 0, 1

	if bed is None:
		# single_bed = False
		bed1, bed2 = "f", "b"

		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {"f": [n for n in range(left_n, right_n+1) if bnValid("f", n, gauge) and n not in avoid_bns.get("f", [])], "b": [n for n in range(left_n, right_n+1) if bnValid("b", n, gauge) and n not in avoid_bns.get("b", [])]}
		else: _bn_locs = bn_locs.copy() #internal version, so not modifying arg
	else:
		# single_bed = True
		if bed == "f": bed1, bed2 = "f", "b"
		else: bed1, bed2 = "b", "f"

		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {bed1: [n for n in range(left_n, right_n+1) if bnValid(bed1, n, gauge) and n not in avoid_bns[bed1]]}
		else: _bn_locs = bn_locs.copy() #internal version, so not modifying arg

	secure_needles = {"f": [], "b": []}

	edge_bns = bnEdges(left_n, right_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)

	if d1 == "+": #first pass is pos
		if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	else: #first pass is neg
		if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
		
	mods2 = modsHalveGauge(gauge, bed1)

	n_ranges = {"+": range(left_n, right_n+1), "-": range(right_n, left_n-1, -1)}

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	if bn_locs is None: print("TODO: add caston") #debug

	if xfer_bns_setup and gauge != 1: #TODO: #check
		# transfer to get loops in place:
		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)
		
		for n in range(left_n, right_n+1):
			if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed1]: continue
			elif n % (gauge*2) == mods2[1] and n in _bn_locs[bed1]: k.xfer(f"{bed1}{n}", f"{bed2}{n}")
		
		# reset settings
		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)


	if bed is not None and gauge != 1: #new #check (TODO: have option of single vs double bed #?)
		mods4 = [modsHalveGauge(gauge*2, mods2[0]), modsHalveGauge(gauge*2, mods2[1])]

		"""
		# transfer to get loops in place:
		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

		for n in range(left_n, right_n+1):
			if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed1]: continue
			elif n % (gauge*2) == mods2[1] and n in _bn_locs[bed1]: k.xfer(f"{bed1}{n}", f"{bed2}{n}")
		
		# reset settings
		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)
		"""

		def passSequence1(d):
			for n in n_ranges[d]:
				if n % (gauge*4) == mods4[0][seq1_idx] and n not in avoid_bns[bed1]: k.knit(d, f"{bed1}{n}", *cs)
				elif n % (gauge*4) == mods4[1][seq1_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
				elif n == n_ranges[d][-1]: k.miss(d, f"{bed1}{n}", *cs)

		def passSequence2(d):
			for n in n_ranges[d]:
				if n % (gauge*4) == mods4[0][seq2_idx] and n not in avoid_bns[bed1]: k.knit(d, f"{bed1}{n}", *cs)
				elif n % (gauge*4) == mods4[1][seq2_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
				elif n == n_ranges[d][-1]: k.miss(d, f"{bed1}{n}", *cs)
	else:
		def passSequence1(d):
			for n in n_ranges[d]:
				if n % (gauge*2) == mods2[seq1_idx] and n not in avoid_bns[bed1]: k.knit(d, f"{bed1}{n}", *cs)
				elif n % (gauge*2) == mods2[seq2_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
				elif n == n_ranges[d][-1]: k.miss(d, f"{bed1}{n}", *cs)
		
		def passSequence2(d):
			for n in n_ranges[d]:
				if n % (gauge*2) == mods2[seq2_idx] and n not in avoid_bns[bed1]: k.knit(d, f"{bed1}{n}", *cs)
				elif n % (gauge*2) == mods2[seq1_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
				elif n == n_ranges[d][-1]: k.miss(d, f"{bed1}{n}", *cs)

	#--- the knitting ---
	for p in range(passes):
		if p % 2 == 0: passSequence1(d1)
		else: passSequence2(d2)

		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it


	# return the loops back
	if xfer_bns_back:
		if bed is not None:
			if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
			if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

			if gauge == 1: #TODO: #check
				for n in range(left_n, right_n+1):
					if avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed1] or not bnValid(bed1, n, gauge): continue
					elif n not in _bn_locs[bed2]: k.xfer(f"{bed2}{n}", f"{bed1}{n}")
			else:
				for n in range(left_n, right_n+1):
					if avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed1] or not bnValid(bed1, n, gauge): continue
					elif n % (gauge*2) == mods2[1] and n in _bn_locs[bed1]: k.xfer(f"{bed2}{n}", f"{bed1}{n}") #TODO: #check
					# elif n % (gauge*2) == mods2[1]: k.xfer(f"{bed2}{n}", f"{bed1}{n}")
			
			# reset settings
			if speed_number is not None: k.speedNumber(speed_number)
			if stitch_number is not None: k.stitchNumber(stitch_number)
		elif bn_locs is not None and (len(bn_locs.get("f", [])) or len(bn_locs.get("b", []))):
			if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
			if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

			for n in range(left_n, right_n+1):
				if avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed1] or not bnValid(bed1, n, gauge): continue
				elif n not in bn_locs.get("f", []) and n in bn_locs.get("b", []): k.xfer(f"f{n}", f"b{n}")
				elif n not in bn_locs.get("b", []) and n in bn_locs.get("f", []): k.xfer(f"b{n}", f"f{n}")
				elif n not in bn_locs.get("f", []) and n not in bn_locs.get("b", []): raise ValueError("TODO: handle this situation")
			
			# reset settings
			if speed_number is not None: k.speedNumber(speed_number)
			if stitch_number is not None: k.stitchNumber(stitch_number)

	k.comment("end interlock")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2


def rib(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]=None, gauge: int=1, sequence: str="fb", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, secure_start_n: bool=False, secure_end_n: bool=False, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, xfer_speed_number: Optional[int]=None, xfer_stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str: #TODO: #check to make sure this is working well for gauge > 1 #*
	'''
	Rib stitch pattern: alternates between front and back bed in a row based on given sequence.

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed rib; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating needle-wise between front and back bed in a pass (e.g. "fb" of "bf" for 1x1, "ffbb" for 2x2, "fbffbb" for 1x1x2x2, etc.). Defaults to `"fb"`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles indices for working loops that are currently on the given bed. Value of `None` indicates we should cast-on first. Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so we will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `secure_start_n` and ...
	* `secure_end_n` are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it]).
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).


	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment(f"begin rib ({sequence})")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if gauge > 1:
		gauged_sequence = ""
		for char in sequence:
			gauged_sequence += char * gauge
		sequence = gauged_sequence
	
	if end_n > start_n or init_direction == "+": #first pass is pos
		d1 = "+"
		d2 = "-"
		n_ranges = {d1: range(start_n, end_n+1), d2: range(end_n, start_n-1, -1)}
	else: #first pass is neg
		d1 = "-"
		d2 = "+"
		n_ranges = {d1: range(start_n, end_n-1, -1), d2: range(end_n, start_n+1)}
	
	if bed is None:
		bed1, bed2 = "f", "b"
		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {"f": [n for n in n_ranges[d1] if bnValid("f", n, gauge)], "b": [n for n in n_ranges[d1] if bnValid("b", n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()
	else:
		if bed == "f": bed1, bed2 = "f", "b"
		else: bed1, bed2 = "b", "f"
		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {bed1: [n for n in n_ranges[d1] if bnValid(bed1, n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()

	secure_needles = {"f": [], "b": []}

	if d1 == "+": #first pass is pos
		edge_bns = bnEdges(start_n, end_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	else: #first pass is neg
		edge_bns = bnEdges(end_n, start_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

	# now let's make sure we have *all* the info in one dict
	xfer_bns = {"f": [n for n in _bn_locs.get("f", []) if sequence[n % len(sequence)] == "b" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["f"]], "b": [n for n in _bn_locs.get("b", []) if sequence[n % len(sequence)] == "f" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["b"]]}
	# xfer_bns = {"f": [n for n in list(set(_bn_locs.get("f", [])+bn_locs.get("f", []))) if sequence[n % len(sequence)] == "b" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["f"]], "b": [n for n in list(set(_bn_locs.get("b", [])+bn_locs.get("b", []))) if sequence[n % len(sequence)] == "f" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["b"]]}

	if len(xfer_bns["f"]) or len(xfer_bns["b"]): # indicates that we might need to start by xferring to proper spots
		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

		for n in n_ranges[d1]: #TODO: #check adjustment for gauge
			if n in xfer_bns["f"]: k.xfer(f"f{n}", f"b{n}")
			elif n in xfer_bns["b"]: k.xfer(f"b{n}", f"f{n}")

		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)
	
	if bn_locs is None: print("TODO: add caston") #debug

	#TODO: maybe change stitch size for rib? k.stitchNumber(math.ceil(specs.stitchNumber/2)) (if so -- remember to reset settings)
	for p in range(passes):
		if p % 2 == 0:
			d = d1
			last_n = end_n
		else:
			d = d2
			last_n = start_n

		for n in n_ranges[d]:
			if n in secure_needles["f"] and n not in _bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
			elif n in secure_needles["b"] and n not in _bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
			elif sequence[n % len(sequence)] == "f" and n not in avoid_bns.get("f", []) and bnValid(bed1, n, gauge): k.knit(d, f"f{n}", *cs) #xferred it or bed1 == "f", ok to knit
			elif sequence[n % len(sequence)] == "b" and n not in avoid_bns.get("b", []) and bnValid(bed1, n, gauge): k.knit(d, f"b{n}", *cs) #xferred it or bed1 == "b", ok to knit
			elif n == last_n: k.miss(d, f"f{n}", *cs)

		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

	# return the loops:
	if xfer_bns_back and (len(xfer_bns["f"]) or len(xfer_bns["b"])):
		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

		for n in n_ranges[d1]:
			if n in xfer_bns["f"]: k.xfer(f"b{n}", f"f{n}")
			elif n in xfer_bns["b"]: k.xfer(f"f{n}", f"b{n}")
			
		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)

	k.comment("end rib")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2


def seed(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]="f", gauge: int=1, sequence: str="fb", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, secure_start_n=True, secure_end_n=True, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, xfer_speed_number: Optional[int]=None, xfer_stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str:
	'''
	Seed stitch pattern: alternates bes needle-wise based on specified sequence, mirroring the sequence pass-wise.

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed garter; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating needle-wise between passes of knits on front and back bed. Defaults to `"fb"`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles that are currently on the given bed (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): *TODO: add code for this* whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `secure_start_n` and ...
	* `secure_end_n` are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it]).
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment(f"begin seed ({sequence})")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+": #first pass is pos
		d1, d2 = "+", "-"
		n_ranges = {d1: range(start_n, end_n+1), d2: range(end_n, start_n-1, -1)}
	else: #first pass is neg
		d1, d2 = "-", "+"
		n_ranges = {d1: range(start_n, end_n-1, -1), d2: range(end_n, start_n+1)}
	
	if bed is None:
		bed1, bed2 = "f", "b"
		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {"f": [n for n in n_ranges[d1] if bnValid("f", n, gauge)], "b": [n for n in n_ranges[d1] if bnValid("b", n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()
	else:
		if bed == "f": bed1, bed2 = "f", "b"
		else: bed1, bed2 = "b", "f"
		if bn_locs is None or (not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", []))): _bn_locs = {bed1: [n for n in n_ranges[d1] if bnValid(bed1, n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()

	# if bed is not None: _bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check
	# else: _bn_locs = bn_locs.copy()

	if gauge > 1:
		gauged_sequence = ""
		for char in sequence:
			gauged_sequence += char * gauge
		sequence = gauged_sequence

	secure_needles = {"f": [], "b": []}

	if d1 == "+": #first pass is pos
		edge_bns = bnEdges(start_n, end_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	else: #first pass is neg
		edge_bns = bnEdges(end_n, start_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

	xfer_bns = {"f": [n for n in _bn_locs.get("f", []) if sequence[n % len(sequence)] == "b" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["f"]], "b": [n for n in _bn_locs.get("b", []) if sequence[n % len(sequence)] == "f" and bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["b"]]}

	if len(xfer_bns["f"]) or len(xfer_bns["b"]): # indicates that we might need to start by xferring to proper spots
		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

		for n in n_ranges[d1]:
			if n in xfer_bns["f"]: k.xfer(f"f{n}", f"b{n}")
			elif n in xfer_bns["b"]: k.xfer(f"b{n}", f"f{n}")
			
		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	for p in range(passes):
		if p % 2 == 0:
			d = d1
			last_n = end_n

			for n in n_ranges[d]:
				if bnValid(bed1, n, gauge):
					if n in secure_needles["f"] and n not in _bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
					elif n in secure_needles["b"] and n not in _bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
					else:
						if n not in avoid_bns.get("f", []) and (sequence[n % len(sequence)] == "f" or (sequence[n % len(sequence)] == "b" and n in avoid_bns.get("b", []))): k.knit(d, f"f{n}", *cs) #xferred it or bed1 == "f", ok to knit
						elif n not in avoid_bns.get("b", []) and (sequence[n % len(sequence)] == "b" or (sequence[n % len(sequence)] == "f" and n in avoid_bns.get("f", []))): k.knit(d, f"b{n}", *cs) #xferred it or bed1 == "b", ok to knit
						elif n == last_n: k.miss(d, f"f{n}", *cs)
				elif n == last_n: k.miss(d, f"f{n}", *cs)
			
			if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
			if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

			if p < passes-1:
				for n in n_ranges[d]:
					if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
					elif bnValid(bed1, n, gauge):
						if sequence[n % len(sequence)] == "f" and n not in secure_needles["f"]: k.xfer(f"f{n}", f"b{n}")
						elif sequence[n % len(sequence)] == "b" and n not in secure_needles["b"]: k.xfer(f"b{n}", f"f{n}")
			elif xfer_bns_back:
				# return the loops:
				for n in n_ranges[d]:
					if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles["f"] or n in secure_needles["b"]: continue
					elif bnValid(bed1, n, gauge):
						if sequence[n % len(sequence)] == "f" and n in xfer_bns.get("b", []): k.xfer(f"f{n}", f"b{n}")
						elif sequence[n % len(sequence)] == "b" and n in xfer_bns.get("f", []): k.xfer(f"b{n}", f"f{n}")

			if speed_number is not None: k.speedNumber(speed_number)
			if stitch_number is not None: k.stitchNumber(stitch_number)
		else:
			d = d2
			last_n = start_n

			for n in n_ranges[d]:
				if bnValid(bed1, n, gauge):
					if n in secure_needles["f"] and n not in _bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
					elif n in secure_needles["b"] and n not in _bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
					else:
						if n not in avoid_bns.get("b", []) and (sequence[n % len(sequence)] == "f" or (sequence[n % len(sequence)] == "b" and n in avoid_bns.get("f", []))): k.knit(d, f"b{n}", *cs) #xferred it or bed1 == "f", ok to knit
						elif n not in avoid_bns.get("f", []) and (sequence[n % len(sequence)] == "b" or (sequence[n % len(sequence)] == "f" and n in avoid_bns.get("b", []))): k.knit(d, f"f{n}", *cs) #xferred it or bed1 == "b", ok to knit
						elif n == last_n: k.miss(d, f"f{n}", *cs)
				elif n == last_n: k.miss(d, f"f{n}", *cs)

			if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
			if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)

			if p < passes-1:
				for n in n_ranges[d]:
					if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
					elif n not in secure_needles and bnValid(bed1, n, gauge):
						if sequence[n % len(sequence)] == "f": k.xfer(f"b{n}", f"f{n}")
						else: k.xfer(f"f{n}", f"b{n}")
			elif xfer_bns_back:
				# return the loops:
				for n in n_ranges[d]: #TODO: adjust for gauge
					if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles["f"] or n in secure_needles["b"]: continue
					elif bnValid(bed1, n, gauge):
						if sequence[n % len(sequence)] == "f" and n in xfer_bns.get("f", []): k.xfer(f"b{n}", f"f{n}")
						elif sequence[n % len(sequence)] == "b" and n in xfer_bns.get("b", []): k.xfer(f"f{n}", f"b{n}")
			
			if speed_number is not None: k.speedNumber(speed_number)
			if stitch_number is not None: k.stitchNumber(stitch_number)
		
		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

	k.comment(f"end seed ({sequence})")

	# return next direction
	if bnValid(bed1, n, gauge) % 2 == 0: #TODO: #check
		if end_n > start_n: return "+"
		else: return "-"
	else:
		if end_n > start_n: return "-"
		else: return "+"


def garter(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]=None, gauge: int=1, sequence: str="fb", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, secure_start_n=True, secure_end_n=True, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, xfer_speed_number: Optional[int]=None, xfer_stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str:
	'''
	Garter stitch pattern: alternates between beds pass-wise.

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed garter; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating length-wise between passes of knits on front and back bed. Defaults to `"fb"`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles that are currently on the given bed (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `secure_start_n` and ...
	* `secure_end_n` are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it]).
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	pattern_rows = {"f": sequence.count("f"), "b": sequence.count("b")}

	k.comment(f"begin {pattern_rows['f']}x{pattern_rows['b']} garter")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+": #first pass is pos
		d1, d2 = "+", "-"
		n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}
	else: #first pass is neg
		d1, d2 = "-", "+"
		n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

	if bed is None:
		bed1, bed2 = "f", "b"
		if not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])):
			_bn_locs = {"f": [n for n in n_ranges[d1] if bnValid("f", n, gauge)], "b": [n for n in n_ranges[d1] if bnValid("b", n, gauge)]} #assume loops on both beds
		else: _bn_locs = bn_locs.copy()
	else:
		if bed == "f": bed1, bed2 = "f", "b"
		else: bed1, bed2 = "b", "f"
		if not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])): _bn_locs = {bed1: [n for n in n_ranges[d1] if bnValid(bed1, n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()

	# if bed is not None: _bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check
	# else: _bn_locs = bn_locs.copy()

	secure_needles = {"f": [], "b": []}

	if d1 == "+": #first pass is pos
		edge_bns = bnEdges(start_n, end_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	else: #first pass is neg
		edge_bns = bnEdges(end_n, start_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	
	# for now: (will be reset)
	d = d1

	if type(pattern_rows) != dict:
		pat_rows = {}
		pat_rows["f"] = pattern_rows
		pat_rows["b"] = pattern_rows
		pattern_rows = pat_rows
	
	b1 = sequence[0]
	b2 = "f" if b1 == "b" else "b"

	xfer_bns = {b2: [n for n in _bn_locs.get(b2, []) if bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles[b2]]}
	# xfer_bns = {b2: [n for n in list(set(_bn_locs.get(b2, [])+bn_locs.get(b2, []))) if bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles[b2]]}

	if len(xfer_bns[b2]):
		for n in n_ranges[d2]:
			if n in xfer_bns[b2]: k.xfer(f"{b2}{n}", f"{b1}{n}")
	
	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	for p in range(passes):
		if p % 2 == 0: d = d1
		else: d = d2

		if p > 0 and b1 != sequence[p % len(sequence)]: # transfer
			if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
			if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)
			
			for n in n_ranges[d]:
				if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
				elif bnValid(bed1, n, gauge) and n not in secure_needles[b1]: k.xfer(f"{b1}{n}", f"{sequence[p % len(sequence)]}{n}")

			if speed_number is not None: k.speedNumber(speed_number)
			if stitch_number is not None: k.stitchNumber(stitch_number)

		b1 = sequence[p % len(sequence)]
		b2 = "f" if b1 == "b" else "b"

		for n in n_ranges[d]:
			if bnValid(bed1, n, gauge):
				if n in secure_needles[b2] or (n in avoid_bns[b1] and n not in avoid_bns[b2]): k.knit(d, f"{b2}{n}", *cs)
				elif n not in avoid_bns[b1]: k.knit(d, f"{b1}{n}", *cs)
				elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
			elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
		
		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
	
	#return loops
	b2 = "f" if b1 == "b" else "b"
	if xfer_bns_back and len(xfer_bns.get(b2, [])):
		for n in n_ranges[d]:
			if n in xfer_bns[b2]: k.xfer(f"{b1}{n}", f"{b2}{n}")

	if type(pattern_rows) == dict: k.comment(f"end {pattern_rows['f']}x{pattern_rows['b']} garter")
	else: k.comment(f"end {pattern_rows}x{pattern_rows} garter")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2
	# return "-" if d == "+" else "+"


def tuckGarter(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]="f", gauge: int=1, sequence: str="ffb", tuck_sequence: str="tk", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, secure_start_n: bool=False, secure_end_n: bool=False, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, xfer_speed_number: Optional[int]=None, xfer_stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str: #TODO: fix this for gauge 2 secure needles
	'''
	Garter with tucks on every other needle after first pass in repeated sequence.

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed garter; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating length-wise between passes of knits on front and back bed. Defaults to `"ffb"`.
	* `tuck_sequence` (str, optional): repeating stitch pattern sequence for alternating needle-wise between knitting and tucking. (Will mirror this pattern in alternating passes).  Defaults to `"tk"`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles that are currently on the given bed (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): *TODO: add code for this* whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `secure_start_n` and ...
	* `secure_end_n` are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it]).
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	pattern_rows = {"f": sequence.count("f"), "b": sequence.count("b")}

	if type(pattern_rows) == dict: k.comment(f"begin {pattern_rows['f']}x{pattern_rows['b']} garter with tucks")
	else: k.comment(f"begin {pattern_rows}x{pattern_rows} garter with tucks")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+": #first pass is pos
		d1, d2 = "+", "-"
		n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}
	else:
		d1, d2 = "-", "+"
		n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

	if bed is None:
		bed1, bed2 = "f", "b"
		if not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])):
			_bn_locs = {"f": [n for n in n_ranges[d1] if bnValid("f", n, gauge)], "b": [n for n in n_ranges[d1] if bnValid("b", n, gauge)]} #assume loops on both beds
		else: _bn_locs = bn_locs.copy()
	else:
		if bed == "f": bed1, bed2 = "f", "b"
		else: bed1, bed2 = "b", "f"
		if not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])): _bn_locs = {bed1: [n for n in n_ranges[d1] if bnValid(bed1, n, gauge)]} #make sure we transfer to get them where we want #TODO: #check
		else: _bn_locs = bn_locs.copy()

	secure_needles = {"f": [], "b": []}

	if d1 == "+": #first pass is pos
		edge_bns = bnEdges(start_n, end_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
	else: #first pass is neg
		edge_bns = bnEdges(end_n, start_n, gauge, bn_locs=_bn_locs, avoid_bns=avoid_bns, return_type=list)
		if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
		if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

	# for now: (will be reset)
	d = d1

	if type(pattern_rows) != dict:
		pat_rows = {"f": pattern_rows, "b": pattern_rows}
		pattern_rows = pat_rows
	
	b1 = sequence[0]
	b2 = "f" if b1 == "b" else "b"

	pattern_rows[b1] += 1 #for the tucks

	xfer_bns = {b2: [n for n in _bn_locs.get(b2, []) if bnValid(bed1, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles[b2]]}

	if len(xfer_bns[b2]):
		for n in n_ranges[d2]:
			if n in xfer_bns.get(b2, []): k.xfer(f"{b2}{n}", f"{b1}{n}")

	mods2 = modsHalveGauge(gauge, bed1)

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	pass_ct = 0
	for p in range(passes):
		if p > 0: b1, b2 = b2, b1 #toggle

		for r in range(pattern_rows[b1]):
			if b1 == sequence[0] and tuck_sequence[r % len(tuck_sequence)] == "t": # r == 0:
				for n in n_ranges[d]:
					if n not in avoid_bns.get(b1, []) and n % (gauge*2) == mods2[0] and n != edge_bns[0][1] and n != edge_bns[1][1]: k.tuck(d, f"{b1}{n}", *cs)
					elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
			else:
				for n in n_ranges[d]:
					if bnValid(bed1, n, gauge):
						if n in secure_needles[b2] or (n in avoid_bns.get(b1, []) and n not in avoid_bns.get(b2, [])): k.knit(d, f"{b2}{n}", *cs)
						elif n not in avoid_bns.get(b1, []): k.knit(d, f"{b1}{n}", *cs)
						elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
					elif n == end_n: k.miss(d, f"{b1}{n}", *cs)

			d = toggleDirection(d)

			if pass_ct == rh_p:
				k.releasehook(*cs)
				if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

			pass_ct += 1
			if pass_ct == passes: break

		if pass_ct == passes and b1 == bed1: break #don't need to return it

		if xfer_speed_number is not None: k.speedNumber(xfer_speed_number)
		if xfer_stitch_number is not None: k.stitchNumber(xfer_stitch_number)
			
		for n in n_ranges[d]:
			if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles.get("f", []) or n in secure_needles.get("b", []) or not bnValid(bed1, n, gauge): continue
			elif n in _bn_locs.get(bed2, []): k.xfer(f"{bed1}{n}", f"{bed2}{n}") #TODO: #check
			else: k.xfer(f"{b1}{n}", f"{b2}{n}")

		if speed_number is not None: k.speedNumber(speed_number)
		if stitch_number is not None: k.stitchNumber(stitch_number)

		if pass_ct == passes: break

	if type(pattern_rows) == dict: k.comment(f"end {pattern_rows['f']-1}x{pattern_rows['b']} garter with tucks")
	else: k.comment(f"end {pattern_rows}x{pattern_rows} garter with tucks")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2


def tuckStitch(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]="f", gauge: int=1, sequence: str="kt", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str:
	'''TODO
	_summary_

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed rib; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating needle-wise between knitting and tucking. (Will mirror this pattern in alternating passes).  Defaults to `"kt"`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles indices for working loops that are currently on the given bed. Value of `None` indicates we should cast-on first. Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so we will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''

	# if releasehook and not tuck_pattern and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment(f"begin tuck stitch ({sequence})")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+":
		d1, d2 = "+", "-"
		n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}
	else:
		d1, d2 = "-", "+"
		n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

	edge_bns = bnEdges(n_ranges["+"][0], n_ranges["+"][-1], gauge, bn_locs={bed: [n for n in n_ranges["+"] if bnValid(bed, n, gauge)]}, avoid_bns=avoid_bns, return_type=list)
	
	if gauge > 1:
		gauged_sequence = ""
		for char in sequence:
			gauged_sequence += char*gauge
		sequence = gauged_sequence
	
	bed2 = "f" if bed == "b" else "b"

	if bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in n_ranges[d2]:
			if bnValid(bed, n, gauge) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed2}{n}", f"{bed}{n}")

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

	for p in range(passes):
		if p % 2 == 0:
			do_knit = "k"
			d = d1
			pass_start_n = start_n
			pass_end_n = end_n
		else:
			do_knit = "t"
			d = d2
			pass_start_n = end_n
			pass_end_n = start_n

		for n in n_ranges[d]:
			if bnValid(bed, n, gauge) and n not in avoid_bns[bed]: # and (n % (gauge*2) == mods2[0] or n % (gauge*2) == mods2[1]):
				if sequence[n % len(sequence)] == do_knit or n == edge_bns[0][1] or n == edge_bns[1][1]: k.knit(d, f"{bed}{n}", *cs)
				else: k.tuck(d, f"{bed}{n}", *cs)
			elif n == pass_end_n: k.miss(d, f"{bed}{n}", *cs)

		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
	
	if xfer_bns_back and bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in n_ranges[toggleDirection(d)]:
			if bnValid(bed, n, gauge) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed}{n}", f"{bed2}{n}")

	k.comment("end tuck stitch")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2
	# if pass_end_n > pass_start_n: return "-" #just knit a pos pass
	# else: return "+"



def altKnitTuck(k, start_n: int, end_n: int, passes: int, c: Union[str, Tuple[str], List[str]], bed: Optional[str]="f", gauge: int=1, sequence: str="kt", tuck_sequence: str="mt", bn_locs: Dict[str,List[int]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, xfer_bns_back: bool=True, inhook: bool=False, releasehook: bool=False, tuck_pattern: bool=True, speed_number: Optional[int]=None, stitch_number: Optional[int]=None, init_direction: Optional[str]=None) -> str:
	'''TODO
	_summary_

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the primary bed, that the loops are on, or belong to if knitting a single-bed variation (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed rib; will by default gauge based on front bed, aka `n % gauge == 0`).
	* `sequence` (str, optional): repeating stitch pattern sequence for alternating length-wise between passes of knits and tucks. Defaults to `"kt"`.
	* `tuck_sequence` (str, optional): TODO. Defaults to `"mt"`.
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `bn_locs` (dict, optional): dict with bed as keys and values as list of needles indices for working loops that are currently on the given bed. Value of `None` indicates we should cast-on first. Defaults to `{"f": [], "b": []}` (aka assume loops are on the specified `bed`, and if `bed is None`, assume loops are on both beds to start so we will likely need to transfer them to get them in place for the stitch pattern).
	* `avoid_bns` (dict, optional): dict with bed as keys and values as list of needles that should stay empty (aka avoid knitting on). Defaults to `{"f": [], "b": []}` (aka don't avoid any needles outside of gauging).
	* `xfer_bns_back` (bool, optional): whether to return loops back to their specified locations in `bn_locs` after knitting (NOTE: not applicable if `bn_locs` is None or empty lists). Defaults to `True`.
	* `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
	* `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
	* `speed_number` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
	* `stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
	* `xfer_speed_number` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
	* `xfer_stitch_number` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
	* `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).

	Raises:
	------
	* ValueError: if `releasehook` and `passes < 2` and `tuck_pattern = False`.

	Returns:
	-------
	* direction (str): next direction to knit in.
	'''
	if releasehook:
		if passes < 2:
			if not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes. Try adding a tuck pattern.")
			else: rh_p = 0
		else: rh_p = 1
	else: rh_p = -1

	cs = c2cs(c) # ensure tuple type

	k.comment(f"begin alt knit/tuck ({sequence})")

	if speed_number is not None: k.speedNumber(speed_number)
	if stitch_number is not None: k.stitchNumber(stitch_number)

	if end_n > start_n or init_direction == "+":
		d1, d2 = "+", "-"
		step = 1
	else:
		d1, d2 = "-", "+"
		step = -1

	mods2 = modsHalveGauge(gauge, bed)

	bed2 = "f" if bed == "b" else "b"

	if bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in range(start_n, end_n+step, step):
			if bnValid(bed, n, gauge) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed2}{n}", f"{bed}{n}")

	if inhook:
		k.inhook(*cs)
		if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs) #TODO: add avoid bns to `tuckPattern` func

	for p in range(passes):
		if p % 2 == 0:
			pass_start_n = start_n
			pass_end_n = end_n
		else:
			pass_start_n = end_n
			pass_end_n = start_n
		if sequence[p % len(sequence)] == "k":
			knitPass(k, start_n=pass_start_n, end_n=pass_end_n, c=c, bed=bed, gauge=gauge)
		else:
			if pass_end_n > pass_start_n: #pass is pos
				for n in range(pass_start_n, pass_end_n+1):
					if n == pass_end_n and bnValid(bed, n, gauge): k.miss("+", f"{bed}{n}", *cs) #don't tuck on last needle since we're going to turn around and knit on it
					elif n % (gauge*2) == mods2[0] and n not in avoid_bns[bed]: k.tuck("+", f"{bed}{n}", *cs)
					elif n == pass_end_n: k.miss("+", f"{bed}{n}", *cs)
			else: #pass is neg
				for n in range(pass_start_n, pass_end_n-1, -1):
					if n == pass_end_n and bnValid(bed, n, gauge): k.miss("-", f"{bed}{n}", *cs) #don't tuck on last needle since we're going to turn around and knit on it
					elif n % (gauge*2) == mods2[1] and n not in avoid_bns[bed]: k.tuck("-", f"{bed}{n}", *cs)
					elif n == pass_end_n: k.miss("-", f"{bed}{n}", *cs)

		if p == rh_p:
			k.releasehook(*cs)
			if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

	if xfer_bns_back and bn_locs is not None and len(bn_locs.get(bed2, [])):
		for n in range(start_n, end_n+step, step):
			if bnValid(bed, n, gauge) and n in bn_locs[bed2] and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
				k.xfer(f"{bed}{n}", f"{bed2}{n}")

	k.comment(f"end alt knit/tuck ({sequence})")

	# return next direction:
	if passes % 2 == 0: return d1
	else: return d2
