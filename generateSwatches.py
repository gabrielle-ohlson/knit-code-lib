import json

import knitout

k = knitout.Writer("1 2 3 4 5 6 7 8 9 10")
k.addHeader("Machine","swgn2")


import knitlib
from knitlib import jersey, rib, garter, altKnitTuck, tuckGarter, seed, tuckStitch # need these for globals()[pat]

from .helpers import c2cs


default_bed = "f"
default_stitchNumber = 63
default_speedNumber = 0

def generate(swatches, out_fp, main_c="1", waste_c="2", draw_c="3", sort_by_width=True):
    main_cs = c2cs(main_c)
    waste_cs = c2cs(waste_c)
    draw_cs = c2cs(draw_c)
    directions = {main_cs: "-", waste_cs: "-", draw_cs: "-"}
    left_n = 0

    pat_info = swatches.copy()

    for pat in pat_info:
        if len(pat) < 4: pat.append({})
        
        if (pat[1][0]-1) % pat[2] != 0: pat[1][0] += (pat[1][0]-1) % pat[2]

    if sort_by_width: pat_info = sorted(pat_info, key=lambda x: x[1][0]) #sort by right needle

    print(pat_info) #debug

    k.stitchNumber(default_stitchNumber)
    k.speedNumber(default_speedNumber)

    for i, (pat, dims, gauge, extensions) in enumerate(pat_info):
        if "tube" in pat:
            tube = True
            if gauge == 1 and not "jersey"in pat:
                print(f"(@ pat: {pat}) gauge must be 2 for non-jersey tubes, changing it.")
                gauge = 2
        else: tube = False

        comment = f"begin swatch:{' half-gauge' if gauge == 2 else ''} {pat} ({dims[0]}x{dims[1]})"

        pat = pat.replace("small", "").replace("large", "").strip() #get rid of these comments when calling as func

        if len(extensions): comment += " " + json.dumps(extensions)

        if i > 0 and gauge == 2:
            for n in range(left_n, right_n+1):
                if n % 2 != 0: k.xfer(f"f{n}", f"b{n}")

        if tube: pat = pat.replace("tube", "").strip()

        if pat == "tuck": pat = "altKnitTuck"

        if "_" in pat:
            if pat.startswith("jersey"):
                pat, bed = pat.split("_")
                sequence = None
            else:
                pat, sequence = pat.split("_")
                if tube:
                    seq = [sequence, ""]
                    for char in sequence:
                        seq[1] += "f" if char == "b" else "b"
                bed = default_bed
        else:
            sequence = None
            bed = default_bed

        if i == 0:
            right_n = dims[0]-1
            knitlib.altTuckCaston(k, right_n, left_n, waste_c, default_bed, gauge, inhook=True, releasehook=True)
        elif dims[0] > right_n:
            if directions[main_cs] == "+": k.miss("-", f"f{left_n}", main_c)
            else: k.miss("+", f"f{dims[0]}", main_c)
        elif not sort_by_width and dims[0] < right_n:
            knitlib.wasteSection(k, left_n, right_n, closed_aston=(not tube), waste_c=waste_c, draw_c=None, in_cs=[], gauge=gauge, end_on_right=end_on_right, initial=False, draw_middle=False, interlock_passes=10)
            knitlib.interlock(k, start_n=right_n, end_n=dims[0]+1, passes=1, c=waste_c, gauge=gauge) # position carrier by new right needle
            for n in range(dims[0]+1, right_n+1):
                k.drop(f"f{n}")
            for n in range(right_n, dims[0], -1):
                k.drop(f"b{n}")
        
        right_n = dims[0]-1

        rows = dims[1]

        if directions[main_cs] == "-":
            start_n = right_n
            end_n = left_n
        else:
            start_n = left_n
            end_n = right_n

        end_on_right = []

        if tube:
            if directions[draw_cs] == "-": end_on_right = [draw_c]
        else:
            if directions[draw_cs] == "+":
                end_on_right = [draw_c]
                directions[draw_cs] = "-"
            else: directions[draw_cs] = "+"


        knitlib.wasteSection(k, left_n, right_n, closed_caston=(not tube), waste_c=waste_c, draw_c=draw_c, in_cs=([draw_c] if i == 0 else []), gauge=gauge, end_on_right=end_on_right, initial=(i==0), draw_middle=False, interlock_passes=20)

        if not tube and bed == "b":
            for n in range(left_n, right_n+1):
                k.xfer(f"f{n}", f"b{n}")

        stitchPatFunc = globals()[pat]

        func_inhook = False
        if i == 0:
            if pat == "interlock": func_inhook = True
            else:
                k.inhook(main_c)
                if end_n > start_n: init_dir = "+"
                else: init_dir = "-"
                knitlib.tuckPattern(k, firstN=start_n, direction=init_dir, c=main_c)

        if tube:
            bn_locs = {
                "f": [n for n in range(left_n, right_n+1) if n % 2 == 0],
                "b": [n for n in range(left_n, right_n+1) if n % 2 != 0]
            }
            func_args_f = {
                "k": k,
                "start_n": start_n,
                "end_n": end_n,
                "passes": 1,
                "c": main_c,
                "bed": "f",
                "gauge": gauge,
                "inhook": func_inhook,  # we want to do this before adding the "begin swatch" flag #(i==0),
                "releasehook": (i==0)
            }

            func_args_b = {
                "k": k,
                "start_n": end_n,
                "end_n": start_n,
                "passes": 1,
                "c": main_c,
                "bed": "b",
                "gauge": gauge
            }

            if pat == "rib" or pat == "seed":
                func_args_f["bn_locs"] = bn_locs
                func_args_b["bn_locs"] = bn_locs

            k.comment(comment)

            if "stitchNumber" in extensions: k.stitchNumber(extensions["stitchNumber"])
            if "speedNumber" in extensions: k.speedNumber(extensions["speedNumber"])

            for r in range(rows):
                func_args = func_args_f.copy()
                
                if sequence is not None:
                    if "garter" in pat: func_args["sequence"] = sequence[r%len(sequence)]
                    else: func_args["sequence"] = seq[r%2]

                stitchPatFunc(**func_args) #main_c dir doesn"t change since circular

                func_args_f["inhook"], func_args_f["releasehook"] = False, False #ensure these are False after first row

                func_args = func_args_b.copy()
                if sequence is not None:
                    if "garter" in pat: func_args["sequence"] = sequence[r%len(sequence)]
                    else: func_args["sequence"] = seq[r%2]

                stitchPatFunc(**func_args) #main_c dir doesn"t change since circular
        else:
            func_args = {
                "k": k,
                "start_n": start_n,
                "end_n": end_n,
                "passes": rows,
                "c": main_c,
                "bed": bed,
                "gauge": gauge,
                "inhook": func_inhook,  # we want to do this before adding the "begin swatch" flag #(i==0),
                "releasehook": (i==0)
            }

            if sequence is not None: func_args["sequence"] = sequence

            if pat == "rib" or pat == "seed": func_args["bn_locs"] = {"f": list(range(left_n, right_n+1)), "b": []}

            k.comment(comment)

            if "stitchNumber" in extensions: k.stitchNumber(extensions["stitchNumber"])
            if "speedNumber" in extensions: k.speedNumber(extensions["speedNumber"])

            directions[main_cs] = stitchPatFunc(**func_args)

        assert directions[main_cs] == "-" or directions[main_cs] == "+" #debug

        k.stitchNumber(default_stitchNumber)
        k.speedNumber(default_speedNumber)

        if not tube and (pat == "rib" or "garter" in pat or bed == "b"): #transfer back to front bed for draw thread
            for n in range(left_n, right_n+1):
                k.xfer(f"b{n}", f"f{n}")

        if i < len(pat_info)-1: miss_draw = pat_info[i+1][1][0]
        else: miss_draw = None

        if tube:
            draw_c_final_d = ("+" if directions[draw_cs] == "-" else "-")
        else:
            draw_c_final_d = directions[draw_cs]
            directions[draw_cs] = ("+" if directions[draw_cs] == "-" else "-")
        knitlib.drawThread(k, left_n, right_n, draw_c, final_direction=draw_c_final_d, circular=tube, miss_draw=miss_draw, gauge=gauge)

        if i < len(pat_info)-1:
            if tube:
                knitlib.circular(k, start_n=left_n, end_n=right_n, passes=6, c=waste_c, gauge=gauge)
            else: knitlib.jersey(k, left_n, right_n, 6, waste_c, bed="f", gauge=gauge)

    if tube: back_needle_ranges=[left_n, right_n]
    else: back_needle_ranges=[]

    knitlib.dropFinish(k, front_needle_ranges=[left_n, right_n], back_needle_ranges=back_needle_ranges, carriers=[main_c, waste_c, draw_c], direction="+", borderC=waste_c, borderLength=20)

    k.write(out_fp)
