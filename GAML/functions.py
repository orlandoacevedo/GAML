import os


def file_size_check(path,fsize=10):
    """check file existence & size"""
    if not os.path.isfile(path):
        print(path)
        raise FileNotFoundError('File not found')
    sizetmp = os.stat(path).st_size
    if sizetmp/1024/1024 > fsize:
        raise ValueError('File size is too big, try to increase its limits')



def file_gen_new(fname,fextend='txt',foriginal=True,bool_dot=True):
    """Generate new file name without overwritings

    Args:
        fname   (str)   :   input file fname
        fextend (str)   :   file extension
        foriginal (bool):   whether keep original
        bool_dot (bool) :   force check dot convention or not
    
    Returns:
        str     :   new file name
    """
    filename = fname
    pos = filename.rfind('.')
    if bool_dot and pos != -1:
        fname = filename[:pos]
        fextend = filename[pos:]
    else:
        fextend = '.' + fextend

    if foriginal is True:
        try:
            f = open(fname + fextend)
            f.close()
        except:
            return fname + fextend

    i = 1
    filename = fname
    while True:
        fname = filename + '-' + str(i) + fextend
        if not os.path.isfile(fname): break
        i += 1
    return fname



def func_file_input(filepath,
                    comment_char='#',
                    dtype=float,
                    bool_tail=True,
                    in_keyword='PAIR',
                    cut_keyword='MAE',
                    bool_force_cut_kw=False,
                    ignore_kw='HEAD'):
    """Read input file
    
    Args:
        filepath    (str)   :   file path
        comment_char (str)  :   char used as comments when reading
        dtype       (type)  :   convert data type
        bool_tail   (bool)  :   whether append tail or not
        in_keyword (str)    :   read leading words
        cut_keyword (str)   :   read triming words
        bool_force_cut_kw(bool) :   whether force trim words exist
        ignore_kw   (str)   :   ignore keyword when reading

    Returns:
        List[List]  :   reading data
    """
    profile = []
    with open(filepath,mode='rt') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                break

            line = line.strip()
            if len(line) == 0 or line[0] == comment_char:
                continue
            
            bo = False
            lp = line.split()
            if len(lp) >= 2 and lp[0] == in_keyword:
                if bool_force_cut_kw and line.find(cut_keyword) == -1:
                    print('Error: in line: ' + line)
                    raise KeyError('cut_keyword is not found')
                ls = []
                try:
                    for tmp in lp[1:]:
                        if tmp != cut_keyword:
                            ls.append(dtype(tmp))
                        else:
                            if bool_tail is True:
                                t = lp.index(tmp) + 1
                                if len(lp) <= t:
                                    ls.append('nan')
                                else:
                                    ls.append(dtype(lp[lp.index(tmp)+1]))
                            break
                    profile.append(ls)
                except ValueError:
                    print('Error: in line: ' + line)
                    raise ValueError('cannot convert')
            elif len(lp) >= 2 and lp[0] == ignore_kw:
                pass
            else:
                print('Error: in line: ' + line)
                raise ValueError('Not correctly defined')

    return profile



def func_roundoff_error(v,vnm,s,snm,n=10,nmround=2):
    """process the round-off-error"""

    def pro_rounderror(v,vnm,s,snm,n,nmround):
        step = 1 / 10**nmround
        cnt = 0
        bool_overload = True
        while True:
            cnt += 1
            ds = s*snm + v*vnm
            if round(ds,nmround + 3) == 0:
                break
            else:
                # here has a trick, no matter s is bigger
                #   or less than zero, the same ds condition
                #   will be got
                # Caution! The zero equivalence should be avoided
                if ds > 0:
                    s = s - step
                    if s == 0:
                        s = s - step
                else:
                    s = s + step
                    if s == 0:
                        s = s + step

            s = round(s,nmround)
            # in case of any overloaded
            if cnt >= n:
                bool_overload = False
                break
        return bool_overload,v,vnm,s,snm

    v = round(v,nmround)
    s = round(s,nmround)

    # take care of zero inputs
    if v == 0:
        v = 1 / 10**nmround

    bo,v,vnm,s,snm = pro_rounderror(v,vnm,s,snm,n,nmround)

    if bo:
        return bo,v,vnm,s,snm
    else:
        bo,s,snm,v,vnm = pro_rounderror(s,snm,v,vnm,n,nmround)
        return bo,v,vnm,s,snm



def func_pro_pn_limit(string,bool_repeats=True):
    """process pn_limit
    
    Raw input should be a string

    1) '1,p, 2, p, 3:P, 4 - Positive, 5 :N, 6- negative, 7, 8, 9  n'
    2) '1p, 2  3, p  4,  - , p, 5 ,6n, 7  8 ,, 9 n'
    3) '1,2,3,4p,  5,6,7,8,9n'
    4) '1-p, 2:p, 3-p, 4p, 5n, 6n, 7-n, 8n, 9n'
    5) '1:p, 2-p, 3p, 4p, 5:n, 6n, 7n, 8-n, 9n'
    6) '1p, 2p, 3p, 4p, 5n, 6n, 7n, 8n, 9n'

    The number of space or tab doesn't matter.
    All of those six inputs are equivalent.

    The comma is chosen as the delimiter, the key word 'p' and 'n'
    represent 'positive' and 'negative' respectively, both its
    initial and full word are OK, they are case-insensitive.

    the bool_repeats are used to define the double-definition
    can be accepted or not for the same entry.

    Note:
        the return value is not sequence based
    """
    line = string.replace(',',' ').replace(':',' ').replace('-',' ').lower()
    line = line.replace('ositive',' ').replace('egative',' ')

    subline = line.replace(' ','')
    try:
        dump_value = int(subline.replace('p','').replace('n',''))
        # The first character in subline can't be 'n' or 'p',
        # 'pn' or 'np' should not exist, and the last char has
        # to be either 'n' or 'p'
        if subline[0] == 'p' or subline[0] == 'n' or \
           'pn' in subline or 'np' in subline or \
           (subline[-1] != 'n' and subline[-1] != 'p'):
            raise ValueError
    except ValueError:
        print(string)
        raise ValueError('Wrong defined')

    nl = pl = ''
    i = 0
    j = 0
    while i < len(line):
        if line[i] == 'p':
            if j < i:
                pl += line[j:i]
            j = i + 1
        elif line[i] == 'n':
            if j < i:
                nl += line[j:i]
            j = i + 1
        i += 1

    nvlist = []
    for i in nl.split():
        nvlist.append([int(i),'n'])
    for i in pl.split():
        nvlist.append([int(i),'p'])

    if not bool_repeats:
        t = [i[0] for i in nvlist]
        if len(t) != len(set(t)):
            print(string)
            raise ValueError('Wrong defined')

    return nvlist



