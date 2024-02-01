from typing import Union, Optional, Tuple, List, Dict

import numpy as np
import regex

import cv2

#===============================================================================
#-------------------------------- MISC HELPERS ---------------------------------
#===============================================================================
def parityRound(num: int, parity: str="even") -> int:
    if parity == "even": return round(num/2)*2
    else: return int(np.floor(num/2))*2 + 1


def toList(el) -> list:
    if isinstance(el, str): return [el]
    else: return list(el)


def toTuple(el) -> tuple:
    if hasattr(el, "__iter__") and not isinstance(el, str): return tuple(el)
    else: return (el,)


def flattenList(l: list) -> list:
    out = []
    for item in l:
        if hasattr(item, "__iter__") and not isinstance(item, str):
            out.extend(flattenList(item))
        else: out.append(item)
    return out


def flattenIter(l: Union[list, tuple]) -> Union[list, tuple]: #TODO: add support for dict and other iters
    out = []
    for item in l:
        if hasattr(item, "__iter__") and not isinstance(item, str): out.extend(flattenIter(item))
        else: out.append(item)
    #
    if type(l) == list: return out
    elif type(l) == tuple: return tuple(out)
    else: raise ValueError(f"type {type(l)} not support yet. TODO")


def processImg(img_path: str, cs_cols: dict, resize_dims: Tuple[int,int]=()) -> Tuple[np.ndarray, List[int]]: #TODO: #check
    '''
    Parameters:
    ----------
    * `img_path` (str): relative or absolute path of image to process.
    * `cs_cols` (dict): a dictionary with carriers (cs) as keys, and the colors they should map to as values.
    * `resize_dims` (tuple[int, int], optional): dimensions of resize width and height. Defaults to `()` (aka don't resize).

    Returns:
    -------
    * (tuple): (arr: numpy array with respective carrier at each needle that it knits with, cs: list of carriers).
    '''
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    if len(resize_dims): img = cv2.resize(img, resize_dims, interpolation=cv2.INTER_NEAREST)

    cols = np.unique(img.reshape(-1, img.shape[-1]), axis=0)

    cs = [int(c) for c in cs_cols.keys()]
    if len(cols) != len(cs_cols):
        unassigned = [col for col in cols.tolist() if col not in cs_cols.values()] #cols, list(cs_cols.values()))
        c = 1
        for col in unassigned:
            while c in cs:
                c += 1
            
            cs_cols[c] = col
            cs.append(c)
            c += 1
    
    arr = np.zeros((h,w), dtype=int)
    for i, col in enumerate(cs_cols.values()):
        mask = np.all(img == col, axis=-1)
        arr[mask] = i 

    arr = cv2.flip(arr, 0)
    return arr, cs

#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------- VALIDATION HELPERS ------------------------------
#===============================================================================
def bnValid(b: str, n: int, gauge: int=1) -> bool:
    return (b == "f" and n % gauge == 0) or (b == "b" and n % gauge == (gauge//2))

#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------------- GETTERS -----------------------------------
#===============================================================================
def bnLast(start_n: int, end_n: int, gauge: int, bn_locs: Union[str, Dict[str,List[int]]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, return_type: type=str) -> Union[str, tuple, list]:
    bn = None
    if end_n > start_n: step = 1
    else: step = -1
    #
    if type(bn_locs) == str: _bn_locs = {bn_locs: [n for n in range(start_n, end_n+step, step) if bnValid(bn_locs, n, gauge) and n not in avoid_bns.get(bn_locs, [])]}
    elif not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])):
        _bn_locs = {"f": [n for n in range(start_n, end_n+step, step) if bnValid("f", n, gauge) and n not in avoid_bns.get("f", [])], "b": [n for n in range(start_n, end_n+step, step) if bnValid("b", n, gauge) and n not in avoid_bns.get("b", [])]}
    else: _bn_locs = bn_locs.copy()
    #
    for n in range(end_n, start_n-step, -step):
        if n in _bn_locs.get("f", []):
            if return_type == str: bn = f"f{n}"
            elif return_type == tuple: bn = ("f", n)
            elif return_type == list: bn = ["f", n]
            else: raise ValueError("unsupported return_type requested.")
            break
        elif n in _bn_locs.get("b", []):
            if return_type == str: bn = f"b{n}"
            elif return_type == tuple: bn = ("b", n)
            elif return_type == list: bn = ["b", n]
            else: raise ValueError("unsupported return_type requested.")
            break
    #
    return bn


def bnEdges(left_n: int, right_n: int, gauge: int, bn_locs: Union[str, Dict[str,List[int]]]={"f": [], "b": []}, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, return_type: type=str) -> Union[Tuple[str,str], Tuple[tuple,tuple], Tuple[list,list]]:
    # edge_bns = []
    #
    if type(bn_locs) == str: _bn_locs = {bn_locs: [n for n in range(left_n, right_n+1) if bnValid(bn_locs, n, gauge) and n not in avoid_bns.get(bn_locs, [])]}
    elif not len(bn_locs.get("f", [])) and not len(bn_locs.get("b", [])):
        _bn_locs = {"f": [n for n in range(left_n, right_n+1) if bnValid("f", n, gauge) and n not in avoid_bns.get("f", [])], "b": [n for n in range(left_n, right_n+1) if bnValid("b", n, gauge) and n not in avoid_bns.get("b", [])]}
    else: _bn_locs = bn_locs.copy()
    #
    return (bnLast(right_n, left_n, gauge, _bn_locs, avoid_bns, return_type), bnLast(left_n, right_n, gauge, _bn_locs, avoid_bns, return_type))
    """
    for n in range(left_n, right_n+1):
        if n in _bn_locs.get("f", []):
            if return_type == str: edge_bns.append(f"f{n}")
            else: edge_bns.append(["f", n])
            break
        elif n in _bn_locs.get("b", []):
            if return_type == str: edge_bns.append(f"b{n}")
            else: edge_bns.append(["b", n])
            break
    #
    for n in range(right_n, left_n-1, -1):
        if n in _bn_locs.get("f", []):
            if return_type == str: edge_bns.append(f"f{n}")
            else: edge_bns.append(["f", n])
            break
        elif n in _bn_locs.get("b", []):
            if return_type == str: edge_bns.append(f"b{n}")
            else: edge_bns.append(["b", n])
            break
    #
    return edge_bns
    """



#-------------------------------------------------------------------------------


#===============================================================================
#----------------------------- FORMATTING HELPERS ------------------------------
#===============================================================================
def c2cs(c: Union[str, Tuple[str], List[str]]) -> Tuple[str]:
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


def toggleDirection(d: str) -> str:
    if d == "-": return "+"
    else: return "-"


def bnHalfG(b: str, n: int) -> int:
    if b == "f": return n*2
    else: return (n*2)+1


def bnGauged(b: str, n: int, gauge: int=2) -> int:
    if b == "f": return n*gauge
    else: return (n*gauge)+(gauge//2)


def modsHalveGauge(gauge: int, mod: Union[int, str]) -> Tuple[int,int]: # usage: n % (gauge*2) == mods[0] or n % (gauge*2) == mods[1]
    if type(mod) == str: #passed bed for it
        if mod == "f": mod = 0
        else: mod = gauge//2 # -1 #if gauge=1, this is 0 no matter what so works
    #
    return (mod, mod+gauge)


def bnSplit(bns: Union[str,List[str],Tuple[str]]) -> Union[Tuple[str,int], List[Tuple[str,int]]]:
    if type(bns) == str:
        i = regex.search(r"[a-z]+", bns).end()
        return (bns[:i], int(bns[i:]))
    else:
        split_idxs = [regex.search(r"[a-z]+", val).end() for val in bns]
        return [(val[:i], int(val[i:])) for (val, i) in zip(bns, split_idxs)]


def bnSort(bn_list: List[str]=[], direction: str="+", unique: bool=True) -> List[Tuple[str,int]]:
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


def bnFormat(needles: Union[str, List[str], Tuple[str], Dict[str,int]], bed: Union[str, None]=None, gauge: int=2, sort: bool=True, unique: bool=True, return_type: type=list) -> Union[List[str], Tuple[str], Dict[str,int]]: #TODO: #check and test this #*
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
    elif return_type == tuple: return tuple(out)
    elif return_type == dict:
        d_out = {}
        for val in out:
            b, n = bnSplit(val)
            if b not in d_out: d_out[b] = []
            d_out[b].append(n)
        #
        return d_out
    else: raise ValueError(f"Return type {return_type} not yet supported.")


def rollSequence(seq_str: str, i: int) -> str:
    return seq_str[i%len(seq_str):]+seq_str[:i%len(seq_str)]

#-------------------------------------------------------------------------------


#===============================================================================
#-------------- KNITTING STUFF (here to prevent circular imports) --------------
#===============================================================================
def tuckPattern(k, first_n: int, direction: str, c: Optional[Union[str, List[str], Tuple[str]]]=None, bed: str="f", machine: str="swgn2") -> None: #remember to drop after (aka pass `c=None`)
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

        
def knitPass(k, start_n: int, end_n: int, c: Union[str, List[str], Tuple[str]], bed: str="f", gauge: int=1, avoid_bns: Dict[str,List[int]]={"f": [], "b": []}, init_direction: Optional[str]=None) -> None:
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
    * `init_direction` (str, optional): in *rare* cases (i.e., when only one needle is being knit), the initial pass direction might not be able to be inferred by the values of `start_n` and `end_n`.  In this case, one can specify the direction using this parameter (otherwise, can leave it as the default value, `None`, which indicates that the direction should/can be inferred).
    '''
    cs = c2cs(c) # ensure tuple type
    avoid_bns_list = bnFormat(avoid_bns, gauge=gauge, return_type=list)
    #
    if end_n > start_n or init_direction == "+": #pass is pos
        for n in range(start_n, end_n+1):
            if f"{bed}{n}" not in avoid_bns_list and bnValid(bed, n, gauge): k.knit("+", f"{bed}{n}", *cs) 
            elif n == end_n: k.miss("+", f"{bed}{n}", *cs)
    else: #pass is neg
        for n in range(start_n, end_n-1, -1):
            if f"{bed}{n}" not in avoid_bns_list and bnValid(bed, n, gauge): k.knit("-", f"{bed}{n}", *cs)
            elif n == end_n: k.miss("-", f"{bed}{n}", *cs)


def rackedXfer(k, from_bn: Union[str, Tuple[str,int]], to_bn: Union[str, Tuple[str,int]]) -> None:
    bn1, bn2 = bnFormat([from_bn, to_bn], sort=False, return_type=list)
    if bn1[0][0] == "f": k.rack(bn1[1]-bn2[1])
    else: k.rack(bn2[1]-bn1[1])
    #
    k.xfer(f"{bn1[0]}{bn1[1]}", f"{bn2[0]}{bn2[1]}")
    k.rack(0)


#-------------------------------------------------------------------------------


#===============================================================================
#-------------------------------- CLASS HELPERS --------------------------------
#===============================================================================
class BedNeedle:
    _b_re = r"^[f|b]s?$"
    _n_re = r"^-?\d+$"
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