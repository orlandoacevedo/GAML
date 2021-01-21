from GAML.functions import file_gen_new, file_size_check, func_file_input


class File_gen_gromacstop(object):
    """Generate GROMACS topology file based on given charge_path file

    Args:
        charge_path (str | list): charge list, required
        symmetry_list (str|list): corresponding symmetry_list
        toppath     (str)       : reference topology file, required
        in_keyword  (str)       : read leading word
        cut_keyword (str)       : read triming char
        reschoose   (str)       : choose reside
        gennm       (str | list): number of generations
        fname       (str)       : output file names

    Returns:
        None    :   topology files

    Note:
        If symmetry_list does not exist, the sequence of charge pairs is
        determined by the [systems] directive in input topology file.
    """
    def __init__(self,*args,**kwargs):
        if 'reschoose' in kwargs and kwargs['reschoose'] is not None:
            if isinstance(kwargs['reschoose'],str):
                if len(kwargs['reschoose'].strip()) != 0:
                    self.reschoose = kwargs['reschoose'].strip()
                else:
                    self.reschoose = 'ALL'
            else:
                print(kwargs['reschose'])
                raise ValueError('reschoose is wrong')
        else:
            self.reschoose = 'ALL'

        bo = False
        if 'toppath' in kwargs and kwargs['toppath'] is not None:
            if isinstance(kwargs['toppath'],str):
                if len(kwargs['toppath'].strip()) != 0:
                    self.toppath = kwargs['toppath'].strip()
                else:
                    bo = True
            else:
                bo = True
            file_size_check(self.toppath,fsize=50)
        else:
            bo = True
        if bo:
            raise ValueError('toppath is wrong')

        if 'in_keyword' in kwargs and kwargs['in_keyword'] is not None:
            if isinstance(kwargs['in_keyword'],str):
                if len(kwargs['in_keyword'].strip()) != 0:
                    self.in_keyword = kwargs['in_keyword'].strip()
                else:
                    self.in_keyword = 'PAIR'
            else:
                raise ValueError('in_keyword is wrong')
        else:
            self.in_keyword = 'PAIR'

        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            if isinstance(kwargs['cut_keyword'],str):
                if len(kwargs['cut_keyword'].strip()) != 0:
                    self.cut_keyword = kwargs['cut_keyword'].strip()
                else:
                    self.cut_keyword = 'MAE'
            else:
                raise ValueError('cut_keyword is wrong')
        else:
            self.cut_keyword = 'MAE'

        if 'fname' in kwargs and kwargs['fname'] is not None:
            if isinstance(kwargs['fname'],str):
                if len(kwargs['fname'].strip()) != 0:
                    self.fname = kwargs['fname'].strip()
                else:
                    self.fname = 'GenGromacsTopfile'
            else:
                raise ValueError('fname is wrong')
        else:
            self.fname = 'GenGromacsTopfile'

        if 'charge_path' in kwargs and kwargs['charge_path'] is not None:
            # func_file_input
            charge_path = kwargs['charge_path']
            if isinstance(charge_path,str):
                file_size_check(charge_path,fsize=50)
                self.file_line_chargepath = charge_path
                self.prochargefile = func_file_input(charge_path,
                                                comment_char='#',
                                                dtype=float,
                                                bool_tail=False,
                                                in_keyword=self.in_keyword,
                                                cut_keyword=self.cut_keyword)
            elif isinstance(charge_path,list):
                self.check_list(charge_path)
                self.prochargefile = charge_path
                self.file_line_chargepath = 'Note: charge_path input is a list'
            else:
                print(charge_path)
                raise ValueError('charge_path is wrong')
        else:
            raise ValueError('charge_path is missing')

        bo = False
        # Note: gennm == 0 means outputs are equal to length of inputs
        if 'gennm' in kwargs and kwargs['gennm'] is not None:
            if isinstance(kwargs['gennm'],int):
                self.gennm = kwargs['gennm']
                if self.gennm < 0: bo = True
            elif isinstance(kwargs['gennm'],str):
                if len(kwargs['gennm'].split()) == 0:
                    self.gennm = 0
                else:
                    try:
                        self.gennm = int(kwargs['gennm'])
                        if self.gennm < 0: raise ValueError
                    except ValueError:
                        bo = True
            else:
                bo = True
        else:
            self.gennm = 0
        if bo:
            raise ValueError('gennm is wrong, it has to be a positive integer')

        if self.gennm == 0: self.gennm = len(self.prochargefile)
        if self.gennm < len(self.prochargefile):
            print('Warning: number of charge entries are larger than gennm')
        else:
            self.gennm = len(self.prochargefile)

        # Note: symmetry_list has to deduct 1 for python-list notation
        if 'symmetry_list' in kwargs and kwargs['symmetry_list'] is not None:
            self.check_symmetry(kwargs['symmetry_list'])
        else:
            self.symmetry_list = []

        self.pro_topfile(self.toppath)

        # check the relation topfile with symmetry_list
        if self.symmetry_list is None or len(self.symmetry_list) == 0:
            self.symmetry_list = list(range(len(self.atomndx)))
        elif len(self.atomndx) < self.symmetry_length:
            raise ValueError('symmetry_list & topfile are not corresponded')
        elif len(self.atomndx) > self.symmetry_length:
            print('Note: only first residue is going to be changed')

        # check the relation chargefile with symmetry_list
        count = 1
        lth = len(self.symmetry_list)
        ls = []
        for i in self.prochargefile[:self.gennm]:
            if len(i) < lth:
                raise ValueError('symmetry_list & topfile are not corresponded')
            elif len(i) > lth:
                ls.append(count)
            count += 1

        if len(ls) > 0:
            print('Warning: number of charges are larger atoms in the topfile')
            print('       : truncation will happen')
            print('       : the number of this charge pair is:')
            for count in ls:
                print(count,end='   ')
            print()



    def check_symmetry(self,key):
        """check symmetry_list

        Attributes:
            self.symmetry_length
            self.symmetry_list
        """
        bo = False
        if key is None:
            self.symmetry_list = []
        elif isinstance(key,list):
            self.symmetry_list = key if len(key) != 0 else []
        elif isinstance(key,str):
            if len(key.strip()) == 0:
                self.symmetry_list = []
            else:
                try:
                    self.symmetry_list = eval(key.strip())
                except:
                    bo = True
        else:
            bo = True

        if not bo and len(self.symmetry_list) != 0:
            flatten = []
            for i in self.symmetry_list:
                if isinstance(i,int):
                    flatten.append(i)
                elif isinstance(i,list):
                    for j in i:
                        if isinstance(j,int):
                            flatten.append(j)
                        else:
                            bo = True
                            break
                else:
                    bo = True
                if bo: break
            self.symmetry_length = len(flatten)
            if self.symmetry_length != len(set(flatten)): bo = True
        if bo:
            print(key)
            raise ValueError('symmetry_list is wrong')



    def check_list(self,list_input):
        """check input list dimensions and data-type, only 2D list is valid"""
        if not isinstance(list_input,list):
            raise ValueError('input is not in list type')
        for i in list_input:
            if isinstance(i,list) and len(i) != 0:
                for j in i:
                    if not isinstance(j,(float,int)):
                        print(j)
                        raise ValueError('cannot convert')
            else:
                print(i)
                raise ValueError('wrong defined')



    def procomments(self,string):
        """remove comments"""
        if string.find(';') == -1:
            return string
        return string[:string.find(';')]



    def pro_topfile(self,toppath):
        """process the topfile

        Attributes:
            self.topfile
            self.atomtypendx
            self.atomndx
        """
        # self.topfile
        with open(toppath,mode='rt') as f: self.topfile = f.readlines()

        i = 0
        atomtypendx = []
        atomndx = []
        molndx = []
        syslist = []
        while i < len(self.topfile):
            # remove the comments
            line = self.procomments(self.topfile[i])

            if line.find('[') != -1:
                line = line.strip().replace(' ','')

            if line == '[atomtypes]':
                j = i + 1
                while True:
                    if j>=len(self.topfile) or self.topfile[j].find('[') != -1:
                        break

                    line = self.topfile[j]
                    subline = self.procomments(line).strip()
                    if len(subline) == 0 or subline[0] in ['#',';']:
                        j += 1
                        continue

                    ltmp = subline.split()
                    if len(ltmp) == 6 or len(ltmp) == 7:
                        atomtypendx.append(j)
                    else:
                        print(line)
                        raise ValueError('wrong top file')

                    j += 1
                i = j

            elif line == '[moleculetype]':
                j = i + 1
                while True:
                    if j>=len(self.topfile) or self.topfile[j].find('[') != -1:
                        break

                    line = self.topfile[j]
                    subline = self.procomments(line).strip()
                    if len(subline) == 0 or subline[0] in ['#',';']:
                        j += 1
                        continue

                    ltmp = subline.split()
                    if len(ltmp) == 2:
                        molndx.append(j)
                    else:
                        print(line)
                        raise ValueError('wrong top file')

                    j += 1
                i = j
            elif line == '[atoms]':
                ls = []
                j = i + 1
                while True:
                    if j>=len(self.topfile) or self.topfile[j].find('[') != -1:
                        break

                    line = self.topfile[j]
                    subline = self.procomments(line).strip()
                    if len(subline) == 0 or subline[0] in ['#',';']:
                        j += 1
                        continue

                    ltmp = subline.split()
                    if len(ltmp) < 6 or len(ltmp) > 8:
                        print(line)
                        raise ValueError('wrong top file')
                    ls.append(j)
                    j += 1
                if len(ls) > 0:
                    atomndx.append(ls)
                i = j
            elif line == '[molecules]':
                j = i + 1
                while True:
                    if j>=len(self.topfile) or self.topfile[j].find('[') != -1:
                        break

                    line = self.topfile[j]
                    subline = self.procomments(line).strip()
                    if len(subline) == 0 or subline[0] in ['#',';']:
                        j += 1
                        continue

                    ltmp = subline.split()
                    if len(ltmp) == 2:
                        syslist.append(ltmp[0])
                    else:
                        print(line)
                        raise ValueError('wrong top file')
                    j += 1
                i = j
            else:
                i += 1

        if len(syslist) == 0 and len(molndx) == 0:
            print('no [moleculetype] nor [molecules] entry is found!')
            raise ValueError('wrong top file')
        if len(syslist) == 0: syslist = molndx

        # adjust the directives' sequence
        proatomndx = []
        for res in syslist:
            bo = True
            print('For top file, processing residue < {:} > ... '.format(res))
            for cmp in atomndx:
                line = self.topfile[cmp[0]]
                if res == line.split()[3]:
                    bo = False
                    proatomndx.append(cmp)
                    break
            if bo:
                print('for residue ' + res + ', its [atoms] is not found')
                raise ValueError('wrong top file')

        # select the residue based on given parameter, self.reschoose
        # self.atomtypendx, self.atomndx
        self.atomtypendx = atomtypendx
        if self.reschoose.upper() != 'ALL':
            count = 0
            self.atomndx = []
            for choose in syslist:
                if choose.upper() == self.reschoose.upper():
                    print('Choosing residue < {:s} >\n'.format(self.reschoose))
                    self.atomndx = proatomndx[count]
                    break
                count += 1

            if len(self.atomndx) == 0:
                print('available residues are: ', syslist)
                raise ValueError('no residue was chosen')
        else:
            print('Choosing all residue\n')
            self.atomndx = [i for j in proatomndx for i in j]



    def run(self):
        """combine the charge file and top file

        Attributes:
            self.outfile
        """
        # take care of self.symmetry_list
        refatomtype = []
        for i in self.symmetry_list:
            if isinstance(i,int):
                line = self.topfile[self.atomndx[i-1]]
                refatomtype.append(line.split()[1])
            else:
                line_1 = self.topfile[self.atomndx[i[0]-1]]
                atype = line_1.split()[1]
                if len(i) > 1:
                    for j in i[1:]:
                        line = self.topfile[self.atomndx[j-1]]
                        if atype != line.split()[1]:
                            print('symmetry_list:')
                            print(line_1[:-1])
                            print(line[:-1])
                            raise ValueError('not equivalent!')
                refatomtype.append(atype)

        totatomtype = []
        for i in self.atomtypendx:
            ltmp = self.topfile[i].split()
            totatomtype.append(ltmp[0])

        atomlist = []
        for i in self.atomndx:
            ltmp = self.topfile[i].split()
            atomlist.append(ltmp[1])

        self.outfile = []
        for charge in self.prochargefile[:self.gennm]:

            # ATTENTION! Here is very important !!!
            # make a copy of self.topfile, avoide the same memory address
            # This copy has the same effect like the DEEP copy
            topfile = self.topfile[:]

            count = 0
            for pair in charge:
                atype = refatomtype[count]
                try:
                    ndx = totatomtype.index(atype)
                except:
                    print(atype)
                    raise ValueError('not defined')
                nm = self.atomtypendx[ndx]
                line = topfile[nm]
                ltmp = self.procomments(line).split()
                subline = ''
                if len(ltmp) == 6:
                    ltmp[2] = pair
                else:
                    ltmp[3] = pair
                for ch in ltmp:
                    subline += '{:>8}  '.format(ch)
                topfile[nm] = subline + '\n'

                # process the [atoms] directive
                scount = 0
                for i in atomlist:
                    if i == atype:
                        snm = self.atomndx[scount]

                        line = topfile[snm]
                        ltmp = self.procomments(line).split()
                        subline = ''
                        if len(ltmp) == 6:
                            ltmp.append(pair)
                        else:
                            ltmp[6] = pair
                        for ch in ltmp:
                            subline += '{:>8}  '.format(ch)
                        topfile[snm] = subline + '\n'
                    scount += 1

                count += 1

            self.outfile.append(topfile)



    def file_print(self):
        """write files"""
        bo = False
        if len(self.outfile) == 0:
            print('Warning: no file is going to output')
            print('       : please try to change the input chargefile')
        else:
            print('\nOne sample of generated GROMACS_top files is:\n')
            print('  [ atoms ]')
            for i in self.atomndx:
                print(self.outfile[0][i],end='')

            line = "This will generate 'top' files, "
            line += '({:} topfiles will be generated)\n'.format(self.gennm)
            line += 'Do you want to continue? y/yes, else quit'
            print(line, end='    ')
            get_input = input()
            if get_input.upper() != 'Y' and get_input.upper != 'YES':
                print('\nWarning: you have decided to quit ...')
                print('       : nothing is generated\n')
            else:
                print('\nGreat! Going to generate files ...\n')
                bo = True

        if bo:
            topnamelist = []
            for top in self.outfile:
                fname = file_gen_new(self.fname,fextend='top',foriginal=False)
                topnamelist.append(fname)
                with open(fname,mode='wt') as f:
                    for line in top:
                        f.write(line)

            fnamelist = self.fname + '_NameList'
            fnamelist = file_gen_new(fnamelist,fextend='txt',foriginal=False)

            print('Note: please check file: < {:} >'.format(fnamelist))
            with open(fnamelist,mode='wt') as f:
                f.write('# The collection of all GROMACS topfile names \n')
                f.write('# The topfile used is:\n')
                f.write('#    {:s}\n'.format(self.toppath))
                f.write('# The charge_file used is:\n')
                f.write('#    {:s}\n\n'.format(self.file_line_chargepath))
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:s}\n\n'.format(str(self.symmetry_list)))
                for i in topnamelist:
                    f.write(i)
                    f.write('\n')



