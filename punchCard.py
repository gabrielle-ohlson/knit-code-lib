import cv2
# import matplotlib.pyplot as plt

from .helpers import c2cs, toggleDirection, tuckPattern, flattenIter

TUCK = 0
FAIRISLE = 1
SLIP = 2

def generate(k, start_n, end_n, passes, c, bed, img_path, punch_card_dims=None, setting=TUCK, c2=None, color_change_mod=None, inhook_carriers=[], outhook_carriers=[]):
    '''
    Function to emulate a punch card for a domestic knitting machine on an industrial machine (programmed with knitout) using a binary (black and white) image.

    Parameters:
    ----------
    * `k` (class instance): instance of the knitout Writer class.
    * `start_n` (int): the initial needle to knit on in a pass.
    * `end_n` (int): the last needle to knit on in a pass (inclusive).
    * `passes` (int): total number of passes to knit (NOTE: there are two passes per row in interlock).
    * `c` (str or list): the carrier to use for the cast-on (or list of carriers, if plating).
    * `bed` (str, optional): the bed to knit on. Valid values are `f` or `b`.
    * `img_path` (str): path to punch card image.
    * `punch_card_dims` (tuple or None, optional): dimensions of punch card in (w, h). Defaults to `None`.
    * `setting` (int, optional): program constant specifying the setting to use for "punched out" sections (white pixels). Defaults to `FAIRISLE`.
    * `c2` (str or list, optional): a second carrier (or list of carriers, if plating) to use for color-work (NOTE: required if `setting == FAIRISLE or color_change_mod is not None`). Defaults to `None`.
    * `color_change_mod` (int or None, optional): indicates: "change carriers every `color_change_mod` passes". Defaults to `None`.
    * `inhook_carriers` (list, optional): carriers to `inhook` before using for the first time (NOTE: will automatically add `tuckPattern` and releasehook too). Defaults to `[]`.
    * `outhook_carriers` (list, optional): carriers to `outhook` at the end of the function. Defaults to `[]`.
    '''
    directions = {}
    #
    if end_n > start_n: # starts pos
        d1, d2 = "+", "-"
        left_n, right_n = start_n, end_n
        step = 1
    else:
        d1, d2 = "-", "+"
        left_n, right_n = end_n, start_n
        step = -1
    #
    cs = c2cs(c)
    #
    if c in inhook_carriers: directions[cs] = None
    else: directions[cs] = d1
    #
    if c2 is not None:
        cs2 = c2cs(c2)
        if c2 in inhook_carriers: directions[cs2] = None
        else: directions[cs2] = d1
    else:
        cs2 = None
        if setting == FAIRISLE: raise ValueError("Must pass an argument to 'c2' param for fairisle setting.")
        elif color_change_mod is not None: raise ValueError("Must pass an argument to 'c2' param for color changing.")
    
    if setting != TUCK and setting != FAIRISLE and setting != SLIP: raise ValueError(f"Unsupported setting: {setting}.  Supported settings are {TUCK} (tuck), {FAIRISLE} (fairisle), and {SLIP} (slip).")
    #get punch card data
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    #
    if punch_card_dims is not None: img = cv2.resize(img, punch_card_dims, interpolation=cv2.INTER_AREA)
    #
    ret, data = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    # flip vertically so going from bottom up
    data = cv2.flip(data, 0)
    h, w = data.shape
    # #remove #debug #v
    # print(data)
    # plt.imshow(data)
    # plt.show()
    # #^
    do_releasehook = False
    #
    for p in range(passes):
        if color_change_mod is not None and p % color_change_mod == (color_change_mod-1): cs, cs2 = cs2, cs
        row = data[p%h] #TODO: #check
        #
        if directions[cs] is None: #inhook
            k.inhook(*cs)
            tuckPattern(k, first_n=left_n if d1 == "+" else right_n, direction=d1, c=cs)
            directions[cs] = d1
            do_releasehook = True
        #
        if directions[cs] == "+":
            for i in row:
                n = i+left_n
                if i == 0: k.knit(directions[cs], f"{bed}{n}", *cs)
                else:
                    if setting == TUCK: k.tuck(directions[cs], f"{bed}{n}", *cs)
                    elif setting == SLIP: k.miss(directions[cs], f"{bed}{n}", *cs)
        else:
            for i in reversed(row):
                n = i+left_n
                if i == 0: k.knit(directions[cs], f"{bed}{n}", *cs)
                else:
                    if setting == TUCK: k.tuck(directions[cs], f"{bed}{n}", *cs)
                    elif setting == SLIP: k.miss(directions[cs], f"{bed}{n}", *cs)
        #
        if do_releasehook:
            tuckPattern(k, first_n=left_n if d1 == "+" else right_n, direction=d1, c=None) #drop it
            k.releasehook(*cs)
            do_releasehook = False
        #
        directions[cs] = toggleDirection(directions[cs])
        #
        if setting == FAIRISLE:
            if directions[cs2] is None: #inhook
                k.inhook(*cs2)
                tuckPattern(k, first_n=left_n if d1 == "+" else right_n, direction=d1, c=cs2)
                directions[cs2] = d1
                do_releasehook = True
            #
            if directions[cs2] == "+":
                for i in row:
                    n = i+left_n
                    if i != 0: k.knit(directions[cs2], f"{bed}{n}", *cs2)
            else:
                for i in reversed(row):
                    n = i+left_n
                    if i != 0: k.knit(directions[cs2], f"{bed}{n}", *cs2)
            #
            if do_releasehook:
                tuckPattern(k, first_n=left_n if d1 == "+" else right_n, direction=d1, c=None) #drop it
                k.releasehook(*cs2)
                do_releasehook = False
            #
            directions[cs2] = toggleDirection(directions[cs2])
    #
    for carrier in flattenIter(outhook_carriers):
        k.outhook(carrier)
