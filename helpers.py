import numpy as np
import regex

#===============================================================================
#-------------------------------- MISC HELPERS ---------------------------------
#===============================================================================
def parityRound(num, parity="even"):
    if parity == "even": return round(num/2)*2
    else: return int(np.floor(num/2))*2 + 1


def toList(el):
    if isinstance(el, str): return [el]
    else: return list(el)


def toTuple(el):
    if hasattr(el, "__iter__") and not isinstance(el, str): return tuple(el)
    else: return (el,)


def flattenList(l):
    out = []
    for item in l:
        if hasattr(item, "__iter__") and not isinstance(item, str):
            out.extend(flattenList(item))
        else: out.append(item)
    return out


def flattenIter(l): #TODO: add support for dict and other iters
    out = []
    for item in l:
        if hasattr(item, "__iter__") and not isinstance(item, str): out.extend(flattenIter(item))
        else: out.append(item)
    #
    if type(l) == list: return out
    elif type(l) == tuple: return tuple(out)
    else: raise ValueError(f"type {type(l)} not support yet. TODO")

#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------- VALIDATION HELPERS ------------------------------
#===============================================================================
def bnValid(b, n, gauge=1):
    return (b == "f" and n % gauge == 0) or (b == "b" and n % gauge == (gauge//2))

#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------------- GETTERS -----------------------------------
#===============================================================================
def bnEdges(left_n, right_n, gauge, bed_loops={"f": [], "b": []}, avoid_bns={"f": [], "b": []}, return_type=str):
    edge_bns = []
    #
    if not len(bed_loops.get("f", [])) and not len(bed_loops.get("b", [])):
        bn_locs = {"f": [n for n in range(left_n, right_n+1) if bnValid("f", n, gauge) and n not in avoid_bns.get("f", [])], "b": [n for n in range(left_n, right_n+1) if bnValid("b", n, gauge) and n not in avoid_bns.get("b", [])]}
    else: bn_locs = bed_loops.copy()
    #
    for n in range(left_n, right_n+1):
        if n in bn_locs.get("f", []):
            if return_type == str: edge_bns.append(f"f{n}")
            else: edge_bns.append(["f", n])
            break
        elif n in bn_locs.get("b", []):
            if return_type == str: edge_bns.append(f"b{n}")
            else: edge_bns.append(["b", n])
            break
    #
    for n in range(right_n, left_n-1, -1):
        if n in bn_locs.get("f", []):
            if return_type == str: edge_bns.append(f"f{n}")
            else: edge_bns.append(["f", n])
            break
        elif n in bn_locs.get("b", []):
            if return_type == str: edge_bns.append(f"b{n}")
            else: edge_bns.append(["b", n])
            break
    #
    return edge_bns

#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------- FORMATTING HELPERS ------------------------------
#===============================================================================
def c2cs(c):
    '''
    Ensures carriers are in the program's conventional form (always tuple, even if passed as string).

    Parameters:
    ----------
    * `c` (iterable (including str) or int): input carriers to format

    Returns:
    -------
    * tuple: output carriers formatted as tuple
    '''
    if hasattr(c, "__iter__") and not isinstance(c, str): return tuple(c)
    else: return (c,)


def toggleDirection(d):
    if d == "-": return "+"
    else: return "-"


def bnHalfG(b, n):
    if b == "f": return n*2
    else: return (n*2)+1


def bnGauged(b, n, gauge=2):
    if b == "f": return n*gauge
    else: return (n*gauge)+(gauge//2)


def halveGauge(gauge, mod): # usage: n % (gauge*2) == mods[0] or n % (gauge*2) == mods[1]
    if type(mod) == str: #passed bed for it
        if mod == "f": mod = 0
        else: mod = gauge//2 # -1 #if gauge=1, this is 0 no matter what so works
    #
    return [mod, mod+gauge]


def bnSplit(bns):
    if type(bns) == str:
        i = regex.search(r"[a-z]+", bns).end()
        return [bns[:i], int(bns[i:])]
    else:
        split_idxs = [regex.search(r"[a-z]+", val).end() for val in bns]
        return [[val[:i], int(val[i:])] for (val, i) in zip(bns, split_idxs)]


def bnSort(bn_list=[], direction="+", unique=True):
    '''
    *TODO
    must be in list with strings format, e.g., ["f0", "b0", "f10"]
    '''
    if unique: b_n_list = bnSplit(list(set(bn_list.copy())))
    else: b_n_list = bnSplit(list(bn_list.copy()))
    #
    sorted_bns = ["".join(str(el) for el in val) for val in sorted(b_n_list, key=lambda x:(-x[1],x[0]))]
    #
    if direction == "+": return sorted_bns[::-1] # bed `f` comes first (so works for when knitting at e.g. `rack 0.25`)
    else: return sorted_bns # bed `b` comes first


def bnFormat(needles, bed=None, gauge=2, sort=True, unique=True, return_type=list): #TODO: #check and test this #*
    '''
    Converts iterable of needles to uniform format that this program likes to work with.
    e.g.: `bnFormat([1, 2, "f4", CarrierTracker(c, start_n=5), range(0, 10)])`

    Parameters:
    ----------
    * `needles` (iterable): iterable of needles to format.
    * `bed` (str, optional): bed to default to if not indicated for a bn value. Defaults to `None`.
    * `gauge` (int, optional): gauge we're knitting in (optional; can be used to infer bed when only needle number is passes). Defaults to `2`.
    * `sort` (bool, optional): _description_. Defaults to `True`.
    * `unique` (bool, optional): _description_. Defaults to `True`.
    * `return_type` (type, optional): supported values are `list` and `dict`.  Defaults to `list`.

    Returns:
    -------
    * _type_: _description_
    '''
    out = []
    # ensure format that will work in for loop
    if not hasattr(needles, "__iter__") or type(needles) == str or type(needles) == dict: needles_iter = [needles]
    else: needles_iter = needles.copy()
    #
    for val in needles_iter:
        if type(val) == str: out.append(val)
        elif type(val) == dict: #TODO: #check
            bed_keys = list(filter(regex.compile(r"^[f|b]s?$").match, [str(key) for key in val.keys()]))
            #
            for b, ns in val.items():
                if b in bed_keys: out.extend(bnFormat(ns, bed=b, gauge=gauge, sort=sort, unique=unique))
                else: out.extend(bnFormat(ns, bed=bed, gauge=gauge, sort=sort, unique=unique))
        elif hasattr(val, "__iter__"): out.extend(bnFormat(val, bed=bed, gauge=gauge, sort=sort, unique=unique))
        elif type(val) == str: out.append(val)
        else:
            if hasattr(val, "needle"): n = val.needle
            elif hasattr(val, "start_n"): n = val.start_n
            else:
                try:
                    n = int(val)
                except Exception:
                    raise ValueError(f"Type {type(val)} not supported.")
            #
            if hasattr(val, "bed"): out.append(f"{val.bed}{n}")
            elif bed is not None: out.append(f"{bed}{n}")
            else:
                if bnValid("f", n, gauge): out.append(f"f{n}")
                elif bnValid("b", n, gauge): out.append(f"b{n}")
                else: raise ValueError(f"Cannot automatically detect bed for needle {n} in gauge {gauge}.")
    #
    if sort: out = bnSort(out, unique=unique)
    elif unique: out = list(set(out))
    #
    if return_type == list: return out
    elif return_type == dict:
        d_out = {}
        for val in out:
            b, n = bnSplit(val)
            if b not in d_out: d_out[b] = []
            d_out[b].append(n)
        #
        return d_out
    else: raise ValueError(f"Return type {return_type} not yet supported.")


def rollSequence(seq_str, i):
    return seq_str[i%len(seq_str):]+seq_str[:i%len(seq_str)]

#-------------------------------------------------------------------------------


#===============================================================================
#-------------- KNITTING STUFF (here to prevent circular imports) --------------
#===============================================================================
def tuckPattern(k, first_n, direction, c=None, bed="f", machine="swgn2"): #remember to drop after (aka pass `c=None`)
    '''
    for securing yarn after inhook before knitting (to be dropped after releasehook)

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `first_n` (int): first needle to tuck on
    * `direction` (str): initial direction to tuck in
    * `c` (str or list, optional): carrier(s) to use. Defaults to None (meaning just drop the tuck pattern).
    * `bed` (str, optional): bed to tuck on. Defaults to "f".
    * `machine` (str, optional): knitting machine model (options are swgn2 and kniterate). Defaults to "swgn2".
    '''
    cs = c2cs(c) # ensure tuple type

    if direction == "+":
        for n in range(first_n-1, first_n-6, -1):
            if c is None: k.drop(f"{bed}{n}")
            elif n % 2 == 0: k.tuck("-", f"{bed}{n}", *cs)
            elif n == first_n-5: k.miss("-", f"{bed}{n}", *cs)
            
        
        if c is not None:
            for n in range(first_n-5, first_n):
                if n % 2 != 0: k.tuck("+", f"{bed}{n}", *cs)
                elif n == first_n-1: k.miss("+", f"{bed}{n}", *cs)
    else:
        if c is not None and machine.lower() == "swgn2": #do it twice so always starting in negative direction
            for n in range(first_n+5, first_n, -1):
                if n % 2 == 0: k.tuck("-", f"{bed}{n}", *cs)
                elif n == first_n+1: k.miss("-", f"{bed}{n}", *cs)

        for n in range(first_n+1, first_n+6):
            if c is None: k.drop(f"{bed}{n}")
            elif n % 2 != 0: k.tuck("+", f"{bed}{n}", *cs)
            elif n == first_n+5: k.miss("+", f"{bed}{n}", *cs)

        if c is not None:
            for n in range(first_n+5, first_n, -1):
                if n % 2 == 0: k.tuck("-", f"{bed}{n}", *cs)
                elif n == first_n+1: k.miss("-", f"{bed}{n}", *cs)

        
def knitPass(k, start_n, end_n, c, bed="f", gauge=1, avoid_bns={"f": [], "b": []}):
    '''
    Plain knit a pass

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class
    * `start_n` (_type_): _description_.
    * `end_n` (_type_): _description_.
    * `c` (_type_): _description_.
    * `bed` (str, optional): _description_. Defaults to `"f"`.
    * `gauge` (int, optional): _description_. Defaults to `1`.
    * `avoid_bns` (dict or list, optional): _description_. Defaults to `[]`.
    '''
    cs = c2cs(c) # ensure tuple type
    avoid_bns_list = bnFormat(avoid_bns, gauge=gauge, return_type=list)
    #
    if end_n > start_n: #pass is pos
        for n in range(start_n, end_n+1):
            if f"{bed}{n}" not in avoid_bns_list and bnValid(bed, n, gauge): k.knit("+", f"{bed}{n}", *cs) 
            elif n == end_n: k.miss("+", f"{bed}{n}", *cs)
    else: #pass is neg
        for n in range(start_n, end_n-1, -1):
            if f"{bed}{n}" not in avoid_bns_list and bnValid(bed, n, gauge): k.knit("-", f"{bed}{n}", *cs)
            elif n == end_n: k.miss("-", f"{bed}{n}", *cs)

#-------------------------------------------------------------------------------


#===============================================================================
#-------------------------------- CLASS HELPERS --------------------------------
#===============================================================================
class BedNeedle:
    _b_re = r"^[f|b]s?$"
    _n_re = r"^\d+$"
    _cs_re = r"^(([1-9]|10)\b ?)+$"
    def __init__(self, b, n, cs=None):
        self.bed = b
        self.needle = n
        self.cs = cs
        self.validate(b, n, cs, raise_err=True)
    #
    def validate(self, b=None, n=None, cs=None, raise_err=False):
        if b is None: b = self.bed
        if n is None: n = self.needle
        if cs is None: cs = self.cs
        #
        b_res = regex.search(self._b_re, b)
        #
        try: n_res = regex.search(self._n_re, str(n))
        except: n_res = None
        #
        if cs is None: cs_res = True
        else:
            if hasattr(cs, "__iter__") and not isinstance(cs, str): cs_res = regex.search(self._cs_re, " ".join(str(el) for el in cs))
            else:
                try: cs_res = regex.search(self._cs_re, str(cs))
                except: cs_res = None
        #
        if raise_err:
            err_msg = ""
            if b_res is None: err_msg += f"Invalid bed value: {b}. "
            if n_res is None: err_msg += f"Invalid needle value: {n}. "
            if cs_res is None: err_msg += f"Invalid carrier(s) value: {cs}."
            #
            if len(err_msg): raise ValueError(err_msg)
        #
        return b_res is not None and n_res is not None and cs_res is not None


class CarrierTracker:
    def __init__(self, cs, start_n=None, end_n=None):
        self.cs = cs
        # internal values
        self._start_n = start_n
        self._end_n = end_n
        #
        self.direction = None # for now # can use this to store the carrier but signify that it isn't in
        #
        self._updateDirection()
    #
    # internal helper method
    def _updateDirection(self, do_toggle=False):
        if self._start_n is not None and self._end_n is not None:
            if self._start_n < self._end_n: self.direction = "+"
            else: self.direction = "-"
        elif do_toggle and self.direction is not None:
            if self.direction == "+": self.direction = "-"
            else: self.direction = "+"
        else: self.direction = None #TODO: decide if should keep ths
    #
    @property
    def start_n(self):
        return self._start_n
    #
    @property
    def end_n(self):
        return self._end_n
    #
    @start_n.setter
    def start_n(self, val):
        self._start_n = val
        self._updateDirection()
    #
    @end_n.setter
    def end_n(self, val):
        self._end_n = val
        self._updateDirection() #TODO: consider changing this since it would be called twice if updating start_n and end_n simultaneously
    #
    def toggle(self, new_start_n=None, new_end_n=None):
        if new_start_n is None: new_start_n = self._end_n
        if new_end_n is None: new_end_n = self._start_n
        #
        self._start_n = new_start_n
        self._end_n = new_end_n
        #
        self._updateDirection(do_toggle=True)
    #
    def __copy__(self):
        return CarrierTracker(self.cs, self._start_n, self._end_n)

#-------------------------------------------------------------------------------