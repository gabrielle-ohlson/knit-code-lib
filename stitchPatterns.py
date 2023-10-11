from .helpers import c2cs, convertToBN, includeNSecureSides, tuckPattern, knitPass

# --------------------------------
# --- STITCH PATTERN FUNCTIONS ---
# --------------------------------
# if doing gauge == 2, want width to be odd so *actually* have number of stitches
def jersey(k, start_n, end_n, length, c, bed='f', gauge=1, empty_needles=[], inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None):
    '''
    helper function for jersey stitch pattern

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to knit on in a pass
    * `end_n` (int): the last needle to knit on in a pass (inclusive)
    * `length` (int): number of rows
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `bed` (str, optional): bed to do the knitting on. Defaults to 'f'.
    * `gauge` (int, optional): gauge to knit in. Defaults to 1.
    * `empty_needles` (list, optional): list of needles that should stay empty (aka avoid knitting on). Defaults to [].
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
    cs = c2cs(c) # ensure list type

    if releasehook and length < 2 and not tuck_pattern: raise ValueError("not safe to releasehook with less than 2 passes.")

    k.comment('begin jersey')
    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    if end_n > start_n: init_dir = '+'
    else: init_dir = '-'

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=cs)

    for p in range(0, length):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=None) # drop it

            releasehook = False

        if p % 2 == 0:
            pass_start_n = start_n
            pass_end_n = end_n
        else:
            pass_start_n = end_n
            pass_end_n = start_n
        knitPass(k, start_n=pass_start_n, end_n=pass_end_n, c=c, bed=bed, gauge=gauge, empty_needles=empty_needles)
    if releasehook: # still hasn't happened
        k.releasehook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=None) # drop it
        releasehook = False

    k.comment('end jersey')

    if length % 2 == 0:
        if end_n > start_n: return '+'
        else: return '-'
    else:
        if end_n > start_n: return '-'
        else: return '+'


def interlock(k, start_n, end_n, length, c, gauge=1, start_condition=1, empty_needles=[], current_bed=None, home_bed=None, secure_start_n=False, secure_end_n=False, inhook=False, releasehook=False, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: add tuck pattern
    '''
    Knits on every needle interlock starting on side indicated by which needle value is greater.
    In this function length is the number of total passes knit so if you want an interlock segment that is 20 courses long on each side set length to 40. Useful if you want to have odd amounts of interlock.

    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (int): the initial needle to knit on in a pass
    * `end_n` (int): the last needle to knit on in a pass (inclusive)
    * `length` (int): total number of rows to knit (NOTE: there are two passes per row, so for an uneven number of passes do e.g. `length=0.5` for 1 pass)
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating)
    * `gauge` (int, optional): gauge to knit in. Defaults to `1`.
    * `start_condition` (int, optional): dictates which needles first pass of interlock knits only (usually you can just ignore this unless you want to do something very specific). #TODO: document better
    * `empty_needles` (list, optional): list of needles that should stay empty (aka avoid knitting on). Defaults to `[]`.
    * `current_bed` (str, optional): the bed(s) that current has knitting (valid values are: 'f' [front] and 'b' [back]); if value is None, will assume that the loops are already in position for interlock (e.g. not knitting circular half-gauge interlock). Defaults to `None`.
    * `home_bed` (str, optional): the bed to transfer the loops back to at the end (if applicable); NOTE: this should only be added if knitting if half gauge tube will stitch patterns inserted on one bed (since the function will act accordingly). Defaults to `None`.
    * secure_start_n and ...
    * secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * `inhook` (bool, optional): whether to have the function do an inhook. Defaults to False.
    * `releasehook` (bool, optional): whether to have the function do a releasehook (after 2 passes). Defaults to False.
    * `speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension. Defaults to `None`.
    * `stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension. Defaults to `None`.
    * `xfer_speedNumber` (int, optional): value to set for the `x-speed-number` knitout extension when transferring. Defaults to `None`.
    * `xfer_stitchNumber` (int, optional): value to set for the `x-stitch-number` knitout extension when transferring. Defaults to `None`.
    '''
    cs = c2cs(c) # ensure list type

    k.comment('begin interlock')
    if inhook: k.inhook(*cs)

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    empty_needles = convertToBN(empty_needles)
        
    length *= 2
    length = int(length) #incase doing e.g. .5 length (only a pass)

    if end_n > start_n: #first pass is pos
        beg = 0
        left_n = start_n
        right_n = end_n
    else: #first pass is neg
        beg = 1
        length += 1
        left_n = end_n
        right_n = start_n
        if start_condition == 1: start_condition = 2 #switch since starting at 1
        else: start_condition = 1
    
    if home_bed is not None:
        if home_bed == 'f':
            homeCondition = lambda n: (n % gauge == 0)
            travelBed = 'b'
        else:
            homeCondition = lambda n: ((n-1) % gauge == 0)
            travelBed = 'f'
    

    def frontBed1(n, direction):
        if ((n == start_n and secure_start_n) or (n == end_n and secure_end_n)) and current_bed == 'b': return False

        if f'f{n}' not in empty_needles and n % gauge == 0 and (((n//gauge) % 2) == 0):
            k.knit(direction, f'f{n}', *cs)
            return True
        else: return False
    
    
    def backBed1(n, direction):
        if ((n == start_n and secure_start_n) or (n == end_n and secure_end_n)) and current_bed == 'f': return False

        if f'b{n}' not in empty_needles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) == 0):
            k.knit(direction, f'b{n}', *cs)
            return True
        else: return False
    
    def frontBed2(n, direction):
        if ((n == start_n and secure_start_n) or (n == end_n and secure_end_n)) and current_bed == 'b': return False

        if f'f{n}' not in empty_needles and n % gauge == 0 and (((n//gauge) % 2) != 0):
            k.knit(direction, f'f{n}', *cs)
            return True
        else: return False
    

    def backBed2(n, direction):
        if ((n == start_n and secure_start_n) or (n == end_n and secure_end_n)) and current_bed == 'f': return False

        if f'b{n}' not in empty_needles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) != 0):
            k.knit(direction, f'b{n}', *cs)
            return True
        else: return False

    if current_bed is not None: #current_bed indicates that we need to start by xferring to proper spots
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        if current_bed == 'f':
            other_bed = 'b'
            currCondition = lambda n: (n % gauge == 0)
        else:
            other_bed = 'f'
            currCondition = lambda n: ((n-1) % gauge == 0)

        for n in range(left_n, right_n+1):
            if (n == start_n and secure_start_n) or (n == end_n and secure_end_n): continue

            if currCondition(n) and f'{current_bed}{n}' not in empty_needles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{current_bed}{n}', f'{other_bed}{n}')
        
        # reset settings
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    #for if home bed
    def homeBed1(n, direction):
        if homeCondition(n) and f'{home_bed}{n}' not in empty_needles and ((n//gauge) % (2*gauge) == 0):
            k.knit(direction, f'{home_bed}{n}', *cs)
            return True
        else: return False
    

    def travelBed1(n, direction):
        if (n == start_n and secure_start_n) or (n == end_n and secure_end_n):
            if homeCondition(n):
                k.knit(direction, f'{home_bed}{n}', *cs)
                return True
            else: return False

        if homeCondition(n) and f'{travelBed}{n}' not in empty_needles and ((n//gauge) % (2*gauge) == (gauge+1)): #check for gauge 1
            k.knit(direction, f'{travelBed}{n}', *cs)
            return True
        else: return False
    

    def homeBed2(n, direction):
        if homeCondition(n) and f'{home_bed}{n}' not in empty_needles and ((n//gauge) % (2*gauge) == gauge):
            k.knit(direction, f'{home_bed}{n}', *cs)
            return True
        else: return False
    

    def travelBed2(n, direction):
        if (n == start_n and secure_start_n) or (n == end_n and secure_end_n):
            if homeCondition(n):
                k.knit(direction, f'{home_bed}{n}', *cs)
                return True
            else: return False

        if homeCondition(n) and f'{travelBed}{n}' not in empty_needles and ((n//gauge) % (2*gauge) == (gauge-1)): #check for gauge 1
            k.knit(direction, f'{travelBed}{n}', *cs)
            return True
        else: return False


    #--- the knitting ---
    for h in range(beg, length):
        if releasehook and h-beg == 2: k.releasehook(*cs)
        if h % 2 == 0:
            for n in range(left_n, right_n+1):
                if start_condition == 1: #first pass of interlock will knit on 0, 1, 4, 5, etc.
                    if home_bed is None or gauge == 1:
                        if frontBed1(n, '+'): continue
                        elif backBed1(n, '+'): continue
                        elif n == right_n: k.miss('+', f'f{n}', *cs)
                    else:
                        if homeBed1(n, '+'): continue
                        elif travelBed1(n, '+'): continue
                        elif n == right_n: k.miss('+', f'f{n}', *cs)
                else: #first pass of interlock will knit on 2, 3, 6, 7, etc.
                    if home_bed is None or gauge == 1:
                        if frontBed2(n, '+'): continue
                        elif backBed2(n, '+'): continue
                        elif n == right_n: k.miss('+', f'f{n}', *cs)
                    else:
                        if homeBed2(n, '+'): continue
                        elif travelBed2(n, '+'): continue
                        elif n == right_n: k.miss('+', f'f{n}', *cs)
        else:
            for n in range(right_n, left_n-1, -1):
                if start_condition == 2:
                    if home_bed is None or gauge == 1:
                        if frontBed1(n, '-'): continue
                        elif backBed1(n, '-'): continue
                        elif n == left_n: k.miss('-', f'f{n}', *cs)
                    else:
                        if homeBed1(n, '-'): continue
                        elif travelBed1(n, '-'): continue
                        elif n == left_n: k.miss('-', f'f{n}', *cs)
                else:
                    if home_bed is None or gauge == 1:
                        if frontBed2(n, '-'): continue
                        elif backBed2(n, '-'): continue
                        elif n == left_n: k.miss('-', f'f{n}', *cs)
                    else:
                        if homeBed2(n, '-'): continue
                        elif travelBed2(n, '-'): continue
                        elif n == left_n: k.miss('-', f'f{n}', *cs)
    
    if home_bed is not None and (gauge != 1 or start_condition != 1):
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in range(left_n, right_n+1):
            if gauge == 1:
                if n % 2 == 0: k.xfer(f'b{n}', f'f{n}')
                else: k.xfer(f'f{n}', f'b{n}')
            else:
                if (n == start_n and secure_start_n) or (n == end_n and secure_end_n): continue

                if currCondition(n) and f'{home_bed}{n}' not in empty_needles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{travelBed}{n}', f'{home_bed}{n}')
        
        # reset settings
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment('end interlock')


def rib(k, start_n, end_n, length, c, bed=None, bed_loops={'f': [], 'b': []}, sequence='fb', gauge=1, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None):
    '''
    *k is the knitout Writer
    *end_n is the last needle
    *start_n is the first needle
    *bed is the bed that we want to knit on
    *bed_loops (optional) indicates which bed working loops are currently on
    *sequence is the repeating rib pattern (e.g. 'fb' of 'bf' for 1x1 [first bed indicates which bed left-most needle will be on], 'ffbb' for 2x2, 'fbffbb' for 1x1x2x2, etc.)
    *gauge is gauge
    '''
    cs = c2cs(c) # ensure list type

    k.comment(f'begin rib ({sequence})')
    # if inhook: k.inhook(*cs)

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if not 'f' in bed_loops: bed_loops['f'] = []
    if not 'b' in bed_loops: bed_loops['b'] = []

    if gauge > 1:
        gauged_sequence = ''
        for char in sequence:
            gauged_sequence += char * gauge
        sequence = gauged_sequence
    
    width = abs(end_n-start_n)+1

    def bedConditions(n):
        if bed == 'f':
            if n % gauge == 0: return True
            else: return False
        else:
            if (n+1) % gauge == 0: return True
            else: return False


    if end_n > start_n: #first pass is pos
        dir1 = '+'
        dir2 = '-'

        ranges = {dir1: range(start_n, end_n+1), dir2: range(end_n, start_n-1, -1)}
    else: #first pass is neg
        dir1 = '-'
        dir2 = '+'

        ranges = {dir1: range(start_n, end_n-1, -1), dir2: range(end_n, start_n+1)}

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=cs)

    
    if bed == 'f': other_bed = 'b'
    else: other_bed = 'f'

    if len(bed_loops['f']) or len(bed_loops['b']): # indicates that we might need to start by xferring to proper spots
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)


        for n in ranges[dir1]: #TODO: adjust for gauge
            if bedConditions(n):
                if sequence[n % len(sequence)] == other_bed and n in bed_loops[bed]: k.xfer(f'{bed}{n}', f'{other_bed}{n}')
                elif sequence[n % len(sequence)] == bed and n in bed_loops[other_bed]: k.xfer(f'{other_bed}{n}', f'{bed}{n}')
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    #TODO: maybe change stitch size for rib? k.stitchNumber(math.ceil(specs.stitchNumber/2)) (if so -- remember to reset settings)
    for p in range(0, length):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=None) # drop it
        if p % 2 == 0:
            direction = dir1
            last_n = end_n
        else:
            direction = dir2
            last_n = start_n

        for n in ranges[direction]:
            if sequence[n % len(sequence)] == 'f':
                if bedConditions(n):
                    k.knit(direction, f'f{n}', *cs) #xferred it or bed == 'f', ok to knit
                elif n == last_n: k.miss(direction, f'f{n}', *cs)
            else: #sequence == 'b'
                if bedConditions(n):
                    k.knit(direction, f'b{n}', *cs) #xferred it or bed == 'b', ok to knit
                elif n == last_n: k.miss(direction, f'b{n}', *cs)
    
    # return the loops:
    if len(bed_loops['f']) or len(bed_loops['b']):
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in ranges[dir1]: #TODO: adjust for gauge
            if bedConditions(n):
                if sequence[n % len(sequence)] == other_bed and n in bed_loops[bed]: k.xfer(f'{other_bed}{n}', f'{bed}{n}')
                elif sequence[n % len(sequence)] == bed and n in bed_loops[other_bed]: k.xfer(f'{bed}{n}', f'{other_bed}{n}')
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment('end rib')

    if length % 2 == 0:
        if end_n > start_n: return '+'
        else: return '-'
    else:
        if end_n > start_n: return '-'
        else: return '+'


def altKnitTuck(k, start_n, end_n, length, c, bed='f', gauge=1, sequence='kt', tuckSequence='mt', inhook=False, releasehook=False, tuck_pattern=True):
    '''
    *TODO
    '''
    cs = c2cs(c) # ensure list type

    k.comment(f'begin alt knit/tuck ({sequence})')

    if end_n > start_n: init_dir = '+'
    else: init_dir = '-'

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=cs)

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    width = abs(end_n-start_n)+1

    if gauge > 1:
        if bed == 'f' and (start_n % gauge != 0 or end_n % gauge != 0): raise ValueError(f"for bed f with gauge: {gauge} > 1, we want both edge needles to be even to ensure there are loops on the end needle => the stitch count is accurate.")
        elif bed == 'b' and (start_n % gauge != 1 or end_n % gauge != 1): raise ValueError(f"for bed b with gauge: {gauge} > 1, we want both edge needles to be odd to ensure there are loops on the end needle => the stitch count is accurate.")

    for p in range(0, length):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=None) # drop it

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
                    if n == pass_end_n and (gauge == 1 or (bed == 'f' and pass_end_n % gauge == 0) or (bed == 'b' and pass_end_n % gauge != 0)): #new #v
                        k.miss('+', f'{bed}{n}', *cs) #new #^
                    elif (bed == 'f' and n % gauge == 0 and (((n//gauge) % 2) == 0)) or (bed == 'b' and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) == 0)):
                        k.tuck('+', f'{bed}{n}', *cs)
                    elif n == pass_end_n: k.miss('+', f'{bed}{n}', *cs)
            else: #pass is neg
                for n in range(pass_start_n, pass_end_n-1, -1):
                    if n == pass_end_n and (gauge == 1 or (bed == 'f' and pass_end_n % gauge == 0) or (bed == 'b' and pass_end_n % gauge != 0)): #new #v
                        k.miss('-', f'{bed}{n}', *cs) #new #^
                    elif (bed == 'f' and n % gauge == 0 and (((n//gauge) % 2) != 0)) or (bed == 'b' and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) != 0)):
                        k.tuck('-', f'{bed}{n}', *cs)
                    elif n == pass_end_n: k.miss('-', f'{bed}{n}', *cs)

    k.comment('end alt knit/tuck')

    if pass_end_n > pass_start_n: return '-' #just knit a pos pass
    else: return '+'


def garter(k, start_n, end_n, length, c, bed='f', bed_loops={'f': [], 'b': []}, sequence='fb', secure_start_n=True, secure_end_n=True, gauge=1, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    '''
    * k is knitout Writer
    * start_n is the starting needle to knit on
    * end_n is the last needle to knit on
    * length is total passes knit
    * c is carrier
    * bed is the bed to start on
    * sequence is the number of knit/purl rows to knit before switch to the other (e.g. 2 -- knit 2 rows, purl 2 rows [repeat]) #TODO: alter (and alter in all other code)
    * secure_start_n and *secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * gauge is... gauge
    '''
    cs = c2cs(c) # ensure list type

    pattern_rows = {
        'f': sequence.count('f'),
        'b': sequence.count('b')
    }

    k.comment(f'begin {pattern_rows["f"]}x{pattern_rows["b"]} garter')

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    secure_needles = {'f': [], 'b': []}

    if bed == 'b':
        other_bed = 'f'
        condition = lambda n: (n % gauge != 0 or gauge == 1)
    else:
        other_bed = 'b'
        condition = lambda n: n % gauge == 0

    if end_n > start_n: #first pass is pos
        dir1 = '+'
        dir2 = '-'

        range1 = range(start_n, end_n+1)
        range2 = range(end_n, start_n-1, -1)

        if gauge == 2:
            if secure_start_n:
                if start_n % 2 == 0:
                    secure_needles['f'].append(start_n)
                    secure_needles['b'].append(start_n+1)
                else:
                    secure_needles['b'].append(start_n)
                    secure_needles['f'].append(start_n+1)
            
            if secure_end_n:
                if end_n % 2 == 0:
                    secure_needles['f'].append(end_n)
                    secure_needles['b'].append(end_n-1)
                else:
                    secure_needles['b'].append(end_n)
                    secure_needles['f'].append(end_n-1)
        else:
            if secure_start_n: secure_needles[bed].append(start_n)
            if secure_end_n: secure_needles[bed].append(end_n)
    else: #first pass is neg
        dir1 = '-'
        dir2 = '+'

        range1 = range(start_n, end_n-1, -1)
        range2 = range(end_n, start_n+1)

        if gauge == 2:
            if secure_start_n:
                if start_n % 2 == 0:
                    secure_needles['f'].append(start_n)
                    secure_needles['b'].append(start_n-1)
                else:
                    secure_needles['b'].append(start_n)
                    secure_needles['f'].append(start_n-1)
            
            if secure_end_n:
                if end_n % 2 == 0:
                    secure_needles['f'].append(end_n)
                    secure_needles['b'].append(end_n+1)
                else:
                    secure_needles['b'].append(end_n)
                    secure_needles['f'].append(end_n+1)
        else:
            if secure_start_n: secure_needles[bed].append(start_n)
            if secure_end_n: secure_needles[bed].append(end_n)

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=cs)
    
    # for now: (will be reset)
    direction = dir1
    needle_range = range1

    if type(pattern_rows) != dict:
        pat_rows = {}
        pat_rows['f'] = pattern_rows
        pat_rows['b'] = pattern_rows
        pattern_rows = pat_rows
    
    b = sequence[0]
    b2 = 'f' if b == 'b' else 'b'

    if len(bed_loops['f']) or len(bed_loops['b']):
        for n in range1:
            if n in bed_loops[b2] and condition(n) and n not in secure_needles[b2]: k.xfer(f'{b2}{n}', f'{b}{n}')
    
    for p in range(0, length):
        if p % 2 == 0:
            direction = dir1
            needle_range = range1
        else:
            direction = dir2
            needle_range = range2

        if p > 0 and b != sequence[p % len(sequence)]: # transfer
            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            
            for n in range1:
                if condition(n) and n not in secure_needles[b]: k.xfer(f'{b}{n}', f'{sequence[p % len(sequence)]}{n}')

            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)

        b = sequence[p % len(sequence)]

        b2 = 'f' if b == 'b' else 'b'

        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=None) # drop it

        for n in needle_range:
            if condition(n):
                if n in secure_needles[b2]: k.knit(direction, f'{b2}{n}', *cs)
                else: k.knit(direction, f'{b}{n}', *cs)
            elif n == end_n: k.miss(direction, f'{b}{n}', *cs)

    if len(bed_loops['f']) or len(bed_loops['b']):
        b2 = 'f' if b == 'b' else b

        if n in bed_loops[b2] and condition(n) and n not in secure_needles[b2]: k.xfer(f'{b}{n}', f'{b2}{n}')

    if type(pattern_rows) == dict: k.comment(f'end {pattern_rows["f"]}x{pattern_rows["b"]} garter')
    else: k.comment(f'end {pattern_rows}x{pattern_rows} garter')

    next_direction = '-' if direction == '+' else '+'
    return next_direction


def tuckGarter(k, start_n, end_n, length, c, bed='f', sequence='ffb', secure_start_n=True, secure_end_n=True, gauge=1, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    '''
    * k is knitout Writer
    * start_n is the starting needle to knit on
    * end_n is the last needle to knit on
    * length is total passes knit
    * c is carrier
    * bed is the bed to start on
    * pattern_rows is the number of knit/purl rows to knit before switch to the other (e.g. 2 -- knit 2 rows, purl 2 rows [repeat])
    * secure_start_n and *secure_end_n are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
    * gauge is... gauge
    '''
    cs = c2cs(c) # ensure list type

    pattern_rows = {
        'f': sequence.count('f'),
        'b': sequence.count('b')
    }

    if type(pattern_rows) == dict: k.comment(f'begin {pattern_rows["f"]}x{pattern_rows["b"]} garter')
    else: k.comment(f'begin {pattern_rows}x{pattern_rows} garter')

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if speedNumber is not None: k.speedNumber(speedNumber)
    if stitchNumber is not None: k.stitchNumber(stitchNumber)

    secure_needles = {}

    if bed == 'b':
        bed2 = 'f'
        condition = lambda n: (n % gauge != 0 or gauge == 1)
    else:
        bed2 = 'b'
        condition = lambda n: n % gauge == 0

    if end_n > start_n: #first pass is pos
        dir1 = '+'
        dir2 = '-'

        range1 = range(start_n, end_n+1)
        range2 = range(end_n, start_n-1, -1)

        if gauge == 2:
            if secure_start_n:
                if start_n % 2 == 0:
                    secure_needles[start_n] = 'f'
                    secure_needles[start_n+1] = 'b'
                else:
                    secure_needles[start_n] = 'b'
                    secure_needles[start_n+1] = 'f'
            
            if secure_end_n:
                if end_n % 2 == 0:
                    secure_needles[end_n] = 'f'
                    secure_needles[end_n-1] = 'b'
                else:
                    secure_needles[end_n] = 'b'
                    secure_needles[end_n-1] = 'f'
        else:
            if secure_start_n: secure_needles[start_n] = bed
            if secure_end_n: secure_needles[end_n] = bed
    else: #first pass is neg
        dir1 = '-'
        dir2 = '+'

        range1 = range(start_n, end_n-1, -1)
        range2 = range(end_n, start_n+1)

        if gauge == 2:
            if secure_start_n:
                if start_n % 2 == 0:
                    secure_needles[start_n] = 'f'
                    secure_needles[start_n-1] = 'b'
                else:
                    secure_needles[start_n] = 'b'
                    secure_needles[start_n-1] = 'f'
            
            if secure_end_n:
                if end_n % 2 == 0:
                    secure_needles[end_n] = 'f'
                    secure_needles[end_n+1] = 'b'
                else:
                    secure_needles[end_n] = 'b'
                    secure_needles[end_n+1] = 'f'
        else:
            if secure_start_n: secure_needles[start_n] = bed
            if secure_end_n: secure_needles[end_n] = bed

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=cs)
    
    # for now: (will be reset)
    direction = dir1
    needle_range = range1

    width = abs(end_n-start_n)+1

    if type(pattern_rows) != dict:
        pat_rows = {}
        pat_rows['f'] = pattern_rows
        pat_rows['b'] = pattern_rows
        pattern_rows = pat_rows
    
    pattern_rows['f'] += 1 #for the tucks

    passCt = 0
    for l in range(0, length):
        if l % 2 == 0:
            b1 = bed
            b2 = bed2
        else:
            b1 = bed2
            b2 = bed

        for r in range(0, pattern_rows[b1]):
            if releasehook and passCt == 2:
                k.releasehook(*cs)
                if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=None) # drop it
            
            if b1 == 'f' and r == 0:
                for n in needle_range:
                    if n % (gauge*2) == 0 and includeNSecureSides(n, secure_needles=secure_needles, knitBed=None): k.tuck(direction, f'{b1}{n}', *cs)
                    elif n == end_n: k.miss(direction, f'{b1}{n}', *cs)
            else:
                for n in needle_range:
                    if condition(n) and includeNSecureSides(n, secure_needles=secure_needles, knitBed=b1): k.knit(direction, f'{b1}{n}', *cs)
                    elif condition(n): k.knit(direction, f'{bed}{n}', *cs)
                    elif n == end_n: k.miss(direction, f'{b1}{n}', *cs)

            if direction == dir1:
                direction = dir2
                needle_range = range2
            else:
                direction = dir1
                needle_range = range1

            passCt += 1
            if passCt == length: break

        if passCt == length and b1 == bed: break #don't need to return it

        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)
            
        for n in range1:
            if condition(n) and includeNSecureSides(n, secure_needles=secure_needles): k.xfer(f'{b1}{n}', f'{b2}{n}')

        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

        if passCt == length: break

    if type(pattern_rows) == dict: k.comment(f'end {pattern_rows["f"]-1}x{pattern_rows["b"]} garter')
    else: k.comment(f'end {pattern_rows}x{pattern_rows} garter')

    return direction #return the direction that the next pass should be, so know which to use next


def seed(k, start_n, end_n, length, c, bed='f', bed_loops={'f': [], 'b': []}, sequence='fb', secure_start_n=True, secure_end_n=True, gauge=1, inhook=False, releasehook=False, tuck_pattern=True, speedNumber=None, stitchNumber=None, xfer_speedNumber=None, xfer_stitchNumber=None): #TODO: fix this for gauge 2 secure needles
    cs = c2cs(c) # ensure list type

    k.comment(f'begin seed ({sequence})')

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    if not 'f' in bed_loops: bed_loops['f'] = []
    if not 'b' in bed_loops: bed_loops['b'] = []

    secure_needles = {}

    if gauge == 2:
        if secure_start_n:
            if start_n % 2 == 0:
                secure_needles[start_n] = 'f'
                secure_needles[start_n-1] = 'b'
            else:
                secure_needles[start_n] = 'b'
                secure_needles[start_n-1] = 'f'
        
        if secure_end_n:
            if end_n % 2 == 0:
                secure_needles[end_n] = 'f'
                secure_needles[end_n+1] = 'b'
            else:
                secure_needles[end_n] = 'b'
                secure_needles[end_n+1] = 'f'
    else:
        if secure_start_n: secure_needles[start_n] = bed
        if secure_end_n: secure_needles[end_n] = bed


    if gauge > 1:
        gauged_sequence = ''
        for char in sequence:
            gauged_sequence += char * gauge
        sequence = gauged_sequence


    def bedConditions(n):
        if bed == 'f':
            if n % gauge == 0: return True
            else: return False
        else:
            if (n+1) % gauge == 0: return True
            else: return False


    if end_n > start_n: #first pass is pos
        dir1 = '+'
        dir2 = '-'

        ranges = {dir1: range(start_n, end_n+1), dir2: range(end_n, start_n-1, -1)}
    else: #first pass is neg
        dir1 = '-'
        dir2 = '+'

        ranges = {dir1: range(start_n, end_n-1, -1), dir2: range(end_n, start_n+1)}

    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=cs)
    
    if bed == 'f': other_bed = 'b'
    else: other_bed = 'f'

    if len(bed_loops['f']) or len(bed_loops['b']): # indicates that we might need to start by xferring to proper spots
        if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
        if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

        for n in ranges[dir1]: #TODO: adjust for gauge
            if n not in secure_needles and bedConditions(n):
                if sequence[n % len(sequence)] == other_bed and n in bed_loops[bed]: k.xfer(f'{bed}{n}', f'{other_bed}{n}')
                elif sequence[n % len(sequence)] == bed and n in bed_loops[other_bed]: k.xfer(f'{other_bed}{n}', f'{bed}{n}')
            
        if speedNumber is not None: k.speedNumber(speedNumber)
        if stitchNumber is not None: k.stitchNumber(stitchNumber)

    for p in range(0, length):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=dir1, c=None) # drop it
        
        if p % 2 == 0:
            direction = dir1
            last_n = end_n

            for n in ranges[direction]:
                if n in secure_needles:
                    if bedConditions(n):
                        k.knit(direction, f'{secure_needles[n]}{n}', *cs) #xferred it or bed == 'f', ok to knit
                    elif n == last_n: k.miss(direction, f'{secure_needles[n]}{n}', *cs)
                else:
                    if sequence[n % len(sequence)] == 'f':
                        if bedConditions(n):
                            k.knit(direction, f'f{n}', *cs) #xferred it or bed == 'f', ok to knit
                        elif n == last_n: k.miss(direction, f'f{n}', *cs)
                    else: #sequence == 'b'
                        if bedConditions(n):
                            k.knit(direction, f'b{n}', *cs) #xferred it or bed == 'b', ok to knit
                        elif n == last_n: k.miss(direction, f'b{n}', *cs)
            
            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            if p < length-1:
                for n in ranges[direction]: #TODO: adjust for gauge
                    if n not in secure_needles and bedConditions(n):
                        if sequence[n % len(sequence)] == 'f': k.xfer(f'f{n}', f'b{n}')
                        else: k.xfer(f'b{n}', f'f{n}')
            else:
                for n in ranges[direction]: #TODO: adjust for gauge
                    if n not in secure_needles and bedConditions(n):
                        if sequence[n % len(sequence)] == 'f' and n in bed_loops['b']: k.xfer(f'f{n}', f'b{n}')
                        elif sequence[n % len(sequence)] == 'b' and n in bed_loops['f']: k.xfer(f'b{n}', f'f{n}')

            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)
        else:
            direction = dir2
            last_n = start_n

            for n in ranges[direction]:
                if n in secure_needles:
                    if bedConditions(n):
                        k.knit(direction, f'{secure_needles[n]}{n}', *cs) #xferred it or bed == 'f', ok to knit
                    elif n == last_n: k.miss(direction, f'{secure_needles[n]}{n}', *cs)
                else:
                    if sequence[n % len(sequence)] == 'f':
                        if bedConditions(n):
                            k.knit(direction, f'b{n}', *cs) #xferred it or bed == 'f', ok to knit
                        elif n == last_n: k.miss(direction, f'b{n}', *cs)
                    else: #sequence == 'b'
                        if bedConditions(n):
                            k.knit(direction, f'f{n}', *cs) #xferred it or bed == 'b', ok to knit
                        elif n == last_n: k.miss(direction, f'f{n}', *cs)

            if xfer_speedNumber is not None: k.speedNumber(xfer_speedNumber)
            if xfer_stitchNumber is not None: k.stitchNumber(xfer_stitchNumber)

            if p < length-1:
                for n in ranges[direction]: #TODO: adjust for gauge
                    if n not in secure_needles and bedConditions(n):
                        if sequence[n % len(sequence)] == 'f': k.xfer(f'b{n}', f'f{n}')
                        else: k.xfer(f'f{n}', f'b{n}')
            else:
                for n in ranges[direction]: #TODO: adjust for gauge
                    if n not in secure_needles and bedConditions(n):
                        if sequence[n % len(sequence)] == 'f' and n in bed_loops['f']: k.xfer(f'b{n}', f'f{n}')
                        elif sequence[n % len(sequence)] == 'b' and n in bed_loops['b']: k.xfer(f'f{n}', f'b{n}')
            
            if speedNumber is not None: k.speedNumber(speedNumber)
            if stitchNumber is not None: k.stitchNumber(stitchNumber)

    k.comment(f'end seed ({sequence})')

    if length % 2 == 0:
        if end_n > start_n: return '+'
        else: return '-'
    else:
        if end_n > start_n: return '-'
        else: return '+'


def tuckStitch(k, start_n, end_n, length, c, bed='f', gauge=1, sequence='kt', inhook=False, releasehook=False, tuck_pattern=True):
    cs = c2cs(c) # ensure list type

    k.comment(f'begin tuck stitch ({sequence})')

    if end_n > start_n:
        init_dir = '+'
        other_dir = '-'
        needle_range0 = range(start_n, end_n+1)
        needle_range1 = range(end_n, start_n-1, -1)
    else:
        init_dir = '-'
        other_dir = '+'
        needle_range0 = range(start_n, end_n-1, -1)
        needle_range1 = range(end_n, start_n+1)
    
    if inhook:
        k.inhook(*cs)
        if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=cs)

    if releasehook and length < 2: raise ValueError("not safe to releasehook with less than 2 passes.")

    for p in range(0, length):
        if releasehook and p == 2:
            k.releasehook(*cs)
            if tuck_pattern: tuckPattern(k, first_n=start_n, direction=init_dir, c=None) # drop it

        if p % 2 == 0:
            needle_range = needle_range0
            do_knit = 'k'
            d = init_dir
            pass_start_n = start_n
            pass_end_n = end_n
        else:
            needle_range = needle_range1
            do_knit = 't'
            d = other_dir
            pass_start_n = end_n
            pass_end_n = start_n

        for n in needle_range:
            if n % (gauge*2) == 0 or n % (gauge*2) == gauge:
                if sequence[(n*gauge) % len(sequence)] == do_knit or n == pass_start_n or n == pass_end_n: k.knit(d, f'{bed}{n}', *cs)
                else: k.tuck(d, f'{bed}{n}', *cs)
            elif n == pass_end_n: k.miss(d, f'{bed}{n}', *cs)

    k.comment('end tuck stitch')

    if pass_end_n > pass_start_n: return '-' #just knit a pos pass
    else: return '+'
