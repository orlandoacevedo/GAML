def file_size_check(path,fsize=10):
    """This function is used to check the file existence and size,
       the unit of size is in megabety"""
    
    import os      
    try:
        sizetmp = os.stat(path).st_size
        if sizetmp/1024/1024 > fsize:
            print('Error: the file size is far larger than %f MB' % fsize)
            print('Error path: ',path)
            exit()
          
    except IOError:
        print('Error : cannot open the file!')
        print('Error path: ',path)
        exit()
        
    return 1



def file_gen_new(fname,fextend='txt',foriginal=True,bool_dot=True):
    """This function is used to make new file but without overriding the
       old one. By default, the "string" after the dot-notation in the
       input file name is used as the final file extension, which means
       it will override the parameter in 'fextend', this behavior can be
       turned off by set 'bool_dot' to False. The parameter 'foriginal'
       is used to set filename be counted or not"""
    
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
        fname = filename + '_' + str(i) + fextend
        try:
            f = open(fname)
            f.close()
        except:
            break
        i += 1
    return fname



def function_file_input(filepath,comment_char='#',dtype=float,bool_tail=True,in_keyword='PAIR',
                        cut_keyword='MAE',bool_force_cut_kw=False):
    """get the input file, check if forcing the cut_kw or not"""
    
    profile = []
    with open(filepath,mode='rt') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            else:
                lp = line[:line.find(comment_char)].split()
                if len(lp) == 0:
                    continue
                elif len(lp) >= 2 and lp[0] == in_keyword:
                    
                    if bool_force_cut_kw and line.find(cut_keyword) == -1:
                        print('Error: no cut_keyword was found')
                        exit()
                            
                    ls = []
                    for tmp in lp[1:]:
                        if tmp != cut_keyword:
                            ls.append(dtype(tmp))
                        else:
                            if bool_tail is True:
                                ls.append(dtype(lp[lp.index(tmp)+1]))
                            break
                    profile.append(ls)
                    
                else:
                    print('Error: The input file format is not correctly defined')
                    print('Error line:')
                    print(line)
                    exit()
                
    return profile



def function_roundoff_error(v,vnm,s,snm,n=10,nmround=2):
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



def function_pro_bool_limit(string,bool_repeats=True):
    """This method is used to process the parameter bool_limit, the raw input is
       a string, its correct formats are;

       1) '1,p, 2, p, 3:P, 4 - Positive, 5 :N, 6- negative, 7,  8, 9   n'
       2) '1p, 2  3, p  4,  - , p, 5 ,6n, 7  8 ,, 9 n'
       3) '1,2,3,4p,  5,6,7,8,9n'
       4) '1-p, 2:p, 3-p, 4p, 5n, 6n, 7-n, 8n, 9n'
       5) '1:p, 2-p, 3p, 4p, 5:n, 6n, 7n, 8-n, 9n'
       6) '1p, 2p, 3p, 4p, 5n, 6n, 7n, 8n, 9n'
    
       The number of space or tab doesn't matter.
       All of those six inputs are equivalent.
       
       The comma is chosen as the delimiter, the key word 'p' and 'n' represent
       'positive' and 'negative' respectively, both its initial and full word
       are OK, they are case-insensitive.

       the bool_repeats are used to define the double-definition can be accepted
       or not for the same entry.

       Note:
       1) the return value is not sequence based,
       2) if any errors happen, the full process is terminated."""
    
    error_info = 'Error: the parameter bool_limit is not correctly defined'
        
    ltmp = string.lower().split()

    line = ''
    for i in ltmp:
        line += i + ','
    sline = ''
    for i in line:
        sline = sline + '-' if i == ':' else sline + i
        
    ltmp = sline.split(',')

    line = ''
    for i in ltmp:   
        if i.find('-') != -1:
            if len(i) == 1 or i[0] == '-':
                if len(line) > 1 and line[-1] == ',':
                    line = line[:-1] + i
                else:          
                    line += i
            else:
                line += i
                
            if len(i) > 1 and i[-1] != '-':
                line += ','
        elif len(i) != 0:
            line += i + ','
            
    ltmp = line.split(',')

    nvlist = []
    reflist = []
    count = 0        
    for i in ltmp:
        try:
            t = i.split('-')
            bool_ndx = False
            if len(t) == 2:
                # check the left-side and the right-side
                n = int(t[0])
                if t[1] not in ['p','positive','n','negative']:
                    raise ValueError

                value = 'p' if ( t[1] in ['p','positive'] ) else 'n'                
                nvlist.append([n,value])

                if count != 0:
                    if ltmp[count-1].find('-') == -1 and \
                       ltmp[count-1].find('p') == -1 and \
                       ltmp[count-1].find('positive') == -1 and \
                       ltmp[count-1].find('n') == -1 and \
                       ltmp[count-1].find('negative') == -1:
                        bool_ndx = True
                        raise ValueError
                
            elif i.find('p') != -1 or i.find('positive') != -1:
                t = i.split('p')
                if len(t[0]) != 0:
                    n = int(t[0])
                    reflist.append(n)
                if len(t[1]) != 0 and t[1] != 'ositive':
                    raise ValueError
                reflist.append('p')
                
            elif i.find('n') != -1 or i.find('negative') != -1:
                t = i.split('n')
                if len(t[0]) != 0:
                    n = int(t[0])
                    reflist.append(n)
                if len(t[1]) != 0 and t[1] != 'egative':
                    raise ValueError
                reflist.append('n')
                
            elif len(i) != 0:
                reflist.append(int(i))
            count += 1
        except:
            print(error_info)
            print('Input string: ',string)
            if bool_ndx:
                print('Error entry: ',ltmp[count-1],i)
            else:
                print('Error entry: ',i)
            exit()

    if len(reflist) == 0:
        return nvlist

    try:
        if reflist[-1] != 'p' and reflist[-1] != 'n':
            i = reflist[-1]
            raise ValueError
    except:
        print(error_info)
        print('Input string: ',string)
        print('Error entry: ',i)
        exit()

    
    j = 0
    while j < len(reflist):
        ls = []
        count = 0
        for n in reflist[j:]:
            count += 1
            if n == 'n' or n == 'p':
                break
            ls.append(n)
            
        for k in ls:
            nvlist.append([k,n])
        j += count

    if not bool_repeats:
        t = [i[0] for i in nvlist]
        if len(t) != len(set(t)):
            print(error_info)
            print(string)
            print('Error: some entries are double defined!')
            exit()

    return nvlist

