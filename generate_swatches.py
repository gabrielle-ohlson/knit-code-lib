import json

import knitout

k = knitout.Writer('1 2 3 4 5 6 7 8 9 10')
k.addHeader('Machine','swgn2')

import lib
from lib import jersey, rib, garter, altKnitTuck, tuckGarter, seed, tuckStitch # need these for globals()[pat]

mainC = '1'
wasteC = '2'
drawC = '3'

default_bed = 'f'
default_stitchNumber = 63
default_speedNumber = 0

def generate(swatches, out_fp, sort_by_width=True):
    mainC_dir = '-'
    drawC_dir = '-'
    leftN = 0

    pat_info = swatches.copy()

    for pat in pat_info:
        if len(pat) < 4: pat.append({})
        
        if (pat[1][0]-1) % pat[2] != 0: pat[1][0] += (pat[1][0]-1) % pat[2]

    if sort_by_width: pat_info = sorted(pat_info, key=lambda x: x[1][0]) #sort by right needle

    print(pat_info) #debug

    k.stitchNumber(default_stitchNumber)
    k.speedNumber(default_speedNumber)

    for i, (pat, dims, gauge, extensions) in enumerate(pat_info):
        if 'tube' in pat:
            tube = True
            if gauge == 1 and not 'jersey'in pat:
                print(f"(@ pat: {pat}) gauge must be 2 for non-jersey tubes, changing it.")
                gauge = 2
        else: tube = False

        comment = f'begin swatch:{" half-gauge" if gauge == 2 else ""} {pat} ({dims[0]}x{dims[1]})'

        pat = pat.replace('small', '').replace('large', '').strip() #get rid of these comments when calling as func

        if len(extensions): comment += ' ' + json.dumps(extensions)

        if i > 0 and gauge == 2:
            for n in range(leftN, rightN+1):
                if n % 2 != 0: k.xfer(f'f{n}', f'b{n}')

        if tube: pat = pat.replace('tube', '').strip()

        if pat == 'tuck': pat = 'altKnitTuck'

        if '_' in pat:
            if pat.startswith('jersey'):
                pat, bed = pat.split('_')
                sequence = None
            else:
                pat, sequence = pat.split('_')
                if tube:
                    seq = [sequence, '']
                    for char in sequence:
                        seq[1] += 'f' if char == 'b' else 'b'
                bed = default_bed
        else:
            sequence = None
            bed = default_bed

        if i == 0:
            rightN = dims[0]-1
            lib.altTuckCaston(k, rightN, leftN, wasteC, default_bed, gauge, inhook=True, releasehook=True)
        elif dims[0] > rightN:
            if mainC_dir == '+': k.miss('-', f'f{leftN}', mainC)
            else: k.miss('+', f'f{dims[0]}', mainC)
        elif not sort_by_width and dims[0] < rightN:
            lib.wasteSection(k, leftN, rightN, closedCaston=(not tube), wasteC=wasteC, drawC=None, inCs=[], gauge=gauge, endOnRight=endOnRight, initial=False, drawMiddle=False, interlockLength=10)
            lib.interlock(k, startN=rightN, endN=dims[0]+1, length=1, c=wasteC, gauge=gauge) # position carrier by new right needle
            for n in range(dims[0]+1, rightN+1):
                k.drop(f'f{n}')
            for n in range(rightN, dims[0], -1):
                k.drop(f'b{n}')
        
        rightN = dims[0]-1

        rows = dims[1]

        if mainC_dir == '-':
            startN = rightN
            endN = leftN
        else:
            startN = leftN
            endN = rightN

        endOnRight = []

        if tube:
            if drawC_dir == '-': endOnRight = [drawC]
        else:
            if drawC_dir == '+':
                endOnRight = [drawC]
                drawC_dir = '-'
            else: drawC_dir = '+'


        lib.wasteSection(k, leftN, rightN, closedCaston=(not tube), wasteC=wasteC, drawC=drawC, inCs=([drawC] if i == 0 else []), gauge=gauge, endOnRight=endOnRight, initial=(i==0), drawMiddle=False, interlockLength=20)

        if not tube and bed == 'b':
            for n in range(leftN, rightN+1):
                k.xfer(f'f{n}', f'b{n}')

        stitchPatFunc = globals()[pat]

        func_inhook = False
        if i == 0:
            if pat == 'interlock': func_inhook = True
            else:
                k.inhook(mainC)
                if endN > startN: init_dir = '+'
                else: init_dir = '-'
                lib.tuckPattern(k, firstN=startN, direction=init_dir, c=mainC)

        if tube:
            bedLoops = {
                'f': [n for n in range(leftN, rightN+1) if n % 2 == 0],
                'b': [n for n in range(leftN, rightN+1) if n % 2 != 0]
            }
            func_args_f = {
                'k': k,
                'startN': startN,
                'endN': endN,
                'length': 1,
                'c': mainC,
                'bed': 'f',
                'gauge': gauge,
                'inhook': func_inhook,  # we want to do this before adding the 'begin swatch' flag #(i==0),
                'releasehook': (i==0)
            }

            func_args_b = {
                'k': k,
                'startN': endN,
                'endN': startN,
                'length': 1,
                'c': mainC,
                'bed': 'b',
                'gauge': gauge
            }

            if pat == 'rib' or pat == 'seed':
                func_args_f['bedLoops'] = bedLoops
                func_args_b['bedLoops'] = bedLoops

            k.comment(comment)

            if 'stitchNumber' in extensions: k.stitchNumber(extensions['stitchNumber'])
            if 'speedNumber' in extensions: k.speedNumber(extensions['speedNumber'])

            for r in range(rows):
                func_args = func_args_f.copy()
                
                if sequence is not None:
                    if 'garter' in pat: func_args['sequence'] = sequence[r%len(sequence)]
                    else: func_args['sequence'] = seq[r%2]

                stitchPatFunc(**func_args) #mainC dir doesn't change since circular

                func_args_f['inhook'], func_args_f['releasehook'] = False, False #ensure these are False after first row

                func_args = func_args_b.copy()
                if sequence is not None:
                    if 'garter' in pat: func_args['sequence'] = sequence[r%len(sequence)]
                    else: func_args['sequence'] = seq[r%2]

                stitchPatFunc(**func_args) #mainC dir doesn't change since circular
        else:
            func_args = {
                'k': k,
                'startN': startN,
                'endN': endN,
                'length': rows,
                'c': mainC,
                'bed': bed,
                'gauge': gauge,
                'inhook': func_inhook,  # we want to do this before adding the 'begin swatch' flag #(i==0),
                'releasehook': (i==0)
            }

            if sequence is not None: func_args['sequence'] = sequence

            if pat == 'rib' or pat == 'seed': func_args['bedLoops'] = {'f': list(range(leftN, rightN+1)), 'b': []}

            k.comment(comment)

            if 'stitchNumber' in extensions: k.stitchNumber(extensions['stitchNumber'])
            if 'speedNumber' in extensions: k.speedNumber(extensions['speedNumber'])

            mainC_dir = stitchPatFunc(**func_args)

        assert mainC_dir == '-' or mainC_dir == '+' #debug

        k.stitchNumber(default_stitchNumber)
        k.speedNumber(default_speedNumber)

        if not tube and (pat == 'rib' or 'garter' in pat or bed == 'b'): #transfer back to front bed for draw thread
            for n in range(leftN, rightN+1):
                k.xfer(f'b{n}', f'f{n}')

        if i < len(pat_info)-1: missDraw = pat_info[i+1][1][0]
        else: missDraw = None

        if tube:
            drawC_finalDir = ('+' if drawC_dir == '-' else '-')
        else:
            drawC_finalDir = drawC_dir
            drawC_dir = ('+' if drawC_dir == '-' else '-')
        lib.drawThread(k, leftN, rightN, drawC, finalDir=drawC_finalDir, circular=tube, missDraw=missDraw, gauge=gauge)

        if i < len(pat_info)-1:
            if tube:
                lib.circular(k, startN=leftN, endN=rightN, length=6, c=wasteC, gauge=gauge)
            else: lib.jersey(k, leftN, rightN, 6, wasteC, bed='f', gauge=gauge)

    if tube: backNeedleRanges=[leftN, rightN]
    else: backNeedleRanges=[]

    lib.dropFinish(k, frontNeedleRanges=[leftN, rightN], backNeedleRanges=backNeedleRanges, carriers=[mainC, wasteC, drawC], direction='+', borderC=wasteC, borderLength=20)

    k.write(out_fp)
