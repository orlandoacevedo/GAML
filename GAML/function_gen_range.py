import random


def func_gen_range(rlist,percent=0.8):
    """filtering charge range

    For an integer 1D list, start from the mode number, find
    a surrounding range, which contains data points no less
    than certain percent

    For return value, the ndxmin is included in the range,
    while ndxmax is not

    Returns:
        int     :   lower-bound
        int     :   higher-bound
    """
    try:
        if not isinstance(rlist,list):
            raise ValueError
        else:
            for i in rlist:
                if not isinstance(i,int):
                    raise ValueError
        percent = float(percent)
        if percent <= 0 or percent > 1:
            raise ValueError
    except ValueError:
        raise ValueError('rlist: 1D integer list; percent: between 0 & 1')

    lth = len(rlist)
    rmax = max(rlist)
    ndxlist = []
    for i in range(lth):
        if rlist[i] == rmax:
            ndxlist.append(i)

    i = 1
    while i < len(ndxlist):
        if ndxlist[i] - ndxlist[i-1] == 1:
            ndxlist.remove(ndxlist[i-1])
        else:
            i += 1

    chooselist = []
    total_sum = sum(rlist)
    rsum = []
    for ndxmax in ndxlist:

        ndxmin = ndxmax

        while True:
            if rlist[ndxmin] < rlist[ndxmax]:
                if ndxmax + 1 < lth:
                    ndxmax = ndxmax + 1
                elif ndxmax == lth - 1:
                    if ndxmin - 1 > 0:
                        ndxmin = ndxmin - 1
                    else:
                        ndxmin = 0
                else:
                    ndxmax = lth - 1

            else:
                if ndxmin - 1 > 0 :
                    ndxmin = ndxmin - 1
                elif ndxmin == 0:
                    if ndxmax + 1 < lth:
                        ndxmax = ndxmax + 1
                    else:
                        ndxmax = lth - 1
                else:
                    ndxmin = 0

            lsum = sum(rlist[ndxmin:ndxmax+1])

            if lsum / total_sum >= percent:
                ltmp = []
                ltmp.append(ndxmin)
                ltmp.append(ndxmax+1)
                rsum.append(lsum)
                chooselist.append(ltmp)
                break

    if len(chooselist) >= 2:
        ndxlist = []
        for i in range(len(rsum)):
            if rsum[i] == max(rsum):
                ndxlist.append(i)

        choose = random.randrange(len(ndxlist))

        ndxmin = chooselist[choose][0]
        ndxmax = chooselist[choose][1]

    return ndxmin,ndxmax



