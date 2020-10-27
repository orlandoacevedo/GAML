"""Parse input file

Contents in `key=value` format.

Any existing key without value defined will be set to None

return:
    log `dict`:
        it contains two keys 'nice' & 'info'
        `log['nice'] == False` means error happens
        please check it use `log['info']`

    profile `list`:
        commands exist, return `3D list`:
            [ [[key,value,info],[key,value,info]], ...]

        otherwise, return empty 1D list
"""


def parsefile(settingfile):
    """Parse the input settingfile"""

    def func_remove_comments(string):
        if string.find('#') != -1:
            string = string[:string.find('#')]
        return string.strip()

    log = {'nice': True,'info':''}
    # this universal string is used to exit prompt
    error_info = 'Error: the input setting file is wrong'

    infile = []
    with open(settingfile,mode='rt') as f:
        nm = 0
        while True:
            line = f.readline()
            nm += 1
            if len(line) == 0:
                break

            line = line.strip()
            if len(line) == 0 or line[0] == '#': continue
            info = str(nm) + ': ' + line

            # help append `='
            if line.find('=') == -1: line += ' ='

            lp = line.split('=',maxsplit=1)

            if len(lp[0].split()) != 1:
                log['nice'] = False
                log['info'] = 'Error: ' + info
                break
            key = lp[0].strip().lower().replace('-','_')

            # take care of 'basis_set' comment exception
            if key == 'basis_set':
                ndx_first = lp[1].find('#')
                if ndx_first == -1:
                    strtmp = ''
                    for i in lp[1].split(): strtmp += i + ' '
                    value = strtmp.strip()
                elif ndx_first == len(lp[1]):
                    # only `#' exist
                    value = '#'
                else:
                    ndx_second = lp[1][ndx_first+1:].find('#')
                    if ndx_second == -1:
                        strtmp = ''
                        for i in lp[1].split(): strtmp += i + ' '
                        value = strtmp.strip()
                    else:
                        strtmp = ''
                        for i in lp[1][:ndx_first+ndx_second+1].split():
                            strtmp += i + ' '
                        value = strtmp.strip()
            else:
                value = func_remove_comments(lp[1])
                # take care of special cases
                if key == 'atomtype_list':
                    value = value.replace('"',' ').replace("'",' ')
                    value = value.replace(';',' ').replace(',',' ').strip()
                    if len(value) != 0 and value[0] == '[':
                        value = value[1:].strip()
                    if len(value) != 0 and value[-1] == ']':
                        value = value[:len(value)-1].strip()
                    if len(value) == 0:
                        value = None
                    else:
                        value = value.split()
                elif key in ['symmetry_list','counter_list','offset_list']:
                    if len(value) == 0:
                        value = None
                    else:
                        if value[0] != '[': value = '[' + value
                        if value[-1] != ']': value = value + ']'
                        try:
                            value = eval(value)
                        except:
                            log['nice'] = False
                            log['info'] = 'Error: ' + info
                            break
                elif key == 'charge_spin':
                    lr = value.split()
                    if len(lr) == 0:
                        value = '0 1'
                    elif len(lr) == 2:
                        value = lr[0] + ' ' + lr[1]
                    else:
                        log['nice'] = False
                        log['info'] = 'Error: ' + info
                        break
                else:
                    if len(value) == 0:
                        value = None
                    elif len(value.split()) != 1:
                        log['nice'] = False
                        log['info'] = 'Error: ' + info
                        break
            infile.append([key,value,info])
    if not log['nice']: return log, []

    # process infile to different blocks
    i = 0
    profile = []
    while i < len(infile):
        ls = []
        if infile[i][0] == 'command':
            ls.append(infile[i])
            j = i + 1
            while j < len(infile) and infile[j][0] != 'command':
                ls.append(infile[j])
                j += 1
            profile.append(ls)
            i = j
        else:
            i += 1

    if len(profile) == 0:
        log['nice'] = False
        log['info'] = 'Error: no command is found'
        return log, []

    return log, profile


