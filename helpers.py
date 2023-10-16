import numpy as np

# --- MISC HELPERS ---
def parityRound(num, parity='even'):
    if parity == 'even': return round(num/2)*2
    else: return int(np.floor(num/2))*2 + 1


def toList(el):
    if isinstance(el, str): return [el]
    else: return list(el)


def toTuple(el):
    if hasattr(el, '__iter__') and not isinstance(el, str): return tuple(el)
    else: return (el,)


def flattenList(l):
    out = []
    for item in l:
        if hasattr(item, '__iter__') and not isinstance(item, str):
            out.extend(flattenList(item))
        else: out.append(item)
    return out


def flattenIter(l): #TODO: add support for dict and other iters
    out = []
    for item in l:
        if hasattr(item, '__iter__') and not isinstance(item, str): out.extend(flattenIter(item))
        else: out.append(item)
    
    if type(l) == list: return out
    elif type(l) == tuple: return tuple(out)
    else: raise ValueError(f"type {type(l)} not support yet. TODO")


def bnHalfG(b, n):
    if b == 'f': return n*2
    else: return (n*2)+1


def bnGauged(b, n, gauge=2):
    if b == 'f': return n*gauge
    else: return (n*gauge)+(gauge//2)


def bnValid(b, n, gauge=1):
    return (b == 'f' and n % gauge == 0) or (b == 'b' and n % gauge == (gauge//2))


def halveGauge(gauge, mod):
    if type(mod) == str: #passed bed for it
        if mod == 'f': mod = 0
        else: mod = gauge//2 # -1 #if gauge=1, this is 0 no matter what so works
    #
    return [mod, mod+gauge]


# --- ENSURES CARRIERS ARE IN THE FORM WE WANT (always tuple, even if passed as string) ---
def c2cs(c):
    if hasattr(c, '__iter__') and not isinstance(c, str): return tuple(c)
    else: return (c,)


def sortBedNeedles(bnList=[], direction='+'):
    '''
    *TODO
    '''
    sortedBnList = list(set(bnList.copy()))
    if direction == '-': sortedBnList.sort(key=lambda bn: int(bn[1:]), reverse=True)
    else: sortedBnList.sort(key=lambda bn: int(bn[1:]))
    return sortedBnList


def convertToBN(needles, sort=True, gauge=2):
    '''
    e.g.: `convertToBN([1, 2, 'f2', range(0, 10)])`

    for now, only works with: list (with potential sublists/sub-ranges), int, or str
    '''
    try:
        int(needles)
        return f'b{needles}' if (needles % gauge != 0) else f'f{needles}'
    except Exception:
        if type(needles) == str: return needles
        else: # list of lists of range
            needles = [convertToBN(n) for sublist in needles for n in ([sublist] if isinstance(sublist, (str, int, float)) else sublist)]
    
    if sort: sortBedNeedles(needles)
    return needles #otherwise, just return original list


def includeNSecureSides(n, secure_needles={}, knit_bed=None):
  '''
  * n is the number associated with the needle we're checking
  * secure_needles is dict with needle numbers as key and bed as value (valid values are 'f', 'b', or 'both')
  * knit_bed is the bed that is currently knitting, if applicable (because this is only checking if we can't xfer it, so if it was unable to be xferred from a certain bed, it should still be knitted on that bed); value of None indicates we are just check for xfer
  '''
  if n in secure_needles:
    if knit_bed is None: return False
    else: #for knitting
      if knit_bed == secure_needles[n]: return True
      else: return False
  else: return True


def toggleDir(track_dict, c):
  if track_dict[c] == '+': track_dict[c] = '-'
  else: track_dict[c] = '+'

  return track_dict[c]


def toggleDirection(d):
    if d == '-': return '+'
    else: return '-'

# ----------------------
# --- KNITTING STUFF ---
# ----------------------

def tuckPattern(k, first_n, direction, c=None, bed='f', machine='swgn2'): #remember to drop after (aka pass `c=None`)
    '''
    for securing yarn after inhook before knitting (to be dropped after releasehook)

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `first_n` (int): first needle to tuck on
    * `direction` (str): initial direction to tuck in
    * `c` (str or list, optional): carrier(s) to use. Defaults to None (meaning just drop the tuck pattern).
    * `bed` (str, optional): bed to tuck on. Defaults to 'f'.
    * `machine` (str, optional): knitting machine model (options are swgn2 and kniterate). Defaults to 'swgn2'.
    '''
    cs = c2cs(c) # ensure tuple type

    if direction == '+':
        for n in range(first_n-1, first_n-6, -1):
            if c is None: k.drop(f'{bed}{n}')
            elif n % 2 == 0: k.tuck('-', f'{bed}{n}', *cs)
            elif n == first_n-5: k.miss('-', f'{bed}{n}', *cs)
            
        
        if c is not None:
            for n in range(first_n-5, first_n):
                if n % 2 != 0: k.tuck('+', f'{bed}{n}', *cs)
                elif n == first_n-1: k.miss('+', f'{bed}{n}', *cs)
    else:
        if c is not None and machine.lower() == 'swgn2': #do it twice so always starting in negative direction
            for n in range(first_n+5, first_n, -1):
                if n % 2 == 0: k.tuck('-', f'{bed}{n}', *cs)
                elif n == first_n+1: k.miss('-', f'{bed}{n}', *cs)

        for n in range(first_n+1, first_n+6):
            if c is None: k.drop(f'{bed}{n}')
            elif n % 2 != 0: k.tuck('+', f'{bed}{n}', *cs)
            elif n == first_n+5: k.miss('+', f'{bed}{n}', *cs)

        if c is not None:
            for n in range(first_n+5, first_n, -1):
                if n % 2 == 0: k.tuck('-', f'{bed}{n}', *cs)
                elif n == first_n+1: k.miss('-', f'{bed}{n}', *cs)

        
def knitPass(k, start_n, end_n, c, bed='f', gauge=1, empty_needles=[]):
    '''
    *TODO
    '''
    cs = c2cs(c) # ensure tuple type

    if end_n > start_n: #pass is pos
        for n in range(start_n, end_n+1):
            if f'{bed}{n}' not in empty_needles:
                if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('+', f'{bed}{n}', *cs) 
                elif n == end_n: k.miss('+', f'{bed}{n}', *cs)
            elif n == end_n: k.miss('+', f'{bed}{n}', *cs)
    else: #pass is neg
        for n in range(start_n, end_n-1, -1):
            if f'{bed}{n}' not in empty_needles:
                if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('-', f'{bed}{n}', *cs)
                elif n == end_n: k.miss('-', f'{bed}{n}', *cs)
            elif n == end_n: k.miss('-', f'{bed}{n}', *cs)


class CarrierTracker:
    def __init__(self, cs, start_n=None, end_n=None):
        self.cs = cs
        # internal values
        self._start_n = start_n
        self._end_n = end_n

        self.direction = None # for now # can use this to store the carrier but signify that it isn't in

        self._updateDirection()

    # internal helper method
    def _updateDirection(self, do_toggle=False):
        if self._start_n is not None and self._end_n is not None:
            if self._start_n < self._end_n: self.direction = '+'
            else: self.direction = '-'
        elif do_toggle and self.direction is not None:
            if self.direction == '+': self.direction = '-'
            else: self.direction = '+'
        else: self.direction = None #TODO: decide if should keep ths

    @property
    def start_n(self):
        return self._start_n
    
    @property
    def end_n(self):
        return self._end_n

    @start_n.setter
    def start_n(self, val):
        self._start_n = val
        self._updateDirection()
    
    @end_n.setter
    def end_n(self, val):
        self._end_n = val
        self._updateDirection() #TODO: consider changing this since it would be called twice if updating start_n and end_n simultaneously
    
    def toggle(self, new_start_n=None, new_end_n=None):
        if new_start_n is None: new_start_n = self._end_n
        if new_end_n is None: new_end_n = self._start_n

        self._start_n = new_start_n
        self._end_n = new_end_n

        self._updateDirection(do_toggle=True)

    def __copy__(self):
        return CarrierTracker(self.cs, self._start_n, self._end_n)
