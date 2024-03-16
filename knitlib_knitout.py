import knitout
from knitout import shiftDirection #check

from typing import Union, Tuple, List
import re
import warnings
from enum import Enum

from queue import Queue
from threading import Thread

import sys
from pathlib import Path

## Standalone boilerplate before relative imports
if not __package__: #remove #?
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name


from .knitout_helpers import IncList, Carrier, InactiveCarrierWarning, UnalignedNeedlesWarning, FloatWarning, StackedLoopWarning, HeldLoopWarning, UnstableLoopWarning, EmptyXferWarning

from .bed_needle import BedNeedleList
    

class KnitoutException(Enum):
    INACTIVE_CARRIER = InactiveCarrierWarning
    #TODO: add double inhook carrier too
    UNALIGNED_NEEDLES = UnalignedNeedlesWarning
    FLOAT = FloatWarning
    STACKED_LOOP = StackedLoopWarning
    HELD_LOOP = HeldLoopWarning #TODO
    UNSTABLE_LOOP = UnstableLoopWarning #TODO
    EMPTY_XFER = EmptyXferWarning
    


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


def ValidationThread(q):
    while True:
        (f, ln, args) = q.get()
        if f is None: break
        if f(*args): print(f"@ line {ln+1}") #debug

class Writer(knitout.Writer):
    def __init__(self, cs):
        super().__init__(cs)
        #
        self.line_number = 0
        # array of operations, strings
        self.operations = IncList()
        self.operations.increment = self.updateLineNumber
        #
        headers = self.headers
        self.headers = IncList() #self.headers)
        self.headers.increment = self.updateLineNumber
        self.headers.extend(headers)
        #
        self.rack_value = 0
        # self.in_carriers = list()
        self.carrier_map = dict()
        self.bns = BedNeedleList()
        # self.row_ct = 0 #?
        self.hook_active = False

        self.setExceptionHandling(enabled_warnings=(KnitoutException.FLOAT, KnitoutException.STACKED_LOOP, KnitoutException.UNSTABLE_LOOP, KnitoutException.EMPTY_XFER), enabled_errors=(KnitoutException.HELD_LOOP, KnitoutException.INACTIVE_CARRIER, KnitoutException.UNALIGNED_NEEDLES)) #default (can be changed by calling it again with different values) (NOTE: any KnitoutExceptions not included in `enabled_warnings` or `enabled_errors` are ignored by default)
        #
        self.q = Queue()
        self.thread = Thread(target=ValidationThread, args=(self.q,), daemon=True)
        # self.thread.daemon = True
        self.thread.start()

    @property
    def row_ct(self):
        return self.bns.getRowCt()
    
    def updateLineNumber(self, n):
        self.line_number += n
    
    def updateCarrier(self, c, op, direction, bed, needle): #*
        w = InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op=op)
        if w: self.carrier_map[c] = Carrier(direction, bed, needle) #warning raised, but not error level
        else: self.carrier_map[c].update(direction, bed, needle)
        #
        return w

    def addCarrier(self, c, op):
        if c in self.carrier_map:
            raise ValueError(f"Attempting to '{op}' carrier that's already in", c) #TODO: make this a KnitoutException type #*#*
            return True
        else:
            self.carrier_map[c] = Carrier()
            return False

    def removeCarrier(self, c, op): #*
        w = InactiveCarrierWarning.check(self, warnings, self.carrier_map, c, op=op)
        if not w: del self.carrier_map[c]
        #
        return w

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
        assert not self.hook_active, f"Can't inhook carrier(s) '{cs}' since the hook is still holding another yarn." #TODO: improve/make this a KnitoutException
        self.hook_active = True
        #
        self.operations.append('inhook ' + cs)
        #
        for c in carriers:
            self.q.put( (self.addCarrier, self.line_number, (c, "inhook")) ) #*
    
    def incarrier(self, *args): #NOTE: can't name func `in` since that is a keyword in python
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('in ' + cs)
        #
        for c in carriers:
            self.q.put( (self.addCarrier, self.line_number, (c, "in")) ) #*

    def outhook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        assert not self.hook_active, f"Can't outhook carrier(s) '{cs}' since the hook is still holding another yarn." #TODO: improve/make this a KnitoutException #TODO: check if this is truly an invalid thing to do
        #
        self.operations.append('outhook ' + cs)
        #
        for c in carriers:
            self.q.put( (self.removeCarrier, self.line_number, (c, "outhook")) ) #*

    def outcarrier(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('out ' + cs)
        #
        for c in carriers:
            self.q.put( (self.removeCarrier, self.line_number, (c, "out")) ) #*

    def releasehook(self, *args):
        argl = list(args)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        assert self.hook_active, f"Can't releasehook carrier(s) '{cs}' since the hook is not holding yarn." #TODO: improve/make this a KnitoutException
        self.hook_active = False
        #
        self.operations.append('releasehook ' + cs)
        #
        for c in carriers:
            self.q.put( (InactiveCarrierWarning.check, self.line_number, (self, warnings, self.carrier_map,c, "releasehook")) ) #*
    
    def rack(self, r: Union[int,float]): #*#*
        if self.rack_value != r: #keep #?
            super().rack(r)
            self.rack_value = r

    def knit(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('knit ' + direction + ' ' + bn + ' ' + cs)
        #
        for c in carriers:
            self.q.put( (FloatWarning.check, self.line_number, (self, warnings, self.carrier_map, c, needle)) ) #*
            #
            self.q.put( (self.updateCarrier, self.line_number, (c, "knit", direction, bed, needle)) ) #*
        #
        self.q.put( (HeldLoopWarning.check, self.line_number, (self, warnings, self.row_ct, self.bns.get(bn), bed, needle)) ) #* #copy #?
        #
        self.bns.increment((bed,needle), is_tuck=False) #*#*


    def tuck(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('tuck ' + direction + ' ' + bn + ' ' + cs)
        #
        for c in carriers:
            self.q.put( (FloatWarning.check, self.line_number, (self, warnings, self.carrier_map, c, needle)) ) #*
            #
            self.q.put( (self.updateCarrier, self.line_number, (c, "tuck", direction, bed, needle)) ) #*
        #
        self.q.put( (HeldLoopWarning.check, self.line_number, (self, warnings, self.row_ct, self.bns.get(bn), bed, needle)) ) #* #copy #?
        #
        self.bns.increment((bed,needle), is_tuck=True) #*#*
        self.q.put( (StackedLoopWarning.check, self.line_number, (self, warnings, self.bns.get(bn), bed, needle)) ) #* #copy #?

    def xfer(self, *args):
        argl = list(args)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        #
        self.operations.append('xfer ' + bn_from + ' ' + bn_to)
        #
        self.q.put( (UnalignedNeedlesWarning.check, self.line_number, (self, warnings, self.rack_value, bed, needle, bed2, needle2)) ) #*
        self.q.put( (EmptyXferWarning.check, self.line_number, (self, warnings, self.bns.get(bn_from), bed, needle)) ) #* #copy #?
        #
        self.bns.xfer((bed,needle), (bed2,needle2), is_split=False) #*#*
        self.q.put( (StackedLoopWarning.check, self.line_number, (self, warnings, self.bns.get(bn_to), bed2, needle2)) ) #* #copy #?

    def split(self, *args):
        argl = list(args)
        direction  = shiftDirection(argl)
        bn_from, (bed, needle) = shiftBedNeedle(argl)
        bn_to, (bed2, needle2) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('split '+ direction + ' '  + bn_from + ' ' + bn_to + ' ' + cs)
        #
        self.q.put( (UnalignedNeedlesWarning.check, self.line_number, (self, warnings, self.rack_value, bed, needle, bed2, needle2)) ) #*
        self.q.put( (EmptyXferWarning.check, self.line_number, (self, warnings, self.bns.get(bn_from), bed, needle)) ) #* #copy #?
        #
        for c in carriers:
            self.q.put( (FloatWarning.check, self.line_number, (self, warnings, self.carrier_map, c, needle)) ) #* #TODO: deepcopy for these #*#*#*
            #
            self.q.put( (self.updateCarrier, self.line_number, (c, "split", direction, bed, needle)) ) #* #TODO: deepcopy for these #? #*#*#*
        #
        self.q.put( (HeldLoopWarning.check, self.line_number, (self, warnings, self.row_ct, self.bns.get(bn_from), bed, needle)) ) #* #copy #?
        #
        self.bns.xfer((bed,needle), (bed2,needle2), is_split=True) #*#*
        self.q.put( (StackedLoopWarning.check, self.line_number, (self, warnings, self.bns.get(bn_to), bed2, needle2)) ) #* #copy #?

    def miss(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn, (bed, needle) = shiftBedNeedle(argl)
        cs, carriers = shiftCarrierSet(argl, self.carriers)
        #
        self.operations.append('miss ' + direction + ' ' + bn + ' ' + cs)
        #
        for c in carriers:
            self.q.put( (self.updateCarrier, self.line_number, (c, "miss", direction, bed, needle)) ) #*
    
    def drop(self, *args):
        argl = list(args)
        bn, (bed, needle) = shiftBedNeedle(argl)
        #
        self.operations.append('drop ' + bn)
        #
        self.q.put( (HeldLoopWarning.check, self.line_number, (self, warnings, self.row_ct, self.bns.get(bn), bed, needle)) ) #* #copy #?
        #
        self.bns.remove((bed,needle)) #*#*

    def clear(self):
        #clear buffers
        self.headers = list()
        self.operations = list()
        #
        self.rack_value = 0
        self.carrier_map = dict()
        self.bns = BedNeedleList()

    def write(self, filename):
        for bn in self.bns:
            self.q.put( (HeldLoopWarning.check, self.line_number, (self, warnings, self.row_ct, self.bns.get(bn), bn.bed, bn.needle)) ) #* #copy #?
        #
        self.q.put((None, None, None)) #indicates we're done
        #
        version = ';!knitout-2\n'
        content = version + '\n'.join(self.headers) + '\n' +  '\n'.join(self.operations)
        try:
            with open(filename, "w") as out:
                print(content, file=out)
            print('wrote file ' + filename)
        except IOError as error:
            print('Could not write to file ' + filename)
        #
        self.thread.join()

