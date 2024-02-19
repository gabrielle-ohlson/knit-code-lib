from typing import Union, Optional, Dict, Tuple, List, Callable
import math

from knitlib import zigzagCaston, sheetBindoff
from .helpers import bnValid
# from .bed_needle import BedNeedle


def decEdge(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]): #TODO: add check for if it is a valid place to transfer to
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    #
    if from_needle < to_needle:
        for i in range(to_needle-from_needle):
            obj.rackedXfer((from_bed, from_needle+i), (to_bed, to_needle+i), reset_rack=False)
    else:
        for i in range(from_needle-to_needle):
            obj.rackedXfer((from_bed, from_needle-i), (to_bed, to_needle-i), reset_rack=False)
    obj.rack(0)


def decSchoolBus(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]):
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    assert to_bed == from_bed, "school-bus decrease to opposite bed not supported yet"
    #
    if from_needle > to_needle: #right side
        ct = from_needle-to_needle
        obj.k.comment(f"decrease {ct} on right") #debug
        if from_bed.startswith("f"):
            xto_bed = "bs"
        else:
            xto_bed = "fs"
        #
        min_n = obj.getMinNeedle(from_bed[0])
        if from_needle-ct+1 > min_n: # valid school bus operation
            w = from_needle-min_n+1
            ct_2 = ct*ct
            r = ct_2/(w-ct)
            r = max(obj.gauge, int(r-math.fmod(r, obj.gauge))) #TODO: #check
            assert r <= obj.MAX_RACK

            sects = math.ceil(ct/r) #TODO: #check
            start_n = from_needle

            for i in range(sects):
                for m in range(0, sects-i):
                    for n in range(start_n-i*r-m*ct, (start_n-i*r-m*ct)-ct, -1):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((from_bed, n), (xto_bed, n-r), reset_rack=False)

                for m in range(0, sects-i):
                    for n in range((start_n-i*r-m*ct)-r, (start_n-i*r-m*ct)-ct-r, -1):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((xto_bed, n), (from_bed, n), reset_rack=False)
                
                """
                for n in range(start_n-i*r-(sects-i)*ct, (start_n-i*r-(sects-i)*ct)-r, -1):
                    if bnValid(from_bed, n, obj.gauge):
                        print(f"stack: {n}") #remove #debug
                """
            #
            obj.rack(0)
        else:
            raise RuntimeError(f"not enough working needles to decrease by {ct} using the school-bus method.")
    else: #left side
        ct = to_needle-from_needle
        obj.k.comment(f"decrease {ct} on left") #debug
        if from_bed.startswith("f"):
            xto_bed = "bs"
        else:
            xto_bed = "fs"
        #
        if to_bed is None: to_bed = from_bed
        #
        assert to_bed == from_bed, "school-bus decrease to opposite bed not supported yet"
        #
        max_n = obj.getMaxNeedle(from_bed[0])
        if from_needle-ct+1 < max_n: # valid school bus operation
            w = max_n-from_needle+1
            ct_2 = ct*ct
            r = ct_2/(w-ct)
            r = max(obj.gauge, int(r-math.fmod(r, obj.gauge))) #TODO: #check
            assert r <= obj.MAX_RACK

            sects = math.ceil(ct/r) #TODO: #check
            start_n = from_needle

            for i in range(sects):
                for m in range(0, sects-i):
                    for n in range(start_n+i*r+m*ct, (start_n+i*r+m*ct)+ct):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((from_bed, n), (xto_bed, n+r), reset_rack=False)

                for m in range(0, sects-i):
                    for n in range((start_n+i*r+m*ct)+r, (start_n+i*r+m*ct)+ct+r):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((xto_bed, n), (from_bed, n), reset_rack=False)
                
                """
                for n in range(start_n+i*r+(sects-i)*ct, (start_n+i*r+(sects-i)*ct)+r):
                    if bnValid(from_bed, n, obj.gauge):
                        print(f"stack: {n}") #remove #debug
                """
            #
            obj.rack(0)
        else:
            raise RuntimeError(f"not enough working needles to decrease by {ct} using the school-bus method.")
    

def decBindoff(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]): #TODO: have option for if double bed or not (aka use sliders instead if still want to keep needles on other bed)
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    #
    sheetBindoff(obj, from_needle, to_needle, from_bed, obj.gauge, add_tag=False)
    if to_bed is not None and from_bed != to_bed: obj.rackedXfer((from_bed, to_needle), to_bn)


#===============================================================================
def incEdge(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]):
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    #
    if from_needle < to_needle:
        for i in range(0, to_needle-from_needle+2, 2):
            obj.rackedXfer((from_bed, from_needle-i//2), (to_bed, to_needle-i), reset_rack=False)
            #
            obj.twist_bns.append(f"{to_bed}{to_needle-i-1}")
    else:
        for i in range(0, from_needle-to_needle+2, 2):
            obj.rackedXfer((from_bed, from_needle+i//2), (to_bed, to_needle+i), reset_rack=False)
            #
            obj.twist_bns.append(f"{to_bed}{to_needle+i+1}")
    obj.rack(0)
    # obj.xfer(from_bn, to_bn)
    # obj.twist_bns.append(from_bn) #TODO


def incSchoolBus(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]):
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    assert to_bed == from_bed, "school-bus increase to opposite bed not supported yet"
    #
    if from_needle < to_needle: #right side
        ct = to_needle-from_needle
        obj.k.comment(f"increase {ct} on right") #debug
        if from_bed.startswith("f"):
            xto_bed = "bs"
        else:
            xto_bed = "fs"
        #
        min_n = obj.getMinNeedle(from_bed[0])
        if from_needle-ct+1 > min_n: # valid school bus operation
            w = from_needle-min_n+1
            ct_2 = ct*ct
            r = ct_2/(w-ct)
            r = max(obj.gauge, int(r-math.fmod(r, obj.gauge))) #TODO: #check
            assert r <= obj.MAX_RACK

            sects = math.ceil(ct/r) #TODO: #check
            start_n = from_needle - ct*sects + 1

            for i in range(sects):
                for m in range(i, sects):
                    for n in range(start_n+i*r+m*ct, (start_n+i*r+m*ct)+ct):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((from_bed, n), (xto_bed, n+r), reset_rack=False)

                for m in range(i, sects):
                    for n in range((start_n+i*r+m*ct)+r, (start_n+i*r+m*ct)+ct+r):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((xto_bed, n), (from_bed, n), reset_rack=False)
                
                for n in range(start_n+i*r+i*ct, (start_n+i*r+i*ct)+r):
                    if bnValid(from_bed, n, obj.gauge): obj.twist_bns.append(f"{from_bed}{n}") #TODO: make these splits instead #?
            #
            obj.rack(0)
        else:
            raise RuntimeError(f"not enough working needles to increase by {ct} using the school-bus method.")
    else: #left side
        ct = from_needle-to_needle
        obj.k.comment(f"increase {ct} on left") #debug
        if from_bed.startswith("f"):
            xto_bed = "bs"
        else:
            xto_bed = "fs"
        #
        if to_bed is None: to_bed = from_bed
        #
        assert to_bed == from_bed, "school-bus increase to opposite bed not supported yet"
        #
        max_n = obj.getMaxNeedle(from_bed[0])
        if from_needle+ct-1 < max_n: # valid school bus operation
            w = max_n-from_needle+1
            ct_2 = ct*ct
            r = ct_2/(w-ct)
            r = max(obj.gauge, int(r-math.fmod(r, obj.gauge))) #TODO: #check
            assert r <= obj.MAX_RACK

            sects = math.ceil(ct/r) #TODO: #check
            start_n = from_needle + ct*sects - 1

            for i in range(sects):
                for m in range(i, sects):
                    for n in range(start_n-i*r-m*ct, (start_n-i*r-m*ct)-ct, -1):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((from_bed, n), (xto_bed, n-r), reset_rack=False)

                for m in range(i, sects):
                    for n in range((start_n-i*r-m*ct)-r, (start_n-i*r-m*ct)-ct-r, -1):
                        if bnValid(from_bed, n, obj.gauge): obj.rackedXfer((xto_bed, n), (from_bed, n), reset_rack=False)
                
                for n in range(start_n-i*r-i*ct, (start_n-i*r-i*ct)-r, -1):
                    if bnValid(from_bed, n, obj.gauge):
                        # print(f"twist: {n}") #remove #debug
                        obj.twist_bns.append(f"{from_bed}{n}")
            #
            obj.rack(0)
        else:
            raise RuntimeError(f"not enough working needles to increase by {ct} using the school-bus method.")
    

def incCaston(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]):
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    #
    assert obj.active_carrier is not None
    if from_needle < to_needle: #right side
        # zigzagCaston(obj, BedNeedle(from_bed, from_needle+1), to_bn, obj.active_carrier)
        zigzagCaston(obj, from_needle+1, to_needle, obj.active_carrier, obj.gauge)
        for n in range(from_needle+1, to_needle+1):
            test_bn = ("b", n) #?
            if n in obj.avoid_bns["b"]:
                next_bn = obj.findNextValidNeedle(*test_bn, in_limits=True)
                obj.rackedXfer(test_bn, next_bn)
                # obj.active_bns.append(next_bn) #TODO
    else: #left side
        zigzagCaston(obj, from_needle-1, to_needle, obj.active_carrier, obj.gauge)
        # zigzagCaston(obj, BedNeedle(from_bed, from_needle-1), to_bn, obj.active_carrier)


def incSplit(obj, from_bn: Tuple[str, int], to_bn: Tuple[Optional[str], int]):
    from_bed, from_needle = from_bn
    to_bed, to_needle = to_bn
    if to_bed is None: to_bed = from_bed
    #
    if from_needle < to_needle: #right side
        raise NotImplementedError("TODO")
    else: #left side
        raise NotImplementedError("TODO")