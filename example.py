import knitout
k = knitout.Writer("1 2 3 4 5 6 7 8 9 10")

from knitlib import altTuckCaston, dropFinish
from knitlib.stitchPatterns import jersey, rib, garter, seed

c = "1"
bed = "f"
left_n = 0
right_n = 30
gauge = 1 
pat_passes = 30


altTuckCaston(k, start_n=right_n, end_n=left_n, c=c, bed=bed, gauge=gauge, inhook=True, releasehook=True, tuck_pattern=True)

jersey(k, start_n=right_n, end_n=left_n, passes=pat_passes, c=c, bed=bed, gauge=gauge)

rib(k, start_n=right_n, end_n=left_n, passes=pat_passes, c=c, bed=bed, sequence="ffb", gauge=gauge)

garter(k, start_n=right_n, end_n=left_n, passes=pat_passes, c=c, bed=bed, sequence="fbffbb", gauge=gauge)

seed(k, start_n=right_n, end_n=left_n, passes=pat_passes, c=c, bed=bed, sequence="fb", gauge=gauge)

dropFinish(k, front_needle_ranges=[left_n, right_n], out_carriers=[c], direction="-", machine="swgn2")

k.write("example.k")