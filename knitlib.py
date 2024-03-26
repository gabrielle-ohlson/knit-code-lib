import os
import sys
sys.path.insert(0, os.getcwd())

from typing import Union, Optional, Tuple, List, Dict

from .helpers import tuckPattern, c2cs, flattenIter, modsHalveGauge, bnValid, toggleDirection, bnLast
from .stitchPatterns import interlock


# ------------
# --- MISC ---
# ------------
def drawThread(k, left_n, right_n, draw_c, final_direction="-", final_bed="f", circular=False, miss_draw=None, gauge=1):
    '''
    helper function for draw threads

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `left_n` (int): the left-most needle to knit on
    * `right_n` (int): the right-most needle to knit on
    * `draw_c` (str): the carrier to use
    * `final_direction` (str, optional): the final direction we want the draw thread to knit in. (Note that if "-", carrier ends on left side, else if "+", carrier ends on right side). Defaults to "-".
    * `final_bed` (str, optional): the final bed knit on (only applicable for circular). Defaults to "f".
    * `circular` (bool, optional): whether to knit circularly. Defaults to False.
    * `miss_draw` (int, optional): optional needle to miss carrier past after knitting. Defaults to None.
    * `gauge` (int, optional): gauge to knit in. Defaults to 1.
    '''
    cs = c2cs(draw_c) # ensure tuple type

    if final_bed == "f": init_bed = "b"
    else: init_bed = "f"

    def posDraw(bed="f", add_miss=True):
        for n in range(left_n, right_n+1):
            if bnValid(bed, n, gauge): k.knit("+", f"{bed}{n}", *cs)
            elif n == right_n: k.miss("+", f"{bed}{n}", *cs)
        if add_miss and miss_draw is not None: k.miss("+", f"{bed}{miss_draw}", *cs)


    def negDraw(bed="f", add_miss=True):
        for n in range(right_n, left_n-1, -1):
            if bnValid(bed, n, gauge): k.knit("-", f"{bed}{n}", *cs)
            elif n == left_n: k.miss("-", f"{bed}{n}", *cs)
        if add_miss and miss_draw is not None: k.miss("-", f"{bed}{miss_draw}", *cs)

    k.comment("begin draw thread")

    if final_direction == "+":
        if circular: negDraw(init_bed, False)
        posDraw(final_bed)
    else:
        if circular: posDraw(init_bed, False)
        negDraw(final_bed)

    k.comment("end draw thread")


#--- FUNCTION FOR DOING THE MAIN KNITTING OF CIRCULAR, OPEN TUBES ---
def circular(k, start_n, end_n, passes, c, gauge=1):
    '''
    Knits on every needle circular tube starting on side indicated by which needle value is greater.
    In this function passes is the number of total passes knit so if you want a tube that
    is 20 courses long on each side set passes to 40.

    *k is knitout Writer
    *start_n is the starting needle to knit on
    *end_n is the last needle to knit on
    *passes is total passes knit
    *c is carrier
    *gauge is... gauge
    '''
    cs = c2cs(c) # ensure tuple type

    if end_n > start_n: #first pass is pos
        d = "+"
        left_n = start_n
        right_n = end_n
    else: #first pass is neg
        d = "-"
        left_n = end_n
        right_n = start_n

    for p in range(passes):
        if d == "+":
            for n in range(left_n, right_n+1):
                if bnValid("f", n, gauge): k.knit("+", f"f{n}", *cs)
                elif n == right_n: k.miss("+", f"f{n}", *cs)
        else:
            for n in range(right_n, left_n-1, -1):
                if bnValid("b", n, gauge): k.knit("-", f"b{n}", *cs)
                elif n == left_n: k.miss("-", f"b{n}", *cs)
        #
        d = toggleDirection(d)


#--- FUNCTION FOR BRINGING IN CARRIERS (only for kniterate) ---
def catchYarns(k, left_n, right_n, carriers, gauge=1, end_on_right=[], miss_needles={}, catch_max_needles=False, speedNumber=100): #TODO: adjust this for cs, inhook, et.
    '''
    _summary_

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `left_n` (int): the left-most needle to knit on
    * `right_n` (int): the right-most needle to knit on
    * `carriers` (list): list of the carriers to bring in
    * `gauge` (int, optional): gauge to knit in. Defaults to 1.
    * `end_on_right` (list, optional): optional list of carriers that should end on the right side of the piece (by default, any carriers not in this list will end on the left). Defaults to [].
    * `miss_needles` (dict, optional): optional dict with carrier as key and an integer needle number as value; indicates a needle that the given carrier should miss at the end to get it out of the way. Defaults to {}.
    * `catch_max_needles` (bool, optional): indicates whether or not the yarns should catch on intervals based on the number of carriers that shift for each carrier to reduce build up (True) or on as many needles as possible when being brought in (False). Defaults to False.
    * `speedNumber` (int, optional): value to set for the x-speed-number knitout extension. Defaults to 100.
    '''

    k.comment("catch yarns")
    if speedNumber is not None: k.speedNumber(speedNumber)

    for i, c in enumerate(carriers):
        k.incarrier(c)

        if c in end_on_right: passes = range(0, 5)
        else: passes = range(0, 4)

        front_ct = 1
        back_ct = 1

        for h in passes:
            if front_ct % 2 != 0: front_ct = 0
            else: front_ct = 1
            if back_ct % 2 != 0: back_ct = 0
            else: back_ct = 1

            if h % 2 == 0:
                for n in range(left_n, right_n+1):
                    if n % gauge == 0 and ((catch_max_needles and ((n/gauge) % 2) == 0) or (((n/gauge) % len(carriers)) == i)):
                        if front_ct % 2 == 0: k.knit("+", f"f{n}", c)
                        elif n == right_n: k.miss("+", f"f{n}", c) #TODO: make boolean #?
                        front_ct += 1
                    elif (gauge == 1 or n % gauge != 0) and ((catch_max_needles and (((n-1)/gauge) % 2) == 0) or ((((n-1)/gauge) % len(carriers)) == i)):
                        if back_ct % 2 == 0: k.knit("+", f"b{n}", c)
                        elif n == right_n: k.miss("+", f"f{n}", c)
                        back_ct += 1
                    elif n == right_n: k.miss("+", f"f{n}", c)
            else:
                for n in range(right_n, left_n-1, -1):
                    if n % gauge == 0 and ((catch_max_needles and ((n/gauge) % 2) != 0) or (((n/gauge) % len(carriers)) == i)):
                        if front_ct % 2 != 0: k.knit("-", f"f{n}", c)
                        elif n == left_n: k.miss("-", f"f{n}", c)
                        front_ct += 1
                    elif (gauge == 1 or n % gauge != 0) and ((catch_max_needles and (((n-1)/gauge) % 2) != 0) or ((((n-1)/gauge) % len(carriers)) == i)):
                        if back_ct % 2 != 0: k.knit("-", f"b{n}", c)
                        elif n == left_n: k.miss("-", f"f{n}", c)
                        back_ct += 1
                    elif n == left_n: k.miss("-", f"f{n}", c)

        if c in miss_needles:
            if c in end_on_right: k.miss("+", f"f{miss_needles[c]}", c)
            else: k.miss("-", f"f{miss_needles[c]}", c)


def wasteSection(k, left_n, right_n, closed_caston=True, waste_c="1", draw_c="2", in_cs=[], gauge=1, init_directions={}, end_on_right=[], first_needles={}, catch_max_needles=False, initial=True, draw_middle=False, interlock_passes=40, speedNumber=None, stitchNumber=None, rollerAdvance=None, waste_speedNumber=None, waste_stitchNumber=None, machine="swgn2"):
    '''
    Does everything to prepare for knitting prior to (and not including) the cast-on.
        - bring in carriers
        - (if kniterate) catch the yarns to make them secure
        - knit waste section for the rollers to catch
        - add draw thread
    Can also be used to produce a waste section to go in-between samples.

    Parameters:
    ----------
    * k (class): the knitout Writer.
    * left_n (int): the left-most needle to knit on.
    * right_n (int): the right-most needle to knit on.
    * closed_caston (bool, optional): determines what happens with the draw thread (if `True`, drops back-bed needles and knits draw on front-bed; if `False`, doesn't drop and knits draw on both beds). Defaults to `True`.
    * waste_c (str, optional): an integer in string form indicating the carrier number to be used for the waste yarn. Defaults to `1`.
    * draw_c (str, optional): same as above, but for the draw thread carrier. Defaults to `2`.
    * in_cs (list, optional): an *optional* list of other carriers that should be brought in/positioned with catchYarns (NOTE: leave empty if not initial wasteSection). Defaults to `[]`.
    * gauge (int, optional): the knitting gauge. Defaults to `1`.
    * init_directions (dict, optional): a dictionary with carriers as keys and directions (`-` or `+`) as values, indicating which direction to start with for a given carrier key. If a carrier that is used in teh waste section isn't included in the dict keys, will default to which ever side the carriers start on for the given machine (left for kniterate and right for swgn2). Defaults to `{}`.
    * end_on_right (list, optional): an *optional* list of carriers that should be parked on the right side after the wasteSection (**see *NOTE* below for details about what to do if not initial**) — e.g. `end_on_right=["2", "3"]`. Defaults to `[]`.
    * first_needles (dict, optional): an *optional* dictionary with carrier as key and a list of `[<left_n>, <right_n>]` as the value. It indicates the edge-most needles in the first row that the carrier is used in for the main piece. — e.g. `first_needles={"1": [0, 10]}`. Defaults to `{}`.
    * catch_max_needles (bool, optional): determines whether or not the maximum number of needles (possible for the given gauge) will be knitted on for *every* carrier (yes if `True`; if `False`, knits on interval determined by number of carriers). Defaults to `False`.
    * initial (bool, optional): if `True`, indicates that this wasteSection is the very first thing being knitted for the piece; otherwise, if `False`, it's probably a wasteSection to separate samples (and will skip over catchYarns). Defaults to True.
    * draw_middle (bool, optional): if `True`, indicates that a draw thread should be placed in the middle of the waste section (and no draw thread will be added at end, also no circular knitting, so only interlock). Defaults to False.
    * interlock_passes (int, optional): the number of passes of interlock that should be included (note that, if not `draw_middle`, 8 rows of circular will also be added onto the <x-number> of `interlock_passes` indicated). Defaults to `40`.

    Returns:
    -------
    * (dict): `carrier_locs`, which indicates the needle number that each carrier is parked by at the end of the wasteSection — e.g. `carrier_locs={"1": 0, "2": 200}`

    *NOTE:*
    if initial wasteSection, side (prior to this wasteSection) is assumed to be left for all carriers
    if not initial wasteSection, follow these guidelines for positioning:
        -> waste_c: if currently on right side (prior to this wasteSection), put it in `end_on_right` list; otherwise, don't
        -> draw_c:
            if not draw_middle: if currently on left side, put it in `end_on_right` list; otherwise, don't
            else: if currently on right side, put it in `end_on_right` list; otherwise, don't
    '''

    carrier_locs = {}

    if stitchNumber is not None: k.stitchNumber(stitchNumber)
    if rollerAdvance is not None: k.rollerAdvance(rollerAdvance)
    
    miss_waste = None
    miss_draw = None
    miss_other_cs = {}

    if len(first_needles):
        if waste_c in first_needles:
            if waste_c in end_on_right:
                miss_waste = first_needles[waste_c][1]
                carrier_locs[waste_c] = first_needles[waste_c][1]
            else:
                miss_waste = first_needles[waste_c][0]
                carrier_locs[waste_c] = first_needles[waste_c][0]
        
        if draw_c in first_needles:
            if draw_c in end_on_right:
                miss_draw = first_needles[draw_c][1]
                carrier_locs[draw_c] = first_needles[draw_c][1]
            else:
                miss_draw = first_needles[draw_c][0]
                carrier_locs[draw_c] = first_needles[draw_c][0]

        if len(in_cs):
            for c in range(0, len(in_cs)):
                if in_cs[c] in first_needles:
                    if in_cs[c] in end_on_right:
                        miss_other_cs[in_cs[c]] = first_needles[in_cs[c]][1]
                        carrier_locs[in_cs[c]] = first_needles[in_cs[c]][1]
                    else:
                        miss_other_cs[in_cs[c]] = first_needles[in_cs[c]][0]
                        carrier_locs[in_cs[c]] = first_needles[in_cs[c]][0]

    carriers = [waste_c, draw_c]
    carriers.extend(in_cs)
    carriers = list(set(carriers))

    carriers = [x for x in carriers if x is not None]

    if len(carriers) != len(carrier_locs):
        for c in carriers:
            if c not in carrier_locs:
                if c in end_on_right: carrier_locs[c] = right_n
                else: carrier_locs[c] = left_n

    if initial:
        catch_end_on_right = end_on_right.copy()

        if closed_caston and not draw_middle:
            if draw_c in end_on_right:
                catch_end_on_right.remove(draw_c)
                if draw_c in miss_other_cs: miss_other_cs[draw_c] = first_needles[draw_c][0] 
            else:
                catch_end_on_right.append(draw_c)
                if draw_c in miss_other_cs: miss_other_cs[draw_c] = first_needles[draw_c][1] 

        if machine.lower() == "kniterate": catchYarns(k, left_n, right_n, carriers, gauge, catch_end_on_right, miss_other_cs, catch_max_needles)
        elif waste_c in in_cs: k.inhook(*c2cs(waste_c))

    k.comment("begin waste section")
    if waste_speedNumber is not None: k.speedNumber(waste_speedNumber)
    if waste_stitchNumber is not None: k.stitchNumber(waste_stitchNumber)

    if draw_middle: interlock_passes //= 2
    
    if draw_c in end_on_right: draw_final_d = "+" #drawSide = "r" # side it ends on (could also do from `finalDirs` or `endDirs`)
    else: draw_final_d = "-" #drawSide = "l"

    # init direction for draw thread: #TODO: do this for other carriers
    if draw_c in init_directions:
        draw_init_d = init_directions[draw_c]
    elif draw_c in in_cs: # meaning we are bringing it in for the first time
        if machine.lower() == "kniterate": draw_init_d = "+"
        else: draw_init_d = "-"
    elif (draw_final_d == "+" and closed_caston) or (draw_final_d == "-" and not closed_caston): draw_init_d = "+"
    else: draw_init_d = "-"
    
    if waste_c in end_on_right: #NOTE: would need to add extra pass if waste_c == draw_c and closed_caston == True (but doesn't really make sense to have same yarn for those)
        if machine.lower() == "kniterate" and initial and interlock_passes > 24:
            interlock(k, right_n, left_n, 24, waste_c, gauge=gauge)
            k.pause("cut yarns")
            interlock(k, right_n, left_n, interlock_passes-24, waste_c, gauge=gauge)
        else: interlock(k, right_n, left_n, interlock_passes, waste_c, gauge=gauge, releasehook=(machine.lower() == "swgn2" and waste_c in in_cs))

        if draw_middle:
            if draw_c is not None:
                if machine.lower() == "swgn2" and draw_c in in_cs:
                    k.inhook(*c2cs(draw_c))
                    tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=draw_c)
                    
                if draw_init_d == draw_final_d: # we need to tuck to get it in the correct position
                    n_range = range(left_n, right_n+1)
                    if draw_init_d == "-": n_range = n_range[::-1] #reverse it reversed(n_range)
                    cs = c2cs(draw_c)
                    for n in n_range:
                        if n % 2 == 0: k.tuck(draw_init_d, f"b{n}", *cs)
                        elif n == n_range[-1]: k.miss(draw_init_d, f"b{n}", *cs)
                    
                    # this is essentially circular
                    drawThread(k, left_n, right_n, draw_c, final_direction=("-" if draw_final_d == "+" else "+"), final_bed="f", circular=False, miss_draw=miss_draw, gauge=gauge)
                    for n in n_range:
                        if n % 2 == 0: k.drop(f"b{n}")
                    drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, final_bed="b", circular=False, miss_draw=miss_draw, gauge=gauge)
                else: drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, circular=True, miss_draw=miss_draw, gauge=gauge) 

                if machine.lower() == "swgn2" and draw_c in in_cs:
                    k.releasehook(*c2cs(draw_c))
                    tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=None) # drop it

            if initial and interlock_passes > 12:
                if interlock_passes < 24:
                    pause_after = 24-interlock_passes
                    interlock(k, right_n, left_n, pause_after, waste_c, gauge=gauge) # 20 32 (16) #12 interlock_passes-8 # 12
                    if machine.lower() == "kniterate": k.pause("cut yarns")
                    interlock(k, right_n, left_n, interlock_passes-pause_after, waste_c, gauge=gauge) # 8 interlockL 20- (32-20) 20-32 + 20+20
                else: interlock(k, right_n, left_n, interlock_passes, waste_c, gauge=gauge)
            else:
                interlock(k, right_n, left_n, interlock_passes, waste_c, gauge=gauge)
                if machine.lower() == "kniterate" and initial: k.pause("cut yarns")
        else:
            if machine.lower() == "kniterate" and initial and interlock_passes <= 24: k.pause("cut yarns")
            circular(k, right_n, left_n, 8, waste_c, gauge)
        if miss_waste is not None: k.miss("+", f"f{miss_waste}", waste_c)
    else:
        if machine.lower() == "kniterate" and initial and interlock_passes > 24:
            interlock(k, left_n, right_n, 24, waste_c, gauge=gauge)
            k.pause("cut yarns")
            interlock(k, left_n, right_n, interlock_passes-24, waste_c, gauge=gauge)
        else:
            if machine.lower() == "swgn2" and initial:
                interlock(k, right_n, left_n, 1.5, waste_c, gauge, releasehook=(machine.lower() == "swgn2" and waste_c in in_cs))
                interlock_passes -= 2
            interlock(k, left_n, right_n, interlock_passes, waste_c, gauge=gauge)

        if draw_middle:
            if draw_c is not None:
                if machine.lower() == "swgn2" and draw_c in in_cs:
                    k.inhook(*c2cs(draw_c))
                    tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=draw_c)
                
                if draw_init_d == draw_final_d: # we need to tuck to get it in the correct position #v
                    n_range = range(left_n, right_n+1)
                    if draw_init_d == "-": n_range = n_range[::-1] #reverse it #reversed(n_range)
                    cs = c2cs(draw_c)
                    for n in n_range:
                        if n % 2 == 0: k.tuck(draw_init_d, f"b{n}", *cs)
                        elif n == n_range[-1]: k.miss(draw_init_d, f"b{n}", *cs)
                    
                    # this is essentially circular
                    drawThread(k, left_n, right_n, draw_c, final_direction=("-" if draw_final_d == "+" else "+"), final_bed="f", circular=False, miss_draw=miss_draw, gauge=gauge)
                    for n in n_range:
                        if n % 2 == 0: k.drop(f"b{n}")
                    drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, final_bed="b", circular=False, miss_draw=miss_draw, gauge=gauge)
                else: drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, circular=True, miss_draw=miss_draw, gauge=gauge) #^

                if machine.lower() == "swgn2" and draw_c in in_cs:
                    k.releasehook(*c2cs(draw_c))
                    tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=None) # drop it

            if initial and interlock_passes > 12:
                if interlock_passes < 24:
                    pause_after = 24-interlock_passes
                    interlock(k, left_n, right_n, pause_after, waste_c, gauge=gauge) # 20 32 (16) #12 interlock_passes-8 # 12
                    if machine.lower() == "kniterate": k.pause("cut yarns")
                    interlock(k, left_n, right_n, interlock_passes-pause_after, waste_c, gauge=gauge) # 8 interlockL 20- (32-20) 20-32 + 20+20
                else: interlock(k, left_n, right_n, interlock_passes, waste_c, gauge=gauge)
            else:
                interlock(k, left_n, right_n, interlock_passes, waste_c, gauge=gauge)
                if initial: k.pause("cut yarns")
        else:
            if machine.lower() == "kniterate" and initial and interlock_passes <= 24: k.pause("cut yarns")
            circular(k, left_n, right_n, 8, waste_c, gauge)
        if miss_waste is not None: k.miss("-", f"f{miss_waste}", *c2cs(waste_c))

    if closed_caston and not draw_middle:
        for n in range(left_n, right_n+1):
            if bnValid("b", n, gauge): k.drop(f"b{n}")

    if not draw_middle and draw_c is not None:
        if machine.lower() == "swgn2" and draw_c in in_cs:
            k.inhook(*c2cs(draw_c))
            tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=draw_c)

        if (closed_caston and draw_init_d != draw_final_d) or (not closed_caston and draw_init_d == draw_final_d): # we need to tuck to get it in the correct position #v
            n_range = range(left_n, right_n+1)
            if draw_init_d == "-": n_range = n_range[::-1] # reverse it #reversed(n_range)

            cs = c2cs(draw_c)
            for n in n_range:
                if n % 2 == 0: k.tuck(draw_init_d, f"b{n}", *cs)
                elif n == n_range[-1]: k.miss(draw_init_d, f"b{n}", *cs)

            if closed_caston: draw_final_d1 = draw_final_d
            else: draw_final_d1 = ("-" if draw_final_d == "+" else "+")

            drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d1, final_bed="f", circular=False, miss_draw=miss_draw, gauge=gauge)

            if not closed_caston: # aka circular
                # this + above drawThread call is essentially circular
                for n in n_range:
                    if n % 2 == 0: k.drop(f"b{n}")
                drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, final_bed="b", circular=False, miss_draw=miss_draw, gauge=gauge)
            else:
                for n in n_range:
                    if n % 2 == 0: k.drop(f"b{n}")
        else: drawThread(k, left_n, right_n, draw_c, final_direction=draw_final_d, circular=(not closed_caston), miss_draw=miss_draw, gauge=gauge)

        if machine.lower() == "swgn2" and draw_c in in_cs:
            k.releasehook(*c2cs(draw_c))
            tuckPattern(k, first_n=(left_n if draw_init_d=="+" else right_n), direction=draw_init_d, c=None) # drop it

    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment("end waste section")
    return carrier_locs


# ---------------
# --- CASTONS ---
# ---------------
def altTuckCaston(k, start_n, end_n, c, bed, gauge=1, inhook=False, releasehook=False, tuck_pattern=False, speedNumber=None, stitchNumber=None, knit_after=True, knit_stitchNumber=None): #TODO #check
    '''
    for sheet caston

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to cast-on
    * `end_n` (int): the last needle to cast-on (inclusive)
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `bed` (str): bed to do the knitting on
    * `gauge` (int, optional): the knitting gauge. Defaults to `1`.
    * `speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
    * `stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
    * `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
    * `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
    * `tuck_pattern` (bool, optional): whether to include a tuck pattern for extra security when bringing in the carrier (only applicable if `inhook` or `releasehook` == `True`). Defaults to `False`.
    * `speedNumber` (int, optional): value to set for the x-speed-number knitout extension. Defaults to None.
    * `stitchNumber` (int, optional): value to set for the x-stitch-number knitout extension. Defaults to None.
    '''

    # for sheet:
    cs = c2cs(c) # ensure tuple type

    k.comment("begin alternating tuck cast-on")
    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    if end_n > start_n: #first pass is pos
        d1 = "+"
        d2 = "-"
        n_range1 = range(start_n, end_n+1)
        n_range2 = range(end_n, start_n-1, -1)
    else: #first pass is neg
        d1 = "-"
        d2 = "+"
        n_range1 = range(start_n, end_n-1, -1)
        n_range2 = range(end_n, start_n+1)

    mods = modsHalveGauge(gauge, bed)

    if abs(mods[1]-start_n%(gauge*2)) < abs(mods[0]-start_n%(gauge*2)): mods = mods[::-1] #so don't start knitting on most recently tucked needle

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)
        
    for n in n_range1:
        if n % (gauge*2) == mods[0]: k.tuck(d1, f"{bed}{n}", *cs)
        elif n == n_range1[-1]: k.miss(d1, f"{bed}{n}", *cs)

    for n in n_range2:
        if n % (gauge*2) == mods[1]:
            k.tuck(d2, f"{bed}{n}", *cs)
        elif n == n_range2[-1]: k.miss(d2, f"{bed}{n}", *cs)

    if releasehook:
        k.releasehook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
    
    if knit_after:
        if knit_stitchNumber is not None: k.stitchNumber(knit_stitchNumber)
        # 2 passes to get the knitting going (and to ensure the last needle we tucked on is skipped)
        for n in n_range1:
            if n % gauge == mods[0]: k.knit(d1, f"{bed}{n}", *cs)

        for n in n_range2:
            if n % gauge == mods[0]: k.knit(d2, f"{bed}{n}", *cs)

    k.comment("end alternating tuck cast-on")


def altTuckClosedCaston(k, start_n, end_n, c, gauge=2):
    #TODO: add stuff for inhook, tuck_pattern, etc.
    cs = c2cs(c) # ensure tuple type
    
    if start_n > end_n: # pass is neg
        d1 = "-"
        n_range1 = range(start_n, end_n-1, -1)
        n_range2 = range(end_n, start_n+1)
        d2 = "+"
    else:
        d1 = "+"
        n_range1 = range(start_n, end_n+1) 
        n_range2 = range(end_n, start_n-1) 
        d2 = "-"
    
    last_n = None

    if gauge == 1:
        for n in n_range1:
            if n % 2 == 0: k.tuck(d1, f"f{n}", *cs)
            else: k.tuck(d1, f"b{n}", *cs)
        
        for n in n_range2:
            if n % 2 == 0: k.tuck(d2, f"b{n}", *cs)
            else: k.tuck(d2, f"f{n}", *cs)
    else:
        for n in n_range1:
            if bnValid("f", n, gauge):
                k.tuck(d1, f"f{n}", *cs)
                last_n = n #keep updating this
            elif bnValid("b", n, gauge):
                k.tuck(d1, f"b{n}", *cs)
                last_n = n #keep updating this

        prev_n = None #TODO: #check this stuff

        if bnValid("f", last_n, gauge):
            if d1 == "-": prev_n = last_n+(gauge//2)
            else: prev_n = last_n-gauge+(gauge//2)
            #
            k.knit(d2, f"b{prev_n}", *cs)
            k.miss(d1, f"f{last_n}", *cs)
        else:
            if d1 == "-": prev_n = last_n+gauge-(gauge//2)
            else: prev_n = last_n-(gauge//2)
            #
            k.knit(d2, f"f{prev_n}", *cs)
            k.miss(d1, f"b{last_n}", *cs)

        # if (bnValid("f", last_n, gauge) and d2 == "-") or (bnValid("b", last_n, gauge) and d2 == "+"):
        #     k.rack(1.25)
        # else:
        # # elif (bnValid("f", last_n, gauge) and d2 == "+") or (bnValid("b", last_n, gauge) and d2 == "-"):
        #     k.rack(-1.25) #TODO: #check (-1.75 #?)
    
        for n in n_range2:
            # if n == last_n: continue # skip first needle that we just knitted #remove
            if n == prev_n: continue # skip first needle that we just knitted
            if bnValid("f", n, gauge): k.knit(d2, f"f{n}", *cs)
            elif bnValid("b", n, gauge): k.knit(d2, f"b{n}", *cs)
            elif n == n_range2[-1]: k.miss(d2, f"f{n}", *cs)

    print(f"carrier {c} parked on {'left' if d2 == '-' else 'right'} side") #debug


#--- FUNCTION FOR CASTING ON OPEN TUBES ---
def altTuckOpenTubeCaston(k, start_n, end_n, c, gauge=1, inhook=False, releasehook=False, tuck_pattern=False, speedNumber=None, stitchNumber=None, knit_after=True):
    '''
    Function for an open-tube cast-on, tucking on alternate needles circularly.

        - total of 6 passes knitted circularly (3 on each bed); carrier will end on the side it started
        - first 4 passes are alternating cast-on, last 2 are extra passes to make sure loops are secure

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to cast-on
    * `end_n` (int): the last needle to cast-on (inclusive)
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `gauge` (int, optional): the knitting gauge. Defaults to `1`.
    * `inhook` (bool, optional): whether to have the function do an inhook. Defaults to `False`.
    * `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to `False`.
    * `tuck_pattern` (bool, optional): whether to include a tuck pattern for extra security when bringing in the carrier (only applicable if `inhook` or `releasehook` == `True`). Defaults to `False`.
    * `speedNumber` (int): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
    * `stitchNumber` (int): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
    '''
    cs = c2cs(c) # ensure tuple type

    k.comment("begin open tube cast-on")
    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    if end_n > start_n: #first pass is pos
        d1 = "+"
        d2 = "-"
        needle_range1 = range(start_n, end_n+1)
        needle_range2 = range(end_n, start_n-1, -1)
    else: #first pass is neg
        d1 = "-"
        d2 = "+"
        needle_range1 = range(start_n, end_n-1, -1)
        needle_range2 = range(end_n, start_n+1)

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

    mods_f = modsHalveGauge(gauge, "f")
    mods_b = modsHalveGauge(gauge, "b")

    for n in needle_range1:
        if n % (gauge*2) == mods_f[0]: k.knit(d1, f"f{n}", *cs)
        elif n == end_n: k.miss(d1, f"f{n}", *cs)
        # if n % gauge == 0 and (((n/gauge) % 2) == 0): k.knit(dir1, f"f{n}", *cs)
        # elif n == end_n: k.miss(dir1, f"f{n}", *cs)

    for n in needle_range2:
        if n % (gauge*2) == mods_b[0]: k.knit(d2, f"b{n}", *cs)
        elif n == start_n: k.miss(d2, f"b{n}", *cs)
        # if (gauge == 1 or n % gauge != 0) and ((((n-1)/gauge) % 2) == 0): k.knit(dir2, f"b{n}", *cs)
        # elif n == start_n: k.miss(dir2, f"b{n}", *cs)

    if releasehook:
        k.releasehook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

    for n in needle_range1:
        if n % (gauge*2) == mods_f[1]: k.knit(d1, f"f{n}", *cs)
        elif n == end_n: k.miss(d1, f"f{n}", *cs)
        # if n % gauge == 0 and (((n/gauge) % 2) != 0): k.knit(dir1, f"f{n}", *cs)
        # elif n == end_n: k.miss(dir1, f"f{n}", *cs)

    for n in needle_range2:
        if n % (gauge*2) == mods_b[1]: k.knit(d2, f"b{n}", *cs)
        elif n == start_n: k.miss(d2, f"b{n}", *cs)
        # if (gauge == 1 or n % gauge != 0) and ((((n-1)/gauge) % 2) != 0): k.knit(dir2, f"b{n}", *cs)
        # elif n == start_n: k.miss(dir2, f"b{n}", *cs)

    if knit_after:
        #two final passes now that loops are secure
        for n in needle_range1:
            if bnValid("f", n, gauge): k.knit(d1, f"f{n}", *cs)
            # if n % gauge == 0: k.knit(dir1, f"f{n}", *cs)
            elif n == end_n: k.miss(d1, f"f{n}", *cs)

        for n in needle_range2:
            if bnValid("b", n, gauge): k.knit(d2, f"b{n}", *cs)
            # if (n+1) % gauge == 0: k.knit(dir2, f"b{n}", *cs)
            elif n == start_n: k.miss(d2, f"b{n}", *cs)

    k.comment("end open tube cast-on")


#--- FUNCTION FOR CASTING ON CLOSED TUBES (zig-zag) ---
def zigzagCaston(k, start_n, end_n, c, gauge=1, inhook=False, releasehook=False, tuck_pattern=True): #TODO: adjust for gauge TODO: indicate that most recent needle needs to be skipped, or do something to secure it (such as `knit_after` param)
    '''
    * k is the knitout Writer
    * start_n is the initial needle to cast-on
    * end_n is the last needle to cast-on (inclusive)
    * c is the carrier to use for the cast-on (or list of carriers, if plating)
    * gauge is gauge

    - only one pass; carrier will end on the side opposite to which it started
    '''
    cs = c2cs(c) # ensure tuple type

    if releasehook and not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes.")

    k.comment("begin zigzag cast-on")

    if end_n > start_n:
        d = "+"
        n_range = range(start_n, end_n+1)
        b1, b2 = "f", "b"
    else:
        d = "-"
        n_range = range(start_n, end_n-1, -1)
        b1, b2 = "b", "f"
    
    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d, c=cs)

    # mods = {b1: modsHalveGauge(gauge, b1), b2: modsHalveGauge(gauge, b2)}
    k.rack(0.25)
    for n in n_range:
        if bnValid(b1, n, gauge): k.knit(d, f"{b1}{n}", *cs)

        if bnValid(b2, n, gauge): k.knit(d, f"{b2}{n}", *cs)
        elif n == n_range[-1]: k.miss(d, f"{b2}{n}", *cs)

    k.rack(0)

    if releasehook:
        k.releasehook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d, c=None) # drop it

    k.comment("end zigzag cast-on")


# -----------------------
# --- BINDOFFS/FINISH ---
# -----------------------

#--- FINISH BY DROP FUNCTION ---
def dropFinish(k, front_needle_ranges=[], back_needle_ranges=[], out_carriers=[], roll_out=True, avoid_bns={"f": [], "b": []}, direction="+", border_c=None, border_passes=16, gauge=1, machine="swgn2"):
    '''
    Finishes knitting by dropping loops (optionally knitting 16 rows of waste yarn prior with `border_c`, and optionally taking carriers listed in `carriers` param out afterwards).

    Parameters:
    ----------
    * `k` (class instance): the knitout Writer.
    * `front_needle_ranges` (list, optional): a list of [left_n, right_n] pairs for needles to drop on the front bed; if multiple sections, can have sub-lists as so: [[leftN1, rightN1], [leftN2, rightN2], ...], or just [left_n, right_n] if only one section. Defaults to `[]`.
    * `back_needle_ranges` (list, optional): same as above, but for back bed. Defaults to `[]`.
    * `out_carriers` (list, optional): list of carriers to take out (optional, only if you want to take them out using this function). Defaults to `[]`.
    * `roll_out` (bool, optional): (for kniterate) an optional boolean parameter indicating whether extra roller advance should be added to roll the piece out. Defaults to `True`.
    * `empty_needles` (list, optional): an optional list of needles that are not currently holding loops (e.g. if using stitch pattern), so don't waste time dropping them. Defaults to `[]`.
    * `direction` (str, optional): an optional parameter to indicate which direction the first pass should have (valid values are "+" or "-"). (NOTE: this is an important value to pass if border_c is included, so know which direction to knit first with border_c). Defaults to `"+"`. #TODO: maybe just add a knitout function to find line that last used the border_c carrier
    * `border_c` (str, optional): an optional carrier that will knit some rows of waste yarn before dropping, so that there is a border edge on the top to prevent the main piece from unravelling (NOTE: if border_c is None, will not add any border). Defaults to `None`.
    * `border_passes` (int, optional): Number of passes for waste border. Defaults to `16`.
    * `gauge` (int, optional): Gauge of waste border, if applicable. Defaults to `2`.
        * NOTE: if gauge is 2, will knit waste border as a tube. if gauge is 1, will knit flat single bed stitch pattern.
    '''

    k.comment("begin drop finish")

    out_cs = list(out_carriers.copy()) #ensure list so we can remove

    if machine.lower() == "kniterate": out_func = k.outcarrier
    else: out_func = k.outhook

    if len(out_carriers):
        if border_c is not None and border_c in out_carriers: out_cs.remove(border_c) # remove so can take it out at end instead
        
        for c in flattenIter(out_cs):
            out_func(c)

    border_cs = c2cs(border_c) #ensure tuple type

    def knitBorder(pos_needle_range, pos_bed, neg_needle_range, neg_bed): #v
        # NOTE: if specified `borderStPat`, assumes `pos_needle_range` and `neg_needle_range` are the same

        d = direction

        def knitBorderPos(needle_range, bed):
            for n in range(needle_range[0], needle_range[1]+1):
                if bnValid(bed, n, gauge) and n not in avoid_bns[bed]: k.knit("+", f"{bed}{n}", *border_cs)
        
        def knitBorderNeg(needle_range, bed):
            for n in range(needle_range[1], needle_range[0]-1, -1):
                if bnValid(bed, n, gauge) and n not in avoid_bns[bed]: k.knit("-", f"{bed}{n}", *border_cs)
    
        for p in range(border_passes):
            if d == "+": knitBorderPos(pos_needle_range, pos_bed)
            else: knitBorderNeg(neg_needle_range, neg_bed)
            #
            d = toggleDirection(d)
    #--- end knitBorder func ---#^

    if border_c is not None:
        if len(front_needle_ranges) and len(back_needle_ranges):
            needle_ranges1 = front_needle_ranges
            bed1 = "f"
            needle_ranges2 = back_needle_ranges
            bed2 = "b"
        else:
            if len(front_needle_ranges):
                needle_ranges1 = front_needle_ranges
                bed1 = "f"
                needle_ranges2 = front_needle_ranges
                bed2 = "f"
            else:
                needle_ranges1 = back_needle_ranges
                bed1 = "b"
                needle_ranges2 = back_needle_ranges
                bed2 = "b"

        if type(needle_ranges1[0]) == int: #just one range (one section)
            knitBorder(needle_ranges1, bed1, needle_ranges2, bed2)
        else:
            for nr in range(0, len(needle_ranges1)):
                knitBorder(needle_ranges1[nr], bed1, needle_ranges2[nr], bed2)

    def dropOnBed(needle_ranges, bed): #v
        if type(needle_ranges[0]) == int: #just one range (one section)
            if roll_out and machine.lower() == "kniterate" and (needle_ranges is back_needle_ranges or not len(back_needle_ranges)): k.addRollerAdvance(2000) #TODO: determine what max roller advance is
            for n in range(needle_ranges[0], needle_ranges[1]+1):
                if bnValid(bed, n, gauge) and n not in avoid_bns[bed]: k.drop(f"{bed}{n}")
        else: #multiple ranges (multiple sections, likely shortrowing)
            for nr in needle_ranges:
                if roll_out and machine.lower() == "kniterate" and needle_ranges.index(nr) == len(needle_ranges)-1 and (needle_ranges is back_needle_ranges or not len(back_needle_ranges)): k.addRollerAdvance(2000)
                for n in range(nr[0], nr[1]+1):
                    if bnValid(bed, n, gauge) and n not in avoid_bns[bed]: k.drop(f"{bed}{n}")
    #--- end dropOnBed func ---#^

    if len(front_needle_ranges): dropOnBed(front_needle_ranges, "f")
    if len(back_needle_ranges): dropOnBed(back_needle_ranges, "b")

    if border_c is not None and border_c in out_carriers: out_func(border_c) #TODO: change to border_cs #?

    k.comment("end drop finish")


def bindoffTag(k, d, bed, edge_n, c, outhook=False, drop=False):
    if c is None: #just drop it
        if d == "-": # started pos
            for n in range(edge_n, edge_n+3):
                k.drop(f"{bed}{n}")
        else:
            for n in range(edge_n, edge_n-3, -1):
                k.drop(f"{bed}{n}")
        #
        return

    cs = c2cs(c) # ensure tuple type

    if d == "+": shift = -1 #will knit the tag to the left of edge_n
    else: shift = 1 #will knit the tag to the right of edge_n

    for r in range(4):
        k.knit(d, f"{bed}{edge_n}", *cs)
        if r == 3:
            k.tuck(d, f"{bed}{edge_n+shift}", *cs)
        d = toggleDirection(d)

    k.tuck(d, f"{bed}{edge_n+(shift*2)}", *cs)
    k.knit(d, f"{bed}{edge_n+(shift)}", *cs)
    k.knit(d, f"{bed}{edge_n}", *cs)

    d = toggleDirection(d)
    if d == "-": # started pos
        for r in range(2):
            for n in range(edge_n, edge_n-3, -1):
                k.knit(d, f"{bed}{n}", *cs)
            d = toggleDirection(d)

            for n in range(edge_n-2, edge_n+1):
                k.knit(d, f"{bed}{n}", *cs)
            d = toggleDirection(d)
        
        if outhook: k.outhook(*cs)
        if drop:
            for n in range(edge_n, edge_n-3, -1):
                k.drop(f"{bed}{n}")
    else: # started neg
        for r in range(2):
            for n in range(edge_n, edge_n+3):
                k.knit(d, f"{bed}{n}", *cs)
            d = toggleDirection(d)
            for n in range(edge_n+2, edge_n-1, -1):
                k.knit(d, f"{bed}{n}", *cs)
            d = toggleDirection(d)
        
        if outhook: k.outhook(*cs)
        if drop:
            for n in range(edge_n, edge_n+3):
                k.drop(f"{bed}{n}")

    
    return d # next direction to knit in (though likely not doing anymore knitting)


#--- SECURE BINDOFF FUNCTION (can also be used for decreasing large number of stitches) ---
def closedBindoff_old(k, count, xfer_needle, c, side="l", double_bed=True, as_dec_method=False, empty_needles=[], tag=True, gauge=1, machine="swgn2", speedNumber=None, stitchNumber=None, xfer_stitchNumber=None): #TODO: add code for gauge 2
    '''
    *TODO
    '''
    cs = c2cs(c) # ensure tuple type

    if not as_dec_method: k.comment("begin closed bindoff")
    else: k.comment("begin dec by bindoff")

    if speedNumber is not None: k.speedNumber(speedNumber)

    def posLoop(op=None, bed=None): #v
        if op == "xfer" and xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
        else: k.stitchNumber(stitchNumber)

        for x in range(xfer_needle, xfer_needle+count):
            if op == "knit":
                if f"{bed}{x}" not in empty_needles: k.knit("+", f"{bed}{x}", *cs)
            elif op == "xfer":
                receive = "b"
                if bed == "b": receive = "f"
                if f"{bed}{x}" not in empty_needles: k.xfer(f"{bed}{x}", f"{receive}{x}")
            else:
                if x == xfer_needle + count - 1 and not as_dec_method: break

                if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                k.xfer(f"b{x}", f"f{x}") #don't have to worry about empty needles here because binding these off
                k.rack(-1)
                k.xfer(f"f{x}", f"b{x+1}")
                k.rack(0)
                if x != xfer_needle:
                    if machine.lower() == "kniterate":
                        if not as_dec_method and x - xfer_needle == 30: k.rollerAdvance(0)
                        elif x > xfer_needle+3 and (as_dec_method or x - xfer_needle < 30): k.addRollerAdvance(-50)
                    k.drop(f"b{x-1}")
                if machine.lower() == "kniterate" and not as_dec_method and x - xfer_needle >= 30: k.addRollerAdvance(50)
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                k.knit("+", f"b{x+1}", *cs)

                if as_dec_method and len(empty_needles) and x == xfer_needle+count-1 and f"b{x+1}" in empty_needles: #transfer this to a non-empty needle if at end and applicable
                    if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

                    if f"f{x+1}" not in empty_needles: k.xfer(f"b{x+1}", f"f{x+1}")
                    else:
                        for z in range(x+2, x+7): #TODO: check what gauge should be
                            if f"f{z}" not in empty_needles:
                                k.rack(z-(x+1))
                                k.xfer(f"b{x+1}", f"f{z}")
                                k.rack(0)
                                break
                            elif f"b{z}" not in empty_needles:
                                k.xfer(f"b{x+1}", f"f{x+1}")
                                k.rack((x+1)-z)
                                k.xfer(f"f{x+1}", f"b{z}")
                                k.rack(0)
                                break
                
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                if x < xfer_needle+count-2: k.tuck("-", f"b{x}", *cs)
                if not as_dec_method and (x == xfer_needle+3 or (x == xfer_needle+count-2 and xfer_needle+3 > xfer_needle+count-2)): k.drop(f"b{xfer_needle-1}")
    #--- end posLoop func ---#^

    def negLoop(op=None, bed=None): #v
        if op == "xfer" and xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
        else: k.stitchNumber(stitchNumber)

        for x in range(xfer_needle+count-1, xfer_needle-1, -1):
            if op == "knit":
                if f"{bed}{x}" not in empty_needles: k.knit("-", f"{bed}{x}", *cs)
            elif op == "xfer":
                receive = "b"
                if bed == "b": receive = "f"
                if f"{bed}{x}" not in empty_needles: k.xfer(f"{bed}{x}", f"{receive}{x}")
            else:
                if x == xfer_needle and not as_dec_method: break

                if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                k.xfer(f"b{x}", f"f{x}")
                k.rack(1)
                k.xfer(f"f{x}", f"b{x-1}")
                k.rack(0)
                if x != xfer_needle+count-1:
                    if machine.lower() == "kniterate":
                        if not as_dec_method and (xfer_needle+count) - x == 30: k.rollerAdvance(0)
                        elif x < xfer_needle+count-4 and (as_dec_method or (xfer_needle+count) - x < 30): k.addRollerAdvance(-50)
                    k.drop(f"b{x+1}")
                if machine.lower() == "kniterate" and not as_dec_method and (xfer_needle+count) - x >= 30: k.addRollerAdvance(50)
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                k.knit("-", f"b{x-1}", *cs)

                if as_dec_method and len(empty_needles) and x == xfer_needle-2 and f"b{x-1}" in empty_needles: #transfer this to a non-empty needle if at end and applicable
                    if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                    if f"f{x-1}" not in empty_needles: k.xfer(f"b{x-1}", f"f{x-1}")
                    else:
                        for z in range(x-2, x-7, -1): #TODO: check what gauge should be
                            if f"f{z}" not in empty_needles:
                                k.rack(z-(x+1))
                                k.xfer(f"b{x-1}", f"f{z}")
                                k.rack(0)
                                break
                            elif f"b{z}" not in empty_needles:
                                k.xfer(f"b{x-1}", f"f{x-1}")
                                k.rack((x+1)-z)
                                k.xfer(f"f{x-1}", f"b{z}")
                                k.rack(0)
                                break
                
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                if x > xfer_needle+1: k.tuck("+", f"b{x}", *cs)
                if not as_dec_method and (x == xfer_needle+count-4 or (x == xfer_needle+1 and xfer_needle+count-4 < xfer_needle+1)): k.drop(f"b{xfer_needle+count}")
    #--- end negLoop func ---#^

    if side == "l": # side == "l", aka binding off in pos direction
        if not as_dec_method:
            posLoop("knit", "f")
            if double_bed: negLoop("knit", "b")

        # if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
        posLoop("xfer", "f")
        if machine.lower() == "kniterate":
            k.rollerAdvance(50)
            k.addRollerAdvance(-50)
        
        if stitchNumber is not None: k.stitchNumber(stitchNumber)
        if not as_dec_method: k.tuck("-", f"b{xfer_needle-1}", *cs)
        k.knit("+", f"b{xfer_needle}", *cs)
        posLoop()

        if not as_dec_method:
            if tag: bindoffTag(k, "+", "b", xfer_needle+count-1, cs)
            else:
                k.miss("-", f"f{xfer_needle}", *cs)
                k.pause(f"finish {c}")
                k.drop(f"b{xfer_needle+count-1}")
                k.miss("+", f"f{xfer_needle+count}", *cs)
    else: # side == "r", aka binding off in neg direction
        xfer_needle = xfer_needle-count + 1

        if not as_dec_method:
            negLoop("knit", "f")
            if double_bed: posLoop("knit", "b")

        negLoop("xfer", "f")
        if machine.lower() == "kniterate":
            k.rollerAdvance(50)
            k.addRollerAdvance(-50)
        
        if stitchNumber is not None: k.stitchNumber(stitchNumber)
        if not as_dec_method: k.tuck("+", f"b{xfer_needle+count}", *cs)
        k.knit("-", f"b{xfer_needle+count-1}", *cs)
        negLoop()

        if stitchNumber is not None: k.stitchNumber(stitchNumber) #reset it
        if not as_dec_method:
            if tag: bindoffTag(k, "-", "b", xfer_needle, cs)
            else:
                k.miss("+", f"f{xfer_needle+count}", *cs)
                k.pause(f"finish {c}")
                k.drop(f"b{xfer_needle}")
                k.miss("+", f"f{xfer_needle-1}", *cs)

    if not as_dec_method: k.comment("end closed bindoff")
    else: k.comment("end dec by bindoff")


def sheetBindoff(k, start_n, end_n, c, bed="f", gauge=1, mod=None, use_sliders=False, add_tag=True, outhook=False, speedNumber=None, stitchNumber=None, xfer_stitchNumber=None): #TODO: #check support for gauge=2 #TODO: add `as_dec_method` option #*
    cs = c2cs(c) #ensure tuple type

    k.comment(f"begin {bed} bed sheet bindoff")

    if speedNumber is not None: k.speedNumber(speedNumber)

    if mod is None:
        if bed == "f": mod = 0
        else: mod = gauge//2

    if end_n > start_n: # carrier is parked on the left side (start pos)
        left_n = start_n+(-(start_n-mod)%gauge) #shift over so starting on needle that we'll knit
        right_n = end_n-((end_n-mod)%gauge) #shift over so ending on needle that we'll knit
        # left_n, right_n = start_n, end_n
        d = "+"
        needle_range = range(left_n, right_n+1, gauge)

        shift = gauge
        # if bed == "f": R = 1 # rack for transferring from bed2
        # else: R = -1
    else: # carrier is parked on the right side (start neg)
        right_n = start_n-((start_n-mod)%gauge) #shift over so starting on needle that we'll knit
        left_n = end_n+(-(end_n-mod)%gauge) #shift over so ending on needle that we'll knit
        # left_n, right_n = end_n, start_n #check
        d = "-"
        needle_range = range(right_n, left_n-1, -gauge)

        shift = -gauge

    if bed == "f":
        bed2 = "b"
        R = 1 # rack for transferring from bed2
    else:
        bed2 = "f"
        R = -1 # rack for transferring from bed2

    if use_sliders: bed2 += "s"

    last_bn = bnLast(start_n, end_n, gauge, bn_locs=bed, return_type=list)
    
    # edge_n = needle_range[-1]

    for n in needle_range:
        if n == last_bn[1]:
            if add_tag:
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                bindoffTag(k, d, bed, n, cs)
            if outhook: k.outhook(*cs)
            if add_tag: bindoffTag(k, d, bed, n, None) #drop it
            break
        else:
            if stitchNumber is not None: k.stitchNumber(stitchNumber)
            k.knit(d, f"{bed}{n}", *cs)
            k.miss(d, f"{bed}{n+shift}", *cs)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            k.xfer(f"{bed}{n}", f"{bed2}{n}")
            k.rack(R*shift)
            k.xfer(f"{bed2}{n}", f"{bed}{n+shift}")
            k.rack(0)

    if stitchNumber is not None: k.stitchNumber(stitchNumber) #reset
    k.comment(f"end {bed} bed sheet bindoff")


def closedTubeBindoff(k, start_n: int, end_n: int, c: Union[str,Tuple[str]], gauge: int=1, bed_mods: Dict[str,int]=None, use_sliders: bool=False, add_tag: bool=True, outhook: bool=False, speedNumber: Optional[int]=None, stitchNumber: Optional[int]=None, xfer_stitchNumber: Optional[int]=None): #TODO: #check support for gauge=2
    cs = c2cs(c) # ensure tuple type

    if bed_mods is None: bed_mods = {"f": 0, "b": gauge//2} #just use default

    k.comment("begin closed tube bindoff")

    if speedNumber is not None: k.speedNumber(speedNumber)

    first_n = None
    bed, bed2 = None, None
    last_bn = []
    R = None

    if end_n > start_n: # carrier is parked on the left side (start pos)
        d, d2 = "+", "-"
        par = 1
        
        for n in range(start_n, end_n+1):
            if n % gauge == bed_mods["f"]:
                first_n = n
                bed = "f"
                bed2 = "b"
                R = -1
                break
            elif n % gauge == bed_mods["b"]:
                first_n = n
                bed = "b"
                bed2 = "f"
                R = 1
                break

        for n in range(end_n, start_n-1, -1):
            if n % gauge == bed_mods["f"]:
                last_bn = ["f", n]
                break
            elif n % gauge == bed_mods["b"]:
                last_bn = ["b", n]
                break
        
        # last_n = end_n-((end_n-bed_mods[bed2])%gauge) #shift over so ending on needle that we'll knit
        needle_range = range(first_n, end_n+1, gauge)
    else: # carrier is parked on the right side (start neg)
        d, d2 = "-", "+"
        par = -1

        for n in range(start_n, end_n-1, -1):
            if n % gauge == bed_mods["f"]:
                first_n = n
                bed = "f"
                bed2 = "b"
                R = -1
                break
            elif n % gauge == bed_mods["b"]:
                first_n = n
                bed = "b"
                bed2 = "f"
                R = 1
                break
        
        for n in range(end_n, start_n+1):
            if n % gauge == bed_mods["f"]:
                last_bn = ["f", n]
                break
            elif n % gauge == bed_mods["b"]:
                last_bn = ["b", n]
                break
        
        # last_n = end_n+(-(end_n-bed_mods[bed2])%gauge) #shift over so ending on needle that we'll knit
        needle_range = range(first_n, end_n-1, -gauge)
        # shift = -gauge

    shift = abs(bed_mods[bed]-bed_mods[bed2])
    # shift2 = gauge-shift
    
    # shift = -(bed_mods[bed]-bed_mods[bed2])
    # if d == "+": shift2 = gauge-shift+1
    # else: shift2 = -(gauge+shift+1)
    # # shift2 = bed_mods[bed]-bed_mods[bed2]

    if use_sliders: bed2 += "s"
    
    for n in needle_range:
        if n == last_bn[1]: #TODO: change this to last_n (aka last needle based on gauge/mods)
            if add_tag:
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                bindoffTag(k, d, bed, n, cs)
            if outhook: k.outhook(*cs)
            if add_tag: bindoffTag(k, d, bed, n, None) #drop it
            break
        else:
            # if f"{bed}{n}" in empty_needles: continue # don't bind it off because it's empty

            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            k.rack(R*shift*par)
            k.xfer(f"{bed}{n}", f"{bed2}{n+shift*par}")
            k.rack(0)

            if stitchNumber is not None: k.stitchNumber(stitchNumber)
            k.knit(d, f"{bed2}{n+shift*par}", *cs)
            k.miss(d2, f"{bed2}{n+shift*par}", *cs)

            if n+shift != last_bn[1]:
                if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                k.rack(-R*(gauge-shift)*par) # -R since we want to flip the rack direction this time
                k.xfer(f"{bed2}{n+shift*par}", f"{bed}{n+gauge*par}")
                k.rack(0)

                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                k.knit(d, f"{bed}{n+gauge*par}", *cs)
                k.miss(d2, f"{bed}{n+gauge*par}", *cs)

    if stitchNumber is not None: k.stitchNumber(stitchNumber) #reset

    k.comment("end closed tube bindoff")

    return last_bn #in case we want to move it since it should be empty etc.


def openTubeBindoff(k, start_n: int, end_n: int, c: Union[str,Tuple[str]], gauge: int=2, bed_mods: Dict[str,int]=None, use_sliders: bool=False, add_tag: bool=True, outhook: bool=False, speedNumber: Optional[int]=None, stitchNumber: Optional[int]=None, xfer_stitchNumber: Optional[int]=None):
    # https://github.com/textiles-lab/knitout-examples/blob/master/J-30.js
    cs = c2cs(c) # ensure tuple type

    if gauge == 1 and use_sliders == False:
        print("WARNING: toggling `use_sliders` to `True`, since `gauge == 1`, and otherwise, bindoff won't be open.")
        use_sliders = True

    if bed_mods is None: bed_mods = {"f": 0, "b": gauge//2} #just use default

    k.comment("begin open tube bindoff")

    if speedNumber is not None: k.speedNumber(speedNumber)
    # if stitchNumber is not None: k.stitchNumber(stitchNumber)

    if end_n > start_n: # carrier is parked on the left side (start pos)
        d = "+"
        left_n, right_n = start_n, end_n

        first_n_b = right_n-((right_n-bed_mods["b"])%gauge)
        
        last_n_f = right_n-((right_n-bed_mods["f"])%gauge) #shift over so ending on needle that we'll knit
        last_n_b = left_n+(-(left_n-bed_mods["b"])%gauge) #shift over so starting on needle that we'll knit
        
        shifts = [gauge, -gauge]
    else: # carrier is parked on the right side (start neg)
        d = "-"
        left_n, right_n = end_n, start_n

        first_n_b = left_n+(-(left_n-bed_mods["b"])%gauge)

        last_n_f = left_n+(-(left_n-bed_mods["f"])%gauge) #shift over so starting on needle that we'll knit
        last_n_b = right_n-((right_n-bed_mods["b"])%gauge) #shift over so ending on needle that we'll knit
        
        shifts = [-gauge, gauge]

    needle_ranges = {
        "+": range(left_n, right_n+1),
        "-": range(right_n, left_n-1, -1)
    }

    # front:
    if use_sliders: b2 = "bs"
    else: b2 = "b"

    for n in needle_ranges[d]:
        if n == last_n_f:
            if stitchNumber is not None: k.stitchNumber(stitchNumber)
            k.knit(d, f"f{n}", *cs)
            k.tuck(d, f"f{n+shifts[0]}", *cs) # extra loop to help hold things up
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            k.rack(n-first_n_b)
            k.xfer(f"f{n}", f"b{first_n_b}")
            k.rack(0)
            k.drop(f"f{n+shifts[0]}")
        else:
            if n % gauge == bed_mods["f"]:
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                k.knit(d, f"f{n}", *cs)
                k.miss(d, f"f{n+shifts[0]}", *cs)
                if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                k.xfer(f"f{n}", f"{b2}{n}")
                k.rack(shifts[0])
                k.xfer(f"{b2}{n}", f"f{n+shifts[0]}")
                k.rack(0)

    # back:
    d = toggleDirection(d)

    if use_sliders: b2 = "fs"
    else: b2 = "f"

    for n in needle_ranges[d]:
        if n == last_n_b: #knit a tag:
            if add_tag:
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                bindoffTag(k, d, "b", n, cs)
                # d = bindoffTag(k, d, "b", n, cs)
            if outhook: k.outhook(*cs)
            if add_tag: bindoffTag(k, d, "b", n, None) #drop it
            break
        else:
            if n % gauge == bed_mods["b"]:
                if stitchNumber is not None: k.stitchNumber(stitchNumber)
                k.knit(d, f"b{n}", *cs)
                k.miss(d, f"b{n+shifts[1]}", *cs)
                if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
                k.xfer(f"b{n}", f"{b2}{n}")
                k.rack(shifts[0]) #still want the same rack, since we've switched beds
                k.xfer(f"{b2}{n}", f"b{n+shifts[1]}")
                k.rack(0)

    if stitchNumber is not None: k.stitchNumber(stitchNumber) #reset
    k.comment("end open tube bindoff")


# 150 roller for second pass of initial transfer
# 300 roller for knit thru everything after transfer
# 0 roller for transfer
# 200 roller for knit
def bindOp(k, b, n, d, c, machine="swgn2"): #TODO: adjust for gauges other than 1
    cs = c2cs(c) #ensure tuple type

    if b == "f":
        b2 = "b"
        if d == "+":
            rack = 1
            shift = 1
            tuck_d = "-"
        else:
            rack = -1
            shift = -1
            tuck_d = "+"
    else:
        b2 = "f"
        if d == "+":
            rack = -1
            shift = 1
            tuck_d = "-"
        else:
            rack = 1
            shift = -1
            tuck_d = "+"

    k.tuck(tuck_d, f"{b}{n-shift}", *cs)
    k.xfer(f"{b}{n}", f"{b2}{n}")
    k.rack(rack)
    k.xfer(f"{b2}{n}", f"{b}{n+shift}")
    k.rack(0)
    if machine == "kniterate": k.addRollerAdvance(200)
    k.knit(d, f"{b}{n+shift}", *cs)
    k.drop(f"{b}{n-shift}")


def simultaneousBindoff(k, start_needles, end_needles, carriers, speedNumber=None, stitchNumber=None, xfer_stitchNumber=None, machine="swgn2"): #TODO: adjust for gauges other than 1
    k.comment(f"begin double bed simultaneous sheet bindoff")

    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)
    if machine == "kniterate": k.rollerAdvance(0)

    if end_needles["b"] > start_needles["b"]: # carrier is parked on the left side (start pos)
        rack = -1
        left_n, right_n = start_needles["b"], end_needles["b"]
        bd = "+"
        bd_t = "-"
        needle_range_b = range(left_n, right_n) #+1)
    else: # carrier is parked on the right side (start neg)
        rack = 1
        left_n, right_n = end_needles["b"], start_needles["b"]
        bd = "-"
        bd_t = "+"
        needle_range_b = range(right_n, left_n, -1) #-1, -1)

    if end_needles["f"] > start_needles["f"]: # carrier is parked on the left side (start pos)
        left_n, right_n = start_needles["f"], end_needles["f"]
        fd = "+"
        fd_t = "-"
        needle_range_f = range(left_n, right_n) #+1)
    else: # carrier is parked on the right side (start neg)
        left_n, right_n = end_needles["f"], start_needles["f"]
        fd = "-"
        fd_t = "+"
        needle_range_f = range(right_n, left_n, -1) #-1, -1)

    for fn, bn in zip(needle_range_f, needle_range_b): #TODO: add tag and what not
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
        k.rack(rack)
        k.tuck(bd_t, f"b{bn+rack}", carriers["b"])
        k.xfer(f"b{bn}", f"f{bn+rack}")
        if fd != bd:
            k.tuck(fd_t, f"f{fn-rack}", carriers["f"])
            k.xfer(f"f{fn}", f"b{fn-rack}")

        k.rack(2*rack)
        k.xfer(f"f{bn+rack}", f"b{bn-rack}")
        if fd != bd: k.xfer(f"b{fn-rack}", f"f{fn+rack}")

        k.drop(f"b{bn+rack}")
        if xfer_stitchNumber is not None: k.stitchNumber(stitchNumber) # reset it
        k.rack(0)
        if machine == "kniterate": k.addRollerAdvance(100)
        k.knit(bd, f"b{bn-rack}", carriers["b"])
        if fd != bd:
            k.drop(f"f{fn-rack}")
            if machine == "kniterate": k.addRollerAdvance(100)
            k.knit(fd, f"f{fn+rack}", carriers["f"])
        else:
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            k.tuck(fd_t, f"f{fn+rack}", carriers["f"])
            k.xfer(f"f{fn}", f"b{fn}")
            k.rack(-rack)
            k.xfer(f"b{fn}", f"f{fn-rack}")

            k.drop(f"f{fn+rack}")
            if xfer_stitchNumber is not None: k.stitchNumber(stitchNumber) # reset it
            k.rack(0)
            if machine == "kniterate": k.addRollerAdvance(100)
            k.knit(fd, f"f{fn-rack}", carriers["f"])

    k.miss(bd, f"b{end_needles['b']-rack}", carriers["b"])
    if fd == bd: k.miss(fd, f"f{end_needles['f']-rack}", carriers["f"])
    else: k.miss(fd, f"f{end_needles['f']+rack}", carriers["f"])

    k.pause("tail?")

    if machine == "kniterate": k.rollerAdvance(100)
    for _ in range(6):
        k.knit(bd, f"b{end_needles['b']}", carriers["b"])
        k.knit(bd_t, f"b{end_needles['b']}", carriers["b"])

        k.knit(fd, f"f{end_needles['f']}", carriers["f"])
        k.knit(fd_t, f"f{end_needles['f']}", carriers["f"])

    k.comment(f"end double bed simultaneous sheet bindoff")