import knitout
from knitout import shiftDirection #check

from typing import Union, Tuple, List
import re
import warnings
from enum import Enum


import sys
from pathlib import Path

## Standalone boilerplate before relative imports
if not __package__: #remove #?
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name


from .knitout_helpers import Carrier, InactiveCarrierWarning, UnalignedNeedlesWarning, StackedLoopWarning, HeldLoopWarning, UnstableLoopWarning, FloatWarning
from .bed_needle import BedNeedleList
    

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
        self.bns = BedNeedleList()
        # self.row_ct = 0 #?
        self.hook_active = False

        self.setExceptionHandling(enabled_warnings=(KnitoutException.FLOAT, KnitoutException.STACKED_LOOP, KnitoutException.HELD_LOOP, KnitoutException.UNSTABLE_LOOP), enabled_errors=(KnitoutException.INACTIVE_CARRIER, KnitoutException.UNALIGNED_NEEDLES)) #default (can be changed by calling it again with different values) (NOTE: any KnitoutExceptions not included in `enabled_warnings` or `enabled_errors` are ignored by default)
    
    @property
    def row_ct(self):
        return self.bns.getRowCt()

    def setExceptionHandling(self, enabled_warnings: Union[Tuple[KnitoutException], List[KnitoutException], KnitoutException], enabled_errors: Union[Tuple[KnitoutException], List[KnitoutException], KnitoutException]):
        if isinstance(enabled_warnings, KnitoutException): enabled_warnings = [enabled_warnings]
        else: assert isinstance(enabled_warnings, (tuple, list)) and isinstance(enabled_warnings[0], KnitoutException), "'enabled_warnings' parameter must be of type Tuple[KnitoutException], List[KnitoutException], or KnitoutException." #check
        #
        if isinstance(enabled_errors, KnitoutException): enabled_errors = [enabled_errors]
        else: assert isinstance(enabled_errors,  (tuple, list)) and isinstance(enabled_errors[0], KnitoutException), "'enabled_errors' parameter must be of type Tuple[KnitoutException], List[KnitoutException], or KnitoutException." #check
        #
        for w in KnitoutException:
            if w in enabled_errors: 
                warnings.simplefilter("error", w.value)
                w.value.ENABLED = True
            elif w in enabled_warnings: 
                warnings.simplefilter("default", w.value)
                w.value.ENABLED = True
            else:
                warnings.simplefilter("ignore", w.value)
                w.value.ENABLED = False
            # print('{:15} = {}'.format(w.name, w.value)) #remove
    
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
            if c in self.carrier_map: raise ValueError("Attempting to 'inhook' carrier that's already in", c) #TODO: make this a KnitoutException type
            else: self.carrier_map[c] = Carrier()
        #
        assert not self.hook_active, f"Can't inhook carrier(s) '{cs}' since the hook is still holding another yarn." #TODO: improve/make this a KnitoutException
        self.hook_active = True
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
            if not InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="outhook"): del self.carrier_map[c] #check 
        #
        assert not self.hook_active, f"Can't outhook carrier(s) '{cs}' since the hook is still holding another yarn." #TODO: improve/make this a KnitoutException #TODO: check if this is truly an invalid thing to do
        #
        self.operations.append('outhook ' + cs)


    def outcarrier(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if not InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="out"): del self.carrier_map[c] #check 
        self.operations.append('out ' + cs)

    def releasehook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="releasehook")
        #
        assert self.hook_active, f"Can't releasehook carrier(s) '{cs}' since the hook is not holding yarn." #TODO: improve/make this a KnitoutException
        self.hook_active = False
        #
        self.operations.append('releasehook ' + cs)
    
    def rack(self, r: Union[int,float]):
        if self.rack_value != r: #keep #?
            super().rack(r)
            self.rack_value = r

    def knit(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            FloatWarning.check(self, warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="knit"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
        #
        HeldLoopWarning.check(self, warnings, self.bns, bed, needle) #new #check
        #
        self.operations.append('knit ' + direction + ' ' + bn + ' ' + cs)
        #
        self.bns.increment((bed,needle), is_tuck=False)


    def tuck(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            FloatWarning.check(self, warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="tuck"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
        #
        HeldLoopWarning.check(self, warnings, self.bns, bed, needle) #new #check
        #
        self.operations.append('tuck ' + direction + ' ' + bn + ' ' + cs)
        #
        self.bns.increment((bed,needle), is_tuck=True)
        StackedLoopWarning.check(self, warnings, self.bns, bed, needle) #check
        # self.setLoc(bed, needle, is_tuck=True)

    def xfer(self, *args):
        argl = list(args)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        #
        UnalignedNeedlesWarning.check(self, warnings, self.rack_value, bed, needle, bed2, needle2)
        #
        self.operations.append('xfer ' + bn_from + ' ' + bn_to)
        #
        self.bns.xfer((bed,needle), (bed2,needle2), is_split=False)
        StackedLoopWarning.check(self, warnings, self.bns, bed2, needle2) #check
        # self.xferLoc(bed, needle, bed2, needle2)


    def split(self, *args):
        argl = list(args)
        direction  = shiftDirection(argl)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        UnalignedNeedlesWarning.check(self, warnings, self.rack_value, bed, needle, bed2, needle2)
        #
        for c in carriers:
            FloatWarning.check(self, warnings, self.carrier_map, c, needle)
            #
            if InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="split"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
        #
        HeldLoopWarning.check(self, warnings, self.bns, bed, needle) #new #check
        #
        self.operations.append('split '+ direction + ' '  + bn_from + ' ' + bn_to + ' ' + cs)
        #
        self.bns.xfer((bed,needle), (bed2,needle2), is_split=True)
        StackedLoopWarning.check(self, warnings, self.bns, bed2, needle2) #check

    def miss(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        for c in carriers:
            if InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op="miss"): self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
            else: self.carrier_map[c].update(direction, bed, needle)
        #
        self.operations.append('miss ' + direction + ' ' + bn + ' ' + cs)
    
    def drop(self, *args):
        argl = list(args)
        bn, (bed, needle) = shiftBedNeedle(argl)
        self.operations.append('drop ' + bn)
        #
        self.bns.remove((bed,needle))

    def clear(self):
        #clear buffers
        self.headers = list()
        self.operations = list()
        #
        self.rack_value = 0
        self.carrier_map = dict()
        self.bns = BedNeedleList()



