class Carrier:
    def __init__(self, direction=None, bed=None, needle=None):
        self.direction = direction
        self.bed = bed
        self.needle = needle
    #
    def update(self, direction=None, bed=None, needle=None):
        if direction is not None: self.direction = direction
        if bed is not None: self.bed = bed
        if needle is not None: self.needle = needle


class InactiveCarrierWarning(UserWarning):
    def __init__(self, c: str, op: str='use'):
        self.message = f"Attempting to {op} carrier '{c}', which hasn't been brought in yet."

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, carrier_map, c, op="use") -> bool:
        if c not in carrier_map:
            warnings.warn(InactiveCarrierWarning(c, op))
            return True
        else: return False


class UnalignedNeedlesWarning(UserWarning):
    def __init__(self, r: int, bn: str, bn2: str):
        self.message = f"'{bn}' and '{bn2}' are unaligned at rack {r}."

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, rack_value, bed, needle, bed2, needle2) -> bool:
        if bed[0] == bed2[0]:
            print(f"can't xfer to/from to same bed ({bed} -> {bed2})")
            warnings.warn(UnalignedNeedlesWarning(rack_value, f"{bed}{needle}", f"{bed2}{needle2}"))
            return True
        elif (bed[0] == "f" and needle-needle2 != rack_value) or (bed[0] == "b" and needle2-needle != self.rack_value):
            warnings.warn(UnalignedNeedlesWarning(rack_value, f"{bed}{needle}", f"{bed2}{needle2}"))
        else: return False



class StackedLoopWarning(UserWarning):
    def __init__(self, bn: str, count: int):
        self.message = f"{count} loops stacked on '{bn}'"

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, stacked_bns, bed, needle) -> bool:
        stack_ct = stacked_bns[bed].count(needle)
        if stack_ct > 1:
            warnings.warn(StackedLoopWarning(f"{bed}{needle}", stack_ct))
            return True
        else: return False


class HeldLoopWarning(UserWarning):
    def __init__(self, bn: str, n_rows: int):
        self.message = f"'{bn}' has been holding an unknit loop for {n_rows} rows." #TODO: phrase this better

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, bn_locs, bed, needle) -> bool:
        raise NotImplementedError
    

class UnstableLoopWarning(UserWarning):
    def __init__(self, bn: str):
        self.message = f"Attempting to knit on '{bn}', which does not yet have a stable loop formed." #TODO: phrase this better

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, bn_locs, bed, needle) -> bool:
        raise NotImplementedError
    

class FloatWarning(UserWarning):
    MIN_FLOAT_LEN = 6 #TODO: add option to adjust

    def __init__(self, c: str, prev_needle: int, needle: int):
        self.message = f"Float of length {abs(needle-prev_needle)} formed bringing carrier '{c}' from previous position, needle {prev_needle}, to needle {needle}." #TODO: phrase this better

    def __str__(self):
        return repr(self.message)
    
    @classmethod
    def check(self, warnings, carrier_map, c, needle) -> bool:
        prev_needle = carrier_map[c].needle
        if abs(needle-prev_needle) < self.MIN_FLOAT_LEN: return False
        else:
            warnings.warn(FloatWarning(c, prev_needle, needle))
            return True