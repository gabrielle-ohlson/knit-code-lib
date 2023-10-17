from .helpers import c2cs, halveGauge, bnValid, toggleDirection, bnEdges, tuckPattern, knitPass

# --------------------------------
# --- STITCH PATTERN FUNCTIONS ---
# --------------------------------
# if doing gauge == 2, want width to be odd so *actually* have number of stitches
def jersey(k, start_n, end_n, passes, c, bed="f", gauge=1, avoid_bns={"f": [], "b": []}, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None):
    '''
    helper function for jersey stitch pattern

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to knit on in a pass
    * `end_n` (int): the last needle to knit on in a pass (inclusive)
    * `passes` (int): number of rows
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `bed` (str, optional): bed to do the knitting on. Defaults to "f".
    * `gauge` (int, optional): gauge to knit in. Defaults to 1.
    * `avoid_needles` (list, optional): list of needles that should stay empty (aka avoid knitting on). Defaults to [].
    * `inhook` (bool, optional): whether to have the function do an inhook. Defaults to False.
    * `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to False.
    * `tuck_pattern` (bool, optional): whether to include a tuck pattern for extra security when bringing in the carrier (only applicable if `inhook` or `releasehook` == `True`). Defaults to `False`.
    * `speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
    * `stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.

    Raises:
    ------
    * ValueError: _description_

    Returns:
    -------
    * _type_: _description_
    '''
    cs = c2cs(c) # ensure tuple type

    if releasehook and passes < 2 and not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes.")

    k.comment("begin jersey")
    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    if end_n > start_n: d1 = "+"
    else: d1 = "-"

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

    for p in range(passes):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

            releasehook = False

        if p % 2 == 0:
            pass_start_n = start_n
            pass_end_n = end_n
        else:
            pass_start_n = end_n
            pass_end_n = start_n

        knitPass(k, start_n=pass_start_n, end_n=pass_end_n, c=c, bed=bed, gauge=gauge, avoid_bns=avoid_bns)
    if releasehook: # still hasn't happened
        k.releasehook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
        releasehook = False

    k.comment("end jersey")

    if passes % 2 == 0:
        if end_n > start_n: return "+"
        else: return "-"
    else:
        if end_n > start_n: return "-"
        else: return "+"


"""
tube (single bed) example:
-------------------------
e.g. for gauge 2:
if mod == 0
"""
def interlock(k, start_n, end_n, passes, c, bed=None, gauge=1, avoid_bns={"f": [], "b": []}, secure_start_n=False, secure_end_n=False, inhook=False, releasehook=False, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: add tuck pattern
    '''
    Knits on every needle interlock starting on side indicated by which needle value is greater.
    In this function length is the number of total passes knit so if you want an interlock segment that is 20 courses long on each side set length to 40. Useful if you want to have odd amounts of interlock.

    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to knit on in a pass
    * `end_n` (int): the last needle to knit on in a pass (inclusive)
    * `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock)
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `bed` (str, optional): the primary bed, that the loops belong to if knitting a single-bed type of interlock (aka if knitting an open tube with separate stitch patterns on either side).  Valid values are `f`, `b`, or `None`.  If `f` or `b`, will halve the gauge and transfer loops to the other bed to get them in place for knitting, and then finally transfer the loops back to at the end.  Defaults to `None` (which means knitting regular closed double bed interlock).
    * `gauge` (int, optional): gauge to knit in. Defaults to `1`.
    # * `reverse_seq` (bool, optional): whether to reverse the needle sequence we start with for interlock passes.  This is useful for when calling this function one pass at a time, e.g., for open tubes, toggling knitting on either bed (so you might, for example, knit on the front bed and start with `passes=1, c=carrier, bed="f", gauge=2, reverse_seq=False`, then do a pass on the back bed, and then call `passes=1, c=carrier, bed="f", gauge=2, reverse_seq=True`).  Otherwise, you can just ignore this.
    * secure_start_n and ...
   
    * `empty_needles` (list, optional): list of needles that should stay empty (aka avoid knitting on). Defaults to `[]`.
    * `current_bed` (str, optional): the bed(s) that current has knitting (valid values are: "f" [front] and "b" [back]); if value is None, will assume that the loops are already in position for interlock (e.g. not knitting circular half-gauge interlock). Defaults to `None`.
    * `home_bed` (str, optional): the bed to transfer the loops back to at the end (if applicable); NOTE: this should only be added if knitting if half gauge tube with stitch patterns inserted on one bed (since the function will act accordingly). Defaults to `None`.
    * secure_start_n and ...
    * secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * `inhook` (bool, optional): whether to have the function do an inhook. Defaults to False.
    * `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to False.
    * `speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
    * `stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
    * `xfer_speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
    * `xfer_stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
    '''
    cs = c2cs(c) # ensure tuple type

    k.comment('begin interlock')
    if inhook: k.inhook(*cs)

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if end_n > start_n: #first pass is pos
        d1, d2 = "+", "-"
        left_n = start_n
        right_n = end_n
        seq1_idx, seq2_idx = 1, 0 #this ensures that if `passes=1` (e.g., when knitting open tubes and switching between beds), we are still toggling which sequence we start with for the first pass in the function
    else: #first pass is neg
        d1, d2 = "-", "+"
        left_n = end_n
        right_n = start_n
        seq1_idx, seq2_idx = 0, 1

    if bed is None:
        single_bed = False
        bed, bed2 = "f", "b"
        
        bn_locs = {"f": [n for n in range(left_n, right_n+1) if bnValid("f", n, gauge) and n not in avoid_bns.get("f", [])], "b": [n for n in range(left_n, right_n+1) if bnValid("b", n, gauge) and n not in avoid_bns.get("b", [])]}
    else:
        single_bed = True
        if bed == "f": bed2 = "b"
        else: bed2 = "f"

        bn_locs = {bed: [n for n in range(left_n, right_n+1) if bnValid(bed, n, gauge) and n not in avoid_bns[bed]], bed2: []}

    secure_needles = {"f": [], "b": []}

    edge_bns = bnEdges(left_n, right_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)

    if d1 == "+": #first pass is pos
        if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    else: #first pass is neg
        if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    
    # seq2_idx = abs(seq1_idx-1)
    
    mods2 = halveGauge(gauge, bed)

    n_ranges = {"+": range(left_n, right_n+1), "-": range(right_n, left_n-1, -1)}

    if single_bed:
        mods4 = [halveGauge(gauge*2, mods2[0]), halveGauge(gauge*2, mods2[1])]

        # transfer to get loops in place:
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in range(left_n, right_n+1):
            if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed]: continue
            elif n % (gauge*2) == mods2[1]: k.xfer(f"{bed}{n}", f"{bed2}{n}")
        
        # reset settings
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

        def passSequence1(d):
            for n in n_ranges[d]:
                if n % (gauge*4) == mods4[0][seq1_idx] and n not in avoid_bns[bed]: k.knit(d, f"{bed}{n}", *cs)
                elif n % (gauge*4) == mods4[1][seq1_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
                elif n == n_ranges[d][-1]: k.miss(d, f"{bed}{n}", *cs)

        def passSequence2(d):
            for n in n_ranges[d]:
                if n % (gauge*4) == mods4[0][seq2_idx] and n not in avoid_bns[bed]: k.knit(d, f"{bed}{n}", *cs)
                elif n % (gauge*4) == mods4[1][seq2_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
                elif n == n_ranges[d][-1]: k.miss(d, f"{bed}{n}", *cs)
    else:
        def passSequence1(d):
            for n in n_ranges[d]:
                if n % (gauge*2) == mods2[seq1_idx] and n not in avoid_bns[bed]: k.knit(d, f"{bed}{n}", *cs)
                elif n % (gauge*2) == mods2[seq2_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
                elif n == n_ranges[d][-1]: k.miss(d, f"{bed}{n}", *cs)
        
        def passSequence2(d):
            for n in n_ranges[d]:
                if n % (gauge*2) == mods2[seq2_idx] and n not in avoid_bns[bed]: k.knit(d, f"{bed}{n}", *cs)
                elif n % (gauge*2) == mods2[seq1_idx] and n not in avoid_bns[bed2]: k.knit(d, f"{bed2}{n}", *cs)
                elif n == n_ranges[d][-1]: k.miss(d, f"{bed}{n}", *cs)

    #--- the knitting ---
    for p in range(passes):
        if releasehook and p == 2: k.releasehook(*cs)
        if p % 2 == 0: passSequence1(d1)
        else: passSequence2(d2)

    # return the loops back
    if single_bed:
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in range(left_n, right_n+1):
            if avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles[bed]: continue
            elif n % (gauge*2) == mods2[1]: k.xfer(f"{bed2}{n}", f"{bed}{n}")
        
        # reset settings
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment('end interlock')


def rib(k, start_n, end_n, passes, c, bed=None, sequence="fb", gauge=1, bed_loops={"f": [], "b": []}, avoid_bns={"f": [], "b": []}, secure_start_n=False, secure_end_n=False, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: #check to make sure this is working well for gauge > 1 #*
    '''
    *k is the knitout Writer
    *end_n is the last needle
    *start_n is the first needle
    *passes is total number of passes to knit
    *c is the carrier
    *bed is the bed that we want to knit on & to use to determine parity
    *bed_loops (optional) indicates which bed working loops are currently on
    *sequence is the repeating rib pattern (e.g. 'fb' of 'bf' for 1x1 [first bed indicates which bed left-most needle will be on], 'ffbb' for 2x2, 'fbffbb' for 1x1x2x2, etc.)
    *gauge is gauge
    '''
    cs = c2cs(c) # ensure tuple type

    k.comment(f"begin rib ({sequence})")

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if gauge > 1:
        gauged_sequence = ''
        for char in sequence:
            gauged_sequence += char * gauge
        sequence = gauged_sequence
    
    if end_n > start_n: #first pass is pos
        d1 = "+"
        d2 = "-"
        n_ranges = {d1: range(start_n, end_n+1), d2: range(end_n, start_n-1, -1)}
    else: #first pass is neg
        d1 = "-"
        d2 = "+"
        n_ranges = {d1: range(start_n, end_n-1, -1), d2: range(end_n, start_n+1)}

    if bed is None:
        bed = "f"
        bn_locs = bed_loops.copy()
    else:
        bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check

    secure_needles = {"f": [], "b": []}

    if d1 == "+": #first pass is pos
        edge_bns = bnEdges(start_n, end_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    else: #first pass is neg
        edge_bns = bnEdges(end_n, start_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

    # now let's make sure we have *all* the info in one dict
    xfer_loops = {"f": [n for n in list(set(bn_locs.get("f", [])+bed_loops.get("f", []))) if sequence[n % len(sequence)] == "b" and bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["f"]], "b": [n for n in list(set(bn_locs.get("b", [])+bed_loops.get("b", []))) if sequence[n % len(sequence)] == "f" and bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["b"]]}

    if len(xfer_loops["f"]) or len(xfer_loops["b"]): # indicates that we might need to start by xferring to proper spots
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in n_ranges[d1]: #TODO: #check adjustment for gauge
            if n in xfer_loops["f"]: k.xfer(f"f{n}", f"b{n}")
            elif n in xfer_loops["b"]: k.xfer(f"b{n}", f"f{n}")
            # if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or not bnValid(bed, n, gauge): continue
            # else:
            #     if sequence[n % len(sequence)] == bed2 and n in xfer_loops[bed] and n not in secure_needles[bed]: k.xfer(f"{bed}{n}", f"{bed2}{n}")
            #     elif sequence[n % len(sequence)] == bed and n in xfer_loops[bed2] and n not in secure_needles[bed2]: k.xfer(f"{bed2}{n}", f"{bed}{n}")
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    #TODO: maybe change stitch size for rib? k.stitchNumber(math.ceil(specs.stitchNumber/2)) (if so -- remember to reset settings)
    for p in range(passes):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
        if p % 2 == 0:
            d = d1
            last_n = end_n
        else:
            d = d2
            last_n = start_n

        for n in n_ranges[d]:
            if n in secure_needles["f"] and n not in bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
            elif n in secure_needles["b"] and n not in bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
            elif sequence[n % len(sequence)] == "f" and n not in avoid_bns.get("f", []) and bnValid(bed, n, gauge): k.knit(d, f"f{n}", *cs) #xferred it or bed == "f", ok to knit
            elif sequence[n % len(sequence)] == "b" and n not in avoid_bns.get("b", []) and bnValid(bed, n, gauge): k.knit(d, f"b{n}", *cs) #xferred it or bed == "b", ok to knit
            elif n == last_n: k.miss(d, f"f{n}", *cs)
    
    # return the loops:
    if len(xfer_loops["f"]) or len(xfer_loops["b"]):
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in n_ranges[d1]:
            if n in xfer_loops["f"]: k.xfer(f"b{n}", f"f{n}")
            elif n in xfer_loops["b"]: k.xfer(f"f{n}", f"b{n}")

            # if bnValid(bed, n, gauge) and n not in avoid_bns[bed] and n not in avoid_bns[bed2]:
            #     if sequence[n % len(sequence)] == bed2 and n in bn_locs[bed]: k.xfer(f"{bed2}{n}", f"{bed}{n}")
            #     elif sequence[n % len(sequence)] == bed and n in bn_locs[bed2]: k.xfer(f"{bed}{n}", f"{bed2}{n}")
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment("end rib")

    if passes % 2 == 0:
        if end_n > start_n: return "+"
        else: return "-"
    else:
        if end_n > start_n: return "-"
        else: return "+"


def altKnitTuck(k, start_n, end_n, passes, c, bed="f", sequence="kt", tuck_sequence="mt", gauge=1, avoid_bns={"f": [], "b": []}, inhook=False, releasehook=False, tuck_pattern=True):
    '''
    *TODO
    '''
    cs = c2cs(c) # ensure tuple type

    k.comment(f"begin alt knit/tuck ({sequence})")

    if end_n > start_n: d1 = "+"
    else: d1 = "-"

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs) #TODO: add avoid bns to `tuckPattern` func

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    mods2 = halveGauge(gauge, bed)

    # if gauge > 1: if not bnValid(bed, start_n, gauge) or not bnValid(bed, end_n, gauge): raise Warning(f"with gauge: {gauge} > 1, we want both edge needles to be on the primary bed, {bed}, to ensure there are loops on the end needle => the stitch count is accurate.")

    for p in range(passes):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

        if p % 2 == 0:
            pass_start_n = start_n
            pass_end_n = end_n
        else:
            pass_start_n = end_n
            pass_end_n = start_n
        if sequence[p % len(sequence)] == 'k':
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

    k.comment("end alt knit/tuck ({sequence})")

    if pass_end_n > pass_start_n: return "-" #just knit a pos pass
    else: return "+"


def garter(k, start_n, end_n, passes, c, bed=None, sequence="fb", gauge=1, bed_loops={"f": [], "b": []}, avoid_bns={"f": [], "b": []}, secure_start_n=True, secure_end_n=True, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    '''
    * k is knitout Writer
    * start_n is the starting needle to knit on
    * end_n is the last needle to knit on
    * passes is total passes knit
    * c is carrier
    * bed is the bed it belongs to
    * sequence is the number of knit/purl rows to knit before switch to the other (e.g. 2 -- knit 2 rows, purl 2 rows [repeat]) #TODO: alter (and alter in all other code)
    * secure_start_n and *secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * gauge is... gauge
    '''
    cs = c2cs(c) # ensure tuple type

    if end_n > start_n: #first pass is pos
        d1, d2 = "+", "-"
        n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}
    else: #first pass is neg
        d1, d2 = "-", "+"
        n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

    if bed is not None: bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check
    else: bn_locs = bed_loops.copy()

    pattern_rows = {"f": sequence.count("f"), "b": sequence.count("b")}

    k.comment(f'begin {pattern_rows["f"]}x{pattern_rows["b"]} garter')

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    secure_needles = {"f": [], "b": []}

    if d1 == "+": #first pass is pos
        edge_bns = bnEdges(start_n, end_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    else: #first pass is neg
        edge_bns = bnEdges(end_n, start_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)
    
    # for now: (will be reset)
    d = d1

    if type(pattern_rows) != dict:
        pat_rows = {}
        pat_rows["f"] = pattern_rows
        pat_rows["b"] = pattern_rows
        pattern_rows = pat_rows
    
    b1 = sequence[0]
    b2 = "f" if b1 == "b" else "b"

    xfer_loops = {b2: [n for n in list(set(bn_locs[b2]+bed_loops.get(b2, []))) if bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles[b2]]}

    if len(xfer_loops[b2]):
        for n in n_ranges[d2]:
            if n in xfer_loops[b2]: k.xfer(f"{b2}{n}", f"{b1}{n}")
    
    for p in range(passes):
        if p % 2 == 0: d = d1
        else: d = d2

        if p > 0 and b1 != sequence[p % len(sequence)]: # transfer
            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            
            for n in n_ranges[d]:
                if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
                elif bnValid(bed, n, gauge) and n not in secure_needles[b1]: k.xfer(f"{b1}{n}", f"{sequence[p % len(sequence)]}{n}")

            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)

        b1 = sequence[p % len(sequence)]
        b2 = "f" if b1 == "b" else "b"

        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

        for n in n_ranges[d]:
            if bnValid(bed, n, gauge):
                if n in secure_needles[b2] or (n in avoid_bns[b1] and n not in avoid_bns[b2]): k.knit(d, f"{b2}{n}", *cs)
                elif n not in avoid_bns[b1]: k.knit(d, f"{b1}{n}", *cs)
                elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
            elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
    
    #return loops
    b2 = "f" if b1 == "b" else "b"
    if len(xfer_loops.get(b2, [])):
        for n in n_ranges[d]:
            if n in xfer_loops[b2]: k.xfer(f"{b1}{n}", f"{b2}{n}")

    if type(pattern_rows) == dict: k.comment(f'end {pattern_rows["f"]}x{pattern_rows["b"]} garter')
    else: k.comment(f'end {pattern_rows}x{pattern_rows} garter')

    next_direction = "-" if d == "+" else "+"
    return next_direction


def tuckGarter(k, start_n, end_n, passes, c, bed="f", sequence="ffb", gauge=1, bed_loops={"f": [], "b": []}, avoid_bns={"f": [], "b": []}, secure_start_n=False, secure_end_n=False, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    '''
    * k is knitout Writer
    * start_n is the starting needle to knit on
    * end_n is the last needle to knit on
    * passes is total passes knit
    * c is carrier
    * bed is the bed to start on
    * pattern_rows is the number of knit/purl rows to knit before switch to the other (e.g. 2 -- knit 2 rows, purl 2 rows [repeat])
    * secure_start_n and *secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * gauge is... gauge
    '''
    cs = c2cs(c) # ensure tuple type

    if bed is not None: bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check
    else:
        bed = "f"
        bn_locs = bed_loops.copy()

    pattern_rows = {"f": sequence.count("f"), "b": sequence.count("b")}

    if type(pattern_rows) == dict: k.comment(f"begin {pattern_rows['f']}x{pattern_rows['b']} garter")
    else: k.comment(f"begin {pattern_rows}x{pattern_rows} garter")

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    secure_needles = {"f": [], "b": []}

    if bed == "b": bed2 = "f"
    else: bed2 = "b"

    if end_n > start_n: #first pass is pos
        d1, d2 = "+", "-"
        n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}

        edge_bns = bnEdges(start_n, end_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    else: #first pass is neg
        d1, d2 = "-", "+"
        n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

        edge_bns = bnEdges(end_n, start_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

    # for now: (will be reset)
    d = d1

    if type(pattern_rows) != dict:
        pat_rows = {"f": pattern_rows, "b": pattern_rows}
        pattern_rows = pat_rows
    
    pattern_rows["f"] += 1 #for the tucks

    b1 = sequence[p % len(sequence)]
    b2 = "f" if b1 == "b" else "b"

    xfer_loops = {b2: [n for n in list(set(bn_locs[b2]+bed_loops.get(b2, []))) if bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles[b2]]}

    if len(xfer_loops[b2]):
        for n in n_ranges[d2]:
            if n in xfer_loops[b2]: k.xfer(f"{b2}{n}", f"{b1}{n}")

    pass_ct = 0
    for p in range(passes):
        if p > 0: b1, b2 = b2, b1 #toggle
        
        # if p % 2 == 0:
        #     b1 = bed
        #     b2 = bed2
        # else:
        #     b1 = bed2
        #     b2 = bed

        for r in range(pattern_rows[b1]):
            if releasehook and pass_ct == 2:
                k.releasehook(*cs)
                if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
            
            if b1 == "f" and r == 0:
                for n in n_ranges[d]:
                    if n not in avoid_bns[b1] and n % (gauge*2) == 0 and n != edge_bns[0][1] and n != edge_bns[1][1]: k.tuck(d, f"{b1}{n}", *cs)
                    elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
            else:
                for n in n_ranges[d]:
                    if bnValid(bed, n, gauge):
                        if n in secure_needles[b2] or (n in avoid_bns[b1] and n not in avoid_bns[b2]): k.knit(d, f"{b2}{n}", *cs)
                        elif n not in avoid_bns[b1]: k.knit(d, f"{b1}{n}", *cs)
                        elif n == end_n: k.miss(d, f"{b1}{n}", *cs)
                    elif n == end_n: k.miss(d, f"{b1}{n}", *cs)

            # if d == d1: d = d2
            # else: d = d1
            d = toggleDirection(d)

            pass_ct += 1
            if pass_ct == passes: break

        if pass_ct == passes and b1 == bed: break #don't need to return it

        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            
        for n in n_ranges[d]:
            if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles.get("f", []) or n in secure_needles.get("b", []) or not bnValid(bed, n, gauge): continue
            elif n in bn_locs[bed2]: k.xfer(f"{bed}{n}", f"{bed2}{n}") #TODO: #check
            else: k.xfer(f"{b1}{n}", f"{b2}{n}")

        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

        if pass_ct == passes: break

    if type(pattern_rows) == dict: k.comment(f"end {pattern_rows['f']-1}x{pattern_rows['b']} garter")
    else: k.comment(f"end {pattern_rows}x{pattern_rows} garter")

    return d #return the direction that the next pass should be, so know which to use next


def seed(k, start_n, end_n, passes, c, bed="f", sequence="fb", gauge=1, bed_loops={"f": [], "b": []}, avoid_bns={"f": [], "b": []}, secure_start_n=True, secure_end_n=True, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    cs = c2cs(c) # ensure tuple type

    k.comment(f"begin seed ({sequence})")

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if bed is not None: bn_locs = {bed: [n for n in n_ranges[d1] if bnValid(bed, n, gauge)]} #make sure we transfer to get them where we want #TODO; #check
    else: bn_locs = bed_loops.copy()

    if gauge > 1:
        gauged_sequence = ''
        for char in sequence:
            gauged_sequence += char * gauge
        sequence = gauged_sequence

    secure_needles = {"f": [], "b": []}

    if end_n > start_n: #first pass is pos
        d1, d2 = "+", "-"
        n_ranges = {d1: range(start_n, end_n+1), d2: range(end_n, start_n-1, -1)}

        edge_bns = bnEdges(start_n, end_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_start_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_end_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])
    else: #first pass is neg
        d1, d2 = "-", "+"
        n_ranges = {d1: range(start_n, end_n-1, -1), d2: range(end_n, start_n+1)}

        edge_bns = bnEdges(end_n, start_n, gauge, bed_loops=bn_locs, avoid_bns=avoid_bns, return_type=list)
        if secure_end_n: secure_needles[edge_bns[0][0]].append(edge_bns[0][1])
        if secure_start_n: secure_needles[edge_bns[1][0]].append(edge_bns[1][1])

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)
    
    # if bed == "f": bed2 = "b"
    # else: bed2 = "f"

    xfer_loops = {"f": [n for n in list(set(bn_locs.get("f", [])+bed_loops.get("f", []))) if sequence[n % len(sequence)] == "b" and bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["f"]], "b": [n for n in list(set(bn_locs.get("b", [])+bed_loops.get("b", []))) if sequence[n % len(sequence)] == "f" and bnValid(bed, n, gauge) and n not in avoid_bns.get("f", []) and n not in avoid_bns.get("b", []) and n not in secure_needles["b"]]}

    if len(xfer_loops["f"]) or len(xfer_loops["b"]): # indicates that we might need to start by xferring to proper spots
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in n_ranges[d1]:
            if n in xfer_loops["f"]: k.xfer(f"f{n}", f"b{n}")
            elif n in xfer_loops["b"]: k.xfer(f"b{n}", f"f{n}")
            # if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
            # elif n not in secure_needles and bnValid(bed, n, gauge): 
            #     if sequence[n % len(sequence)] == bed2 and n in bn_locs[bed]: k.xfer(f"{bed}{n}", f"{bed2}{n}")
            #     elif sequence[n % len(sequence)] == bed and n in bn_locs[bed2]: k.xfer(f"{bed2}{n}", f"{bed}{n}")
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    for p in range(passes):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it
        
        if p % 2 == 0:
            d = d1
            last_n = end_n

            for n in n_ranges[d]:
                if bnValid(bed, n, gauge):
                    if n in secure_needles["f"] and n not in bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
                    elif n in secure_needles["b"] and n not in bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
                    else:
                        if n not in avoid_bns.get("f", []) and (sequence[n % len(sequence)] == "f" or (sequence[n % len(sequence)] == "b" and n in avoid_bns.get("b", []))): k.knit(d, f"f{n}", *cs) #xferred it or bed == "f", ok to knit
                        elif n not in avoid_bns.get("b", []) and (sequence[n % len(sequence)] == "b" or (sequence[n % len(sequence)] == "f" and n in avoid_bns.get("f", []))): k.knit(d, f"b{n}", *cs) #xferred it or bed == "b", ok to knit
                        elif n == last_n: k.miss(d, f"f{n}", *cs)
                elif n == last_n: k.miss(d, f"f{n}", *cs)
            
            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            if p < passes-1:
                for n in n_ranges[d]:
                    if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
                    elif bnValid(bed, n, gauge):
                        if sequence[n % len(sequence)] == "f" and n not in secure_needles["f"]: k.xfer(f"f{n}", f"b{n}")
                        elif sequence[n % len(sequence)] == "b" and n not in secure_needles["b"]: k.xfer(f"b{n}", f"f{n}")
            else:
                for n in n_ranges[d]:
                    if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles["f"] or n in secure_needles["b"]: continue
                    elif bnValid(bed, n, gauge):
                        if sequence[n % len(sequence)] == "f" and n in xfer_loops.get("b", []): k.xfer(f"f{n}", f"b{n}")
                        elif sequence[n % len(sequence)] == "b" and n in xfer_loops.get("f", []): k.xfer(f"b{n}", f"f{n}")

            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)
        else:
            d = d2
            last_n = start_n

            for n in n_ranges[d]:
                if bnValid(bed, n, gauge):
                    if n in secure_needles["f"] and n not in bn_locs.get("b", []): k.knit(d, f"f{n}", *cs) #TODO: #check
                    elif n in secure_needles["b"] and n not in bn_locs.get("f", []): k.knit(d, f"b{n}", *cs) #TODO: #check
                    else:
                        if n not in avoid_bns.get("b", []) and (sequence[n % len(sequence)] == "f" or (sequence[n % len(sequence)] == "b" and n in avoid_bns.get("f", []))): k.knit(d, f"b{n}", *cs) #xferred it or bed == "f", ok to knit
                        elif n not in avoid_bns.get("f", []) and (sequence[n % len(sequence)] == "b" or (sequence[n % len(sequence)] == "f" and n in avoid_bns.get("b", []))): k.knit(d, f"f{n}", *cs) #xferred it or bed == "b", ok to knit
                        elif n == last_n: k.miss(d, f"f{n}", *cs)
                elif n == last_n: k.miss(d, f"f{n}", *cs)

            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            if p < passes-1:
                for n in n_ranges[d]:
                    if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []): continue
                    elif n not in secure_needles and bnValid(bed, n, gauge):
                        if sequence[n % len(sequence)] == "f": k.xfer(f"b{n}", f"f{n}")
                        else: k.xfer(f"f{n}", f"b{n}")
            else:
                for n in n_ranges[d]: #TODO: adjust for gauge
                    if n in avoid_bns.get("f", []) or n in avoid_bns.get("b", []) or n in secure_needles["f"] or n in secure_needles["b"]: continue
                    elif bnValid(bed, n, gauge):
                        if sequence[n % len(sequence)] == "f" and n in xfer_loops.get("f", []): k.xfer(f"b{n}", f"f{n}")
                        elif sequence[n % len(sequence)] == "b" and n in xfer_loops.get("b", []): k.xfer(f"f{n}", f"b{n}")
            
            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment(f"end seed ({sequence})")

    if bnValid(bed, n, gauge) % 2 == 0:
        if end_n > start_n: return "+"
        else: return "-"
    else:
        if end_n > start_n: return "-"
        else: return "+"


def tuckStitch(k, start_n, end_n, passes, c, bed="f", sequence="kt", gauge=1, avoid_bns={"f": [], "b": []}, inhook=False, releasehook=False, tuck_pattern=True):
    cs = c2cs(c) # ensure tuple type

    k.comment(f"begin tuck stitch ({sequence})")

    if end_n > start_n:
        d1, d2 = "+", "-"
        n_ranges = {"+": range(start_n, end_n+1), "-": range(end_n, start_n-1, -1)}
    else:
        d1, d2 = "-", "+"
        n_ranges = {"-": range(start_n, end_n-1, -1), "+": range(end_n, start_n+1)}

    edge_bns = bnEdges(n_ranges["+"][0], n_ranges["+"][-1], gauge, bed_loops={bed: [n for n in n_ranges["+"] if bnValid(bed, n, gauge)]}, avoid_bns=avoid_bns, return_type=list)
    
    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=cs)

    if releasehook and passes < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    for p in range(passes):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=d1, c=None) # drop it

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
            if bnValid(bed, n, gauge) and n not in avoid_bns[bed] and (n % (gauge*2) == 0 or n % (gauge*2) == gauge):
                if sequence[(n*gauge) % len(sequence)] == do_knit or n == edge_bns[0][1] or n == edge_bns[1][1]: k.knit(d, f"{bed}{n}", *cs)
                else: k.tuck(d, f"{bed}{n}", *cs)
            elif n == pass_end_n: k.miss(d, f"{bed}{n}", *cs)

    k.comment("end tuck stitch")

    # return next direction:
    if pass_end_n > pass_start_n: return "-" #just knit a pos pass
    else: return "+"
