#!/usr/bin/env python3

# version 0.10 : start
# version 0.20 : add threshold_small
# version 0.30 : add prompt to remove repeats
# version 0.31 : more clear on threshold error
# version 0.32 : echo more info when processing
# version 0.33 : add more echoing

import os


# chargepair file to be checked
chkfile = ''

# charge threshold
threshold = 0.8

# lowerest value
threshold_small = 0.03

# summary MAE file
maefile = ''



#
# END of user inputs
#


if os.path.isfile(chkfile):
    print('Note: charge pair file : < {:} >'.format(chkfile))
    bool_chkfile = True
else:
    print('Warning: Check File is not found, setting to False')
    bool_chkfile = False

if os.path.isfile(maefile):
    print('Note: charge pair file : < {:} >'.format(maefile))
    bool_maefile = True
else:
    print('Warning: MAE File is not found, setting to False')
    bool_maefile = False



def fprocess(file):
    profile = []
    with open(file,'rt') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            sub = line if line.find('#') == -1 else line[:line['#']]
            sub = sub.strip()
            if len(sub) == 0: continue

            ltmp = sub.split()
            if ltmp[0] == 'PAIR':
                ls = []
                for i in ltmp[1:]:
                    if i.lower() != 'mae':
                        ls.append(float(i))
                    else:
                        break
                profile.append(ls)
            else:
                print('Error line')
                print(line)
                exit()
    return profile



if bool_chkfile:
    print('For CHKFILE checking...')
    rmlist = []
    profile = fprocess(chkfile)
    # NEW self-check
    i = 1
    while i < len(profile):
        j = 0
        while j < i:
            p = profile[i]
            t = profile[j]
            bo = True
            for k in range(len(p)):
                if p[k] - t[k] > 0.0001:
                    bo = False
                    break
            if bo:
                rmlist.append(p)
                print('Failed on NEW self-check:',p)
                break
            j += 1
        i += 1

    for p in profile:
        for i in p:
            if abs(i) > threshold or abs(i) < threshold_small:
                rmlist.append(p)
                if abs(i) > threshold:
                    print('threshold Error < big >:         ',p)
                else:
                    print('threshold Error <small>:         ',p)
                break



if bool_maefile:
    print('For MAEFILE checking...')
    totfile = fprocess(maefile)
    # TOT self-check
    i = 1
    while i < len(totfile):
        j = 0
        while j < i:
            p = totfile[i]
            t = totfile[j]
            bo = True
            for k in range(len(p)):
                if p[k] - t[k] > 0.0001:
                    bo = False
                    break
            if bo:
                print('Failed on TOT self-check:',p)
                break
            j += 1
        i += 1


if bool_chkfile and bool_maefile:
    print('For compare FILE checking...')
    # compare-check
    for p in profile:
        for t in totfile:
            bo = True
            for k in range(len(p)):
                if p[k] - t[k] > 0.0001:
                    bo = False
                    break
            if bo:
                rmlist.append(p)
                print('Failed on compare-check: ',p)
                break

# cleanup rmlist
if bool_chkfile:
    if len(rmlist) <= 1:
        rmchklist = rmlist
    else:
        i = 1
        rmchklist = [rmlist[0],]
        while i < len(rmlist):
            j = 0
            while j < i:
                p = rmlist[i]
                t = rmlist[j]
                bo = True
                for k in range(len(p)):
                    if p[k] - t[k] > 0.0001:
                        bo = False
                        break
                if not bo:
                    rmchklist.append(p)
                    break
                j += 1
            i += 1



if bool_chkfile:
    pnm = len(profile)
    print('\nDONE everything for < ',chkfile, ' >')
    print('In total, < ', pnm,' > PAIRs\n')

    if len(rmchklist) != 0:
        print('Found < {:} > problematic entries in chkfile < {:} >'.format(len(rmchklist),chkfile))
        print('Do you want to remove this from chkfile? y/yes, else not')
        t = input()
        if t.lower() in ['y','yes']:
            with open(chkfile,'r') as f:
                infile = f.readlines()

            with open(chkfile,'w') as f:
                for line in infile:
                    ltmp = line.split()
                    if len(ltmp) >= 2 and ltmp[0] == 'PAIR':

                        bo = True
                        for ref in rmchklist:
                            i = 1
                            bo = True
                            while i < len(ref):
                                # extremely care on index number i
                                # ltmp starts from        "PAIR  nm  nm  nm  nm"
                                # However ref starts from " nm   nm  nm  nm"
                                if float(ltmp[i]) - ref[i-1] > 0.0001:
                                    bo = False
                                    break
                                i += 1
                            if bo:
                                break

                        if not bo:
                            f.write(line)
                    else:
                        f.write(line)
            print('DONE chkfile removing')
            pnm = len(profile) - len(rmchklist)

    print('\nDONE everything for < ',chkfile, ' >')
    print('In total, < ', pnm ,' > PAIRs\n')

print('DONE everything')


