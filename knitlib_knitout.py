import knitout
from knitout import shiftDirection #check

from typing import Union, Tuple, List
import re
import warnings
from enum import Enum

from .knitout_helpers import Carrier, InactiveCarrierWarning, UnalignedNeedlesWarning, StackedLoopWarning, HeldLoopWarning, UnstableLoopWarning, FloatWarning
    

class KnitoutException(Enum):
    INACTIVE_CARRIER = InactiveCarrierWarning
    #TODO: add double inhook carrier too
    UNALIGNED_NEEDLES = UnalignedNeedlesWarning
    FLOAT = FloatWarning
    STACKED_LOOP = StackedLoopWarning
    HELD_LOOP = HeldLoopWarning #TODO
    UNSTABLE_LOOP = UnstableLoopWarning #TODO
    


# # ou can utilize the handy warnings.simplefilter() method using the 1st parameter in [‘error’, ‘ignore’, ‘default’, ‘module’, ‘always’, ‘once’] to control how all warnings are dealt with or using a second parameter Category in order to only have the simplefilter() method controls only some warnings. For example:
# # adding a single entry into warnings filter 
# warnings.simplefilter("error", StackedLoopWarning) 

# warnings.filterwarnings("ignore") #start out by ignoring all warnings
# # warnings.warn("", StackedLoopWarning)

  

reg = re.compile(r"^([f|b]s?)(-?\d+)?$") #TODO: decide if should keep as compile #?

def getBedNeedle(bn: str):
    res = re.match(r"^([f|b]s?)(-?\d+)$", bn)
    if res is not None:
        bed, needle = res.group(1), int(res.group(2))
        return bed, needle
    else: raise ValueError(f"'{bn}' is not a valid bed-needle string.")


def shiftCarrierSet(args, carriers):
    if len(args) == 0:
        raise AssertionError("No carriers specified")
    for c in args:
        if not str(c) in carriers:
            raise ValueError("Carrier not specified in initial set", c)
    cs = [str(c) for c in args]
    return ' '.join(cs), cs


def shiftBedNeedle(args):
    if len(args) == 0:
        raise AssertionError("No needles specified")
    bn = args.pop(0)
    bed = None
    needle = None
    #
    if isinstance(bn, str):
        m = reg.match(bn)
        if m is None:
            raise ValueError("Invalid BedNeedle string.", bn)
        else:
            bed = m.group(1)
            if m.group(2) is not None:
                needle = int(m.group(2))
            elif isinstance(args[0], int) or args[0].isdigit():
                needle = int(args.pop(0))
            else:
                raise ValueError("Invalid needle. Must be numeric.", m.group(2))
    elif isinstance(bn, (list, tuple)):
        if len(bn) != 2:
            raise ValueError("Bed and Needle need to be supplied.")
        if (bn[0] == 'f' or bn[0] == 'b' or bn[0] == 'fs' or bn[0] == 'bs'):
            bed = bn[0]
        else:
            raise ValueError("Invalid bed type. Must be 'f' 'b' 'fs' 'bs'.")
        if isinstance(bn[1], int) or bn[1].isdigit():
            needle = int(bn[1])
        else:
            raise ValueError("2.Invalid needle. Must be numeric.")
    else:
        raise AssertionError("Invalid BedNeedle type")
    #
    return bed+str(needle), (bed, needle)


class Writer(knitout.Writer):
    def __init__(self, cs):
        super().__init__(cs)
        #
        self.rack_value = 0
        # self.in_carriers = list()
        self.carrier_map = dict()
        self.stacked_bns = {"f": [], "b": [], "fs": [], "bs": []} #keep #?
        self.bn_locs = {"f": [], "b": [], "fs": [], "bs": []}

        self.setExceptionHandling(enabled_warnings=(KnitoutException.FLOAT, KnitoutException.STACKED_LOOP, KnitoutException.HELD_LOOP, KnitoutException.UNSTABLE_LOOP), enabled_errors=(KnitoutException.INACTIVE_CARRIER, KnitoutException.UNALIGNED_NEEDLES)) #default (can be changed by calling it again with different values) (NOTE: any KnitoutExceptions not included in `enabled_warnings` or `enabled_errors` are ignored by default)
    
    # def verifyCarriers(self, carriers) -> None:
    #     for c in carriers:
    #         if c not in self.in_carriers: raise ValueError("Carrier not already in", c)

    # def enableAllWarnings(self):

    def setExceptionHandling(self, enabled_warnings: Union[Tuple[KnitoutException], List[KnitoutException], KnitoutException], enabled_errors: Union[Tuple[KnitoutException], List[KnitoutException], KnitoutException]):
        if isinstance(enabled_warnings, KnitoutException): enabled_warnings = [enabled_warnings]
        else: assert isinstance(enabled_warnings, (Tuple[KnitoutException], List[KnitoutException])), "'enabled_warnings' parameter must be of type Tuple[KnitoutException], List[KnitoutException], or KnitoutException." #check
        #
        if isinstance(enabled_errors, KnitoutException): enabled_errors = [enabled_errors]
        else: assert isinstance(enabled_errors, (Tuple[KnitoutException], List[KnitoutException])), "'enabled_errors' parameter must be of type Tuple[KnitoutException], List[KnitoutException], or KnitoutException." #check
        #
        for w in KnitoutException:
            if w in enabled_errors: warnings.simplefilter("error", w.value)
            elif w in enabled_warnings: warnings.simplefilter("default", w.value)
            else: warnings.simplefilter("ignore", w.value)
            # print('{:15} = {}'.format(w.name, w.value)) #remove


    def setLoc(self, bed, needle, is_tuck=False):
        if needle not in self.bn_locs[bed]: self.bn_locs[bed].append(needle)
        else:
            if is_tuck:
                self.stacked_bns[bed].append(needle)
                #
                StackedLoopWarning.check(warnings, self.stacked_bns, bed, needle) #check
                # stack_ct = self.stacked_bns[bed].count(needle)
                # if stack_ct > 1: warnings.warn(StackedLoopWarning(f"{bed}{needle}", stack_ct)) #warnings.warn(f"{stack_ct} loops stacked on '{bed}{needle}'")
            else: self.stacked_bns[bed] = [n for n in self.stacked_bns[bed] if n != needle] #filter out all occurrences
    
    def unsetLoc(self, bed, needle):
        if needle in self.bn_locs[bed]: self.bn_locs[bed].remove(needle)
        #
        if needle in self.stacked_bns[bed]:
            self.stacked_bns[bed] = [n for n in self.stacked_bns[bed] if n != needle] #filter out all occurrences

    def xferLoc(self, bed, needle, bed2, needle2, is_split=False): #check
        bed_stacked = self.stacked_bns[bed].copy() #TODO: see if needle deep copy
        # bed2_stacked = self.stack_bns[bed2].copy()
        #
        if needle in self.bn_locs[bed]:
            if needle2 not in self.bn_locs[bed2]: self.bn_locs[bed2].append(needle2)
            if not is_split: self.bn_locs[bed].remove(needle)
        elif is_split: self.bn_locs[bed].append(needle)
        #
        if needle in bed_stacked:
            for n in bed_stacked:
                if n == needle:
                    self.stacked_bns[bed].remove(needle)
                    self.stacked_bns[bed2].append(needle2)
            #
            StackedLoopWarning.check(warnings, self.stacked_bns, bed2, needle2) #check
            # stack_ct = self.stacked_bns[bed2].count(needle2)
            # if stack_ct > 1:  warnings.warn(StackedLoopWarning(f"{bed2}{needle2}", stack_ct)) #warnings.warn(f"{stack_ct} loops stacked on '{bed2}{needle2}'")
        #
        # if is_split and needle2 in bed2_stacked:
        #     for n in bed2_stacked:
        #         if n == needle2:
        #             self.stacked_bns[bed2].remove(needle2)
        #             self.stacked_bns[bed].append(needle)
    
    # patch on x-vis-color method:
    def visColor(self, hexcode, *args):
        if hexcode[0] != '#': hexcode = '#' + hexcode
        cs = ' '.join(str(c) for c in args)
        self.operations.append(f'x-vis-color {hexcode} {cs}')
    
    #===========================================================================
    def inhook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if c in self.carrier_map: raise ValueError("Attempting to 'inhook' carrier that's already in", c)
            else: self.carrier_map[c] = Carrier() # self.in_carriers.append(c)
        # self.in_carriers.extend(carriers)
        #
        self.operations.append('inhook ' + cs)
    
    def incarrier(self, *args): #NOTE: can't name func `in` since that is a keyword in python
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        for c in carriers:
            if c in self.carrier_map: raise ValueError("Attempting to 'in' carrier that's already in", c)
            else: self.carrier_map[c] = Carrier()
        # self.in_carriers.extend(carriers)
        #
        self.operations.append('in ' + cs)

    def outhook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if not InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="outhook"): del self.carrier_map[c] #check 
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "outhook")) #raise ValueError("Attempting to 'outhook' carrier that is not already in", c)
            # else: del self.carrier_map[c] #check #self.in_carriers.remove(c)
        #
        self.operations.append('outhook ' + cs)


    def outcarrier(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if not InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="out"): del self.carrier_map[c] #check 
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "out")) #raise ValueError("Attempting to 'out' carrier that is not already in", c)
            # else: del self.carrier_map[c] 
        self.operations.append('out ' + cs)

    def releasehook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="releasehook")
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "releasehook")) #raise ValueError("Attempting to 'releasehook' carrier that is not already in", c)
        #
        self.operations.append('releasehook ' + cs)
    
    def rack(self, r):
        super().rack(r)
        self.rack_value = r

    def knit(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            FloatWarning.check(warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="knit"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "knit")) #raise ValueError("Attempting to 'knit' with carrier that is not already in", c)
            # else: self.carrier_map[c].update(direction, bed, needle)
        #
        self.operations.append('knit ' + direction + ' ' + bn + ' ' + cs)
        #
        self.setLoc(bed, needle)
        # bed, needle = getBedNeedle(bn)

        # super().knit(*args)

    def tuck(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            FloatWarning.check(warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="tuck"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
            # if c not in self.carrier_map:warnings.warn(InactiveCarrierWarning(c, "tuck")) #raise ValueError("Attempting to 'tuck' with carrier that is not already in", c)
            # else: self.carrier_map[c].update(direction, bed, needle)
        #
        self.operations.append('tuck ' + direction + ' ' + bn + ' ' + cs)
        #
        self.setLoc(bed, needle, is_tuck=True)

    def xfer(self, *args):
        argl = list(args)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        #
        UnalignedNeedlesWarning.check(warnings, self.rack_value, bed, needle, bed2, needle2)
        # assert bed[0] != bed2[0], f"can't xfer to/from to same bed ({bed} -> {bed2})"
        # if bed[0] == "f":
        #     if needle-needle2 != self.rack_value: warnings.warn(UnalignedRackWarning(self.rack_value, bn_from, bn_to))
        # else:
        #     if needle2-needle != self.rack_value: warnings.warn(UnalignedRackWarning(self.rack_value, bn_from, bn_to))
        #
        self.operations.append('xfer ' + bn_from + ' ' + bn_to)
        #
        self.xferLoc(bed, needle, bed2, needle2)
        # self.unsetLoc(bed, needle)
        # self.setLoc(bed2, needle2)


    def split(self, *args):
        argl = list(args)
        direction  = shiftDirection(argl)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        UnalignedNeedlesWarning.check(warnings, self.rack_value, bed, needle, bed2, needle2)
        # assert bed[0] != bed2[0], f"can't split to/from to same bed ({bed} -> {bed2})"
        # if bed[0] == "f":
        #     if needle-needle2 != self.rack_value: warnings.warn(UnalignedRackWarning(self.rack_value, bn_from, bn_to))
        # else:
        #     if needle2-needle != self.rack_value: warnings.warn(UnalignedRackWarning(self.rack_value, bn_from, bn_to))
        #
        for c in carriers:
            FloatWarning.check(warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="split"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "split")) #raise ValueError("Attempting to 'split' with carrier that is not already in", c)
            # else: self.carrier_map[c].update(direction, bed, needle)
        #
        self.operations.append('split '+ direction + ' '  + bn_from + ' ' + bn_to + ' ' + cs)
        #
        self.xferLoc(bed, needle, bed2, needle2, is_split=True)
        # self.setLoc(bed2, needle2)

    def miss(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if InactiveCarrierWarning.check(warnings, self.carrier_map, c, op="miss"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
            # if c not in self.carrier_map: warnings.warn(InactiveCarrierWarning(c, "miss")) #raise ValueError("Attempting to 'miss' with carrier that is not already in", c)
            # else: self.carrier_map[c].update(direction, bed, needle)
        #
        self.operations.append('miss ' + direction + ' ' + bn + ' ' + cs)
    
    def drop(self, *args):
        argl = list(args)
        bn, (bed, needle) = shiftBedNeedle(argl)
        self.operations.append('drop ' + bn)
        #
        self.unsetLoc(bed, needle)

    def clear(self):
        #clear buffers
        self.headers = list()
        self.operations = list()
        #
        self.rack_value = 0
        self.carrier_map = dict()
        self.stacked_bns = {"f": [], "b": [], "fs": [], "bs": []}
        self.bn_locs = {"f": [], "b": [], "fs": [], "bs": []}



