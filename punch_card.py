import numpy as np
import cv2
# import matplotlib.pyplot as plt

from .helpers import c2cs, toggleDirection, tuckPattern, flattenIter, bnValid, bnEdges

TUCK = 0 # punch card: tuck on non-punched (white) pixels
FAIRISLE = 1 # punch card: knit color 2 on punched (black) pixels
SLIP = 2 # punch card: miss on non-punched (white) pixels
LACE = 3 # punch card: xfer on punched (black) pixels TODO
# WEAVE = 4 # punch card: TODO


AMISS_INTERVAL = 2
MAX_FLOAT_WIDTH = 5


# The punched hole is the design stitch, with one exception. For tuck stitch it is the UNPUNCHED hole which tucks, so all the other spaces have to be punched (it was what drove me to buy electronic machines).

# needles forward knit next row and needles back tuck

# The punch card holes will be the contrast color in Fair-isle - the top secondary yarn when weaving - the transferred stitch when knitting lace.
# The punch card holes will be the plain knit stitch when knitting Tuck - and the plain knit stitch when knitting slip/skip.


def generate(k, start_n, end_n, passes, c, bed, img_path, punch_card_width=24, punch_card_height=None, setting=TUCK, c2=None, color_change_mod=None, gauge=1, gauge_data=False, validate_setting=False, inhook_carriers=[], outhook_carriers=[], add_amiss=False):
	'''
	Function to emulate a punch card for a domestic knitting machine on an industrial machine (programmed with knitout) using a binary (black and white) image.

	Parameters:
	----------
	* `k` (class instance): instance of the knitout Writer class.
	* `start_n` (int): the initial needle to knit on in a pass.
	* `end_n` (int): the last needle to knit on in a pass (inclusive).
	* `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
	* `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
	* `bed` (str, optional): the bed to knit on. Valid values are `f` or `b`.
	* `img_path` (str): path to punch card image.
	 * `punch_card_width` (int or None, optional): actual width of punch card for resizing image. Defaults to `None` (aka use image width).
	* `punch_card_height` (int or None, optional): actual height of punch card for resizing image. Defaults to `None` (aka use image height).
	* `setting` (int, optional): program constant specifying the setting to use for "punched out" sections (white pixels). Defaults to `FAIRISLE`.
	* `c2` (str or list, optional): a second carrier (or list of carriers, if plating) to use for color-work (NOTE: required if `setting == FAIRISLE or color_change_mod is not None`). Defaults to `None`.
	* `color_change_mod` (int or None, optional): indicates: "change carriers every `color_change_mod` passes". Defaults to `None`.
	* `gauge` (int, optional): gauge to knit in. Defaults to `1`.
	* `gauge_data` (bool, optional): whether to scale the punch card data to the gauge (so that each pixel is still knitted). Defaults to `False`.
	* `validate_setting` (bool, optional): whether to check to make sure setting operation followings "knitting rules." Defaults to `False`.
	* `inhook_carriers` (list, optional): carriers to `inhook` before using for the first time (NOTE: will automatically add `tuckPattern` and releasehook too). Defaults to `[]`.
	* `outhook_carriers` (list, optional): carriers to `outhook` at the end of the function. Defaults to `[]`.

	Raises:
	------
	* ValueError: if `c2 is None` and `setting == FAIRISLE or color_change_mod is not None`.

	Returns:
	-------
	* (str): next direction to knit carrier `c` in.
	* (str, optional): if `c2 is not None` --- next direction to knit carrier `c2` in.
	'''
	if setting != TUCK and setting != FAIRISLE and setting != SLIP and setting != LACE: raise ValueError(f"Unsupported setting: {setting}.  Supported settings are {TUCK} (tuck), {FAIRISLE} (fairisle), {SLIP} (slip), and {LACE} (lace).")
	#
	k.fabricPresser("auto") #new #check #TODO: determine if should always be there
	#
	#get punch card data
	img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
	#
	if punch_card_width is not None or punch_card_height is not None:
		punch_card_dims = (punch_card_width if punch_card_width is not None else img.shape[1], punch_card_height if punch_card_height is not None else img.shape[0])
		img = cv2.resize(img, punch_card_dims, interpolation=cv2.INTER_AREA)
		# if punch_card_dims is not None: img = cv2.resize(img, punch_card_dims, interpolation=cv2.INTER_AREA)
	#
	if setting == FAIRISLE or setting == LACE: ret, data = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV) #inverse so that 0 means plain knit with c
	else: ret, data = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY) # 0 means plain knit
	#
	# flip vertically so going from bottom up
	data = cv2.flip(data, 0)
	h, w = data.shape
	#
	bed2 = "b" if bed == "f" else "f"
	#
	directions = {}
	#
	if end_n > start_n: # starts pos
		d1, d2 = "+", "-"
		left_n, right_n = start_n, end_n
		step = 1
	else:
		d1, d2 = "-", "+"
		left_n, right_n = end_n, start_n
		step = -1
	#
	n_ranges = {"-": range(right_n, left_n-1, -1), "+": range(left_n, right_n+1)}
	#
	left_edge_bn, right_edge_bn = bnEdges(left_n, right_n, gauge, return_type=list)
	#
	cs = c2cs(c)
	#
	if c in inhook_carriers: directions[cs] = None
	else: directions[cs] = d1
	#
	if c2 is not None:
		cs2 = c2cs(c2)
		if c2 in inhook_carriers: directions[cs2] = None
		else: directions[cs2] = d1
	else:
		cs2 = None
		if setting == FAIRISLE: raise ValueError("Must pass an argument to 'c2' param for fairisle setting.")
		elif color_change_mod is not None: raise ValueError("Must pass an argument to 'c2' param for color changing.")
	# #remove #debug #v
	# print(data)
	# plt.imshow(data)
	# plt.show()
	# #^
	if gauge_data:
		def getData(p, n):
			return data[p%h][(n//gauge)%w] #TODO: #check
			# if gauge_height: return data[(p//gauge)%h][(n//gauge)%w]
	else:
		def getData(p, n):
			return data[p%h][n%w]
	#
	if validate_setting:
		print("TODO")
		if setting == TUCK or setting == LACE:
			def validate(p, n):
				if getData(p, n) == 0: return True #not actually a tuck
				return n != left_edge_bn[1] and n != right_edge_bn[1] and (n-gauge < left_edge_bn[1] or getData(p, n-gauge) == 0) and (n+gauge > right_edge_bn[1] or getData(p, n+gauge) == 0)
				#
				"""
				if n == left_edge_bn[1] or n == right_edge_bn[1]: return False
				if p < passes-1: #another pass is coming
					if n-gauge >= left_edge_bn[1] and getData(p, n-gauge) != 0: #tuck on both this needle and needle to the left
						if getData(p+1, n) != 0 and getData(p+1, n-gauge) != 0: return False
					#
					if n+gauge <= right_edge_bn[1] and getData(p, n+gauge) != 0: #tuck on both this needle and needle to the right
						if getData(p+1, n) != 0 and getData(p+1, n-gauge) != 0: return False
				else: return (n-gauge <= left_edge_bn[1] or getData(p, n-gauge) == 0) and (n+gauge >= right_edge_bn[1] or getData(p, n+gauge) == 0) #TODO: maybe have a system to allow some tucks, but just converting it to valid 
				"""
		else:
			def validate(p, n):
				if getData(p, n) == 0: return True #not actually a slip/c2
				#
				print("TODO")
				# kns = np.where(data[p%h] == 0)
				# if n-gauge < left_edge_bn[1]: left_kn = left_edge_bn[1]
				# else: left_kn = np.where(data[p%h][:n%w] == 0)
	else:
		validate = lambda p, n: True

	#
	do_releasehook = False
	#
	for p in range(passes):
		row = data[p%h] #TODO: #check
		#
		if directions[cs] is None: #inhook
			k.inhook(*cs)
			tuckPattern(k, first_n=start_n, direction=d1, c=cs)
			# tuckPattern(k, first_n=left_n if d1 == "+" else right_n, direction=d1, c=cs)
			directions[cs] = d1
			do_releasehook = True
		#
		d = directions[cs]
		miss_n = n_ranges[d][-1]
		#
		for n in n_ranges[d]:
			if bnValid(bed, n, gauge):
				# if row[n%w] == 0: k.knit(d, f"{bed}{n}", *cs) #TODO: #check
				if getData(p, n) == 0: k.knit(d, f"{bed}{n}", *cs) #TODO: #check
				else:
					if setting == TUCK: k.tuck(d, f"{bed}{n}", *cs)
					elif setting == SLIP or n == miss_n: k.miss(d, f"{bed}{n}", *cs)
					elif setting == LACE: #TODO: #check #TODO: have xfer be staggered if multiple needles in lace hole and multiple needles for knitting to the side
						if n == left_edge_bn[1] or n == right_edge_bn[1]: k.knit(d, f"{bed}{n}", *cs) # always knit edge-most needles
						else:
							k.xfer(f"{bed}{n}", f"{bed2}{n}")
							if d == "+": #transfer to the left
								# find next needle that contains knitting
								for n2 in range(n, left_edge_bn[1]-1, -1):
									if bnValid(n2) and getData(p, n2) == 0: break # will default to left_edge_bn[1]
								#
								if bed2 == "f": k.rack(n-n2)
								else: k.rack(n2-n)
								#
								k.xfer(f"{bed2}{n}", f"{bed}{n2}")
								k.rack(0)
							else: #transfer to the right
								# find next needle that contains knitting
								for n2 in range(n, right_edge_bn[1]+1):
									if bnValid(n2) and getData(p, n2) == 0: break # will default to right_edge_bn[1]
								#
								if bed2 == "f": k.rack(n-n2)
								else: k.rack(n2-n)
								#
								k.xfer(f"{bed2}{n}", f"{bed}{n2}")
								k.rack(0)
			elif n == miss_n: k.miss(d, f"{bed}{n}", *cs)

		"""
		if directions[cs] == "+":
			row = data[p%h] #TODO: #check
			#
			for n in range(left_n, right_n+1):
				if bnValid(bed, n, gauge):
					if row[n%w] == 0: #TODO: #check
						k.knit(directions[cs], f"{bed}{n}", *cs)
					else:
						if setting == TUCK: k.tuck(directions[cs], f"{bed}{n}", *cs)
						elif setting == SLIP or n == right_n: k.miss(directions[cs], f"{bed}{n}", *cs)
				elif n == right_n: k.miss(directions[cs], f"{bed}{n}", *cs)
			'''
			for i in row:
				n = i+left_n
				if bnValid(bed, n, gauge):
					if i == 0: k.knit(directions[cs], f"{bed}{n}", *cs)
					else:
						if setting == TUCK: k.tuck(directions[cs], f"{bed}{n}", *cs)
						elif setting == SLIP: k.miss(directions[cs], f"{bed}{n}", *cs)
			'''
		else:
			for i in reversed(row):
				n = i+left_n
				if i == 0: k.knit(directions[cs], f"{bed}{n}", *cs)
				else:
					if setting == TUCK: k.tuck(directions[cs], f"{bed}{n}", *cs)
					elif setting == SLIP: k.miss(directions[cs], f"{bed}{n}", *cs)
		"""
		#
		if do_releasehook:
			tuckPattern(k, first_n=start_n, direction=d1, c=None) #drop it
			k.releasehook(*cs)
			do_releasehook = False
		#
		if add_amiss and p % AMISS_INTERVAL == AMISS_INTERVAL-1: #new #check
			for n in n_ranges[toggleDirection(d)]:
				k.amiss(f"{bed}{n}")

			for n in n_ranges[d]:
				k.amiss(f"{bed2}{n}")
		#
		directions[cs] = toggleDirection(directions[cs])
		#
		if setting == FAIRISLE:
			if directions[cs2] is None: #inhook
				k.inhook(*cs2)
				tuckPattern(k, first_n=start_n, direction=d1, c=cs2)
				directions[cs2] = d1
				do_releasehook = True
			#
			d = directions[cs2]
			miss_n = n_ranges[d][-1]
			#
			for n in n_ranges[d]:
				if bnValid(bed, n, gauge):
					if getData(p, n) == 0: k.knit(d, f"{bed}{n}", *cs2) #TODO: #check
					else:
						if setting == TUCK: k.tuck(d, f"{bed}{n}", *cs2)
						elif setting == SLIP or n == miss_n: k.miss(d, f"{bed}{n}", *cs2)
				elif n == miss_n: k.miss(d, f"{bed}{n}", *cs2)
			#
			if do_releasehook:
				tuckPattern(k, first_n=start_n, direction=d1, c=None) #drop it
				k.releasehook(*cs2)
				do_releasehook = False
			#
			directions[cs2] = toggleDirection(directions[cs2])
		#
		if color_change_mod is not None and p % color_change_mod == (color_change_mod-1): cs, cs2 = cs2, cs
	#
	for carrier in flattenIter(outhook_carriers):
		k.outhook(carrier)
	#
	if c2 is None: return directions[cs]
	else: return directions[c2cs(c)], directions[c2cs(c2)] #since they could have been toggled
