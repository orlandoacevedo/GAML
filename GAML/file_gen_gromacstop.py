from GAML.functions import file_gen_new, file_size_check, func_file_input

class File_gen_gromacstop(object):
    """
    This class is used to generate GROMACS topology file based on given charge_path file,
    to be more precise, the symmetry_list also can be input as a reference. Generally,
    the charge_path either can be a path linking a real file, or can be list.

    However, if symmetry_list does not exist, the sequence of charge pairs is determined
    by the [systems] directive in the GROMACS topology file.
    """

    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,}

        if 'reschoose' in kwargs and kwargs['reschoose'] is not None:
            if isinstance(kwargs['reschoose'],str):
                if len(kwargs['reschoose'].split()) != 0:
                    self.reschoose = kwargs['reschoose']
                else:
                    self.reschoose = 'ALL'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter reschoose is not correctly defined'
        else:
            self.reschoose = 'ALL'


        bo = False
        if 'toppath' in kwargs and kwargs['toppath'] is not None:
            if isinstance(kwargs['toppath'],str):
                if len(kwargs['toppath'].split()) != 0:
                    self.toppath = kwargs['toppath']
                else:
                    bo = True
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter toppath is not correctly defined'
            self.log = file_size_check(self.toppath,fsize=50)
            if not self.log['nice']: return
        else:
            bo = True
        if bo:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter toppath is missing'
            return


        if 'in_keyword' in kwargs and kwargs['in_keyword'] is not None:
            if isinstance(kwargs['in_keyword'],str):
                if len(kwargs['in_keyword'].split()) != 0:
                    self.in_keyword = kwargs['in_keyword']
                else:
                    self.in_keyword = 'PAIR'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter in_keyword is not correctly defined'
        else:
            self.in_keyword = 'PAIR'

        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            if isinstance(kwargs['cut_keyword'],str):
                if len(kwargs['cut_keyword'].split()) != 0:
                    self.cut_keyword = kwargs['cut_keyword']
                else:
                    self.cut_keyword = 'MAE'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter cut_keyword is not correctly defined'
        else:
            self.cut_keyword = 'MAE'

        if 'fname' in kwargs and kwargs['fname'] is not None:
            if isinstance(kwargs['fname'],str):
                if len(kwargs['fname'].split()) != 0:
                    self.fname = kwargs['fname']
                else:
                    self.fname = 'GenGromacsTopfile'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter fname is not correctly defined'
        else:
            self.fname = 'GenGromacsTopfile'


        if 'charge_path' in kwargs and kwargs['charge_path'] is not None:
            # func_file_input
            charge_path = kwargs['charge_path']
            if isinstance(charge_path,str):           
                self.log = file_size_check(charge_path,fsize=50)
                if not self.log['nice']: return
                self.file_line_chargepath = charge_path
                self.log, self.prochargefile = func_file_input(charge_path,comment_char='#',dtype=float,
                                                          bool_tail=False,in_keyword=self.in_keyword,
                                                          cut_keyword=self.cut_keyword)
                if not self.log['nice']: return
            elif isinstance(charge_path,list):
                dump_value = self._f_list_dcheck(charge_path)
                if not self.log['nice']: return
                self.prochargefile = charge_path
                self.file_line_chargepath = 'Note: charge_path input is a list'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: wrong defined charge_path parameter\n' + \
                                   'Error: it only can either be a list or a real file path'
                return
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter charge_path is missing'
            return


        bo = False
        # Note: gennm == 0 means outputs are equal to lenght of inputs
        if 'gennm' in kwargs and kwargs['gennm'] is not None:
            if isinstance(kwargs['gennm'],int):
                self.gennm = kwargs['gennm']
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
            self.log['nice'] = False
            self.log['info'] = 'Error: the gennm has to be a positive integer\n' + \
                               'Error gennm: '+ str(kwargs['gennm'])
            return
        self.gennm = min(self.gennm, len(self.prochargefile))
        if self.gennm == 0: self.gennm = len(self.prochargefile)


        # Note: each human-readable indice of symmetry_list has to deduct 1 for python-list
        bo = False
        if 'symmetry_list' in kwargs and kwargs['symmetry_list'] is not None:
            if isinstance(kwargs['symmetry_list'],list):
                self.symmetry_list = kwargs['symmetry_list'] if len(kwargs['symmetry_list']) != 0 else None
            elif isinstance(kwargs['symmetry_list'],str):
                self.symmetry_list = kwargs['symmetry_list'] if len(kwargs['symmetry_list'].split()) != 0 else None
            else:
                bo = True
        else:
            self.symmetry_list = None
        if not bo and isinstance(self.symmetry_list,str):
            try:
                self.symmetry_list = eval(self.symmetry_list)
            except:
                bo = True
        if not bo and self.symmetry_list is not None:
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
            symmetry_length = len(flatten)
            if symmetry_length != len(set(flatten)): bo = True
        if bo:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter symmetry_list is not correctly defined'
            return
    

        dump_value = self._f_pro_topfile(self.toppath)
        if not self.log['nice']: return
        
        # check the relation topfile with symmetry_list
        if self.symmetry_list is None:
            self.symmetry_list = list(range(len(self.atomndx)))
        elif len(self.atomndx) < symmetry_length:
            self.log['nice'] = False
            self.log['info'] = 'Error: the symmetry_list and topfile are not corresponded'
            return
        elif len(self.atomndx) > symmetry_length:
            print('Warning: symmetry_list only makes changes on the first residue')


        # check the relation chargefile with symmetry_list
        count = 1
        lth = len(self.symmetry_list)
        ls = []
        for i in self.prochargefile[:self.gennm]:
            if len(i) < lth:
                self.log['nice'] = False
                self.log['info'] = 'Error: the chargefile and topfile are not corresponded'
                return
            elif len(i) > lth:
                ls.append(count)
            count += 1
            
        if len(ls) > 0:
            print('Warning: the number of charges are bigger than the number of atoms in the topfile')
            print('       : truncation will happen, only the number of leading charges will be used')
            print('       : the number of this charge pair is:')
            for count in ls:
                print(count,end='   ')
            print()



    def _f_list_dcheck(self,list_input):
        """check if the input list dimensions and data-type, only 2D list is valid"""

        self.log['nice'] = True
        self.log['info'] = 'Error: the input_list is not properly defined'
        if not isinstance(list_input,list):
            self.log['nice'] = False
            return
        for i in list_input:
            if isinstance(i,list) and len(i) != 0:
                for j in i:
                    if not isinstance(j,(float,int)):
                        self.log['nice'] = False
                        return 0
            else:
                self.log['nice'] = False
                return 0
        return 1


    def procomments(self,string):
        if string.find(';') == -1:
            return string
        return string[:string.find(';')]


    def _f_pro_topfile(self,toppath):
        """process the topfile, and remove its all comments to a more tight format,
           the final parameters are, self.protopfile, self.atomtypendx, self.atomndx"""

        # self.protopfile
        with open(toppath,mode='rt') as f:
            self.protopfile = f.readlines()

        i = 0
        atomtypendx = []
        atomndx = []
        molndx = []
        syslist = []
        while i < len(self.protopfile):

            # remove the comments
            line = self.procomments(self.protopfile[i])

            if line.find('[') != -1:
                strtmp = ''
                for char in line:
                    if char != ' ' and char != '\t' and char != '\n':
                        strtmp += char
                line = strtmp

            if line == '[atomtypes]':
                j = i + 1
                while True:
                    if self.protopfile[j].find('[') != -1 or j >= len(self.protopfile):
                        break
                    subline = self.protopfile[j]
                    subltmp = self.procomments(subline).split()
                    
                    if len(subltmp) == 0 or (len(subltmp) > 0 and subltmp[0][0] in ['#',';']):
                        j += 1
                        continue
                    if len(subltmp) == 6 or len(subltmp) == 7:
                        atomtypendx.append(j)
                    else:
                        self.log['nice'] = False
                        self.log['info'] = 'Error: wrong top file input\n' + \
                                           'Error: wrong entry,\n' + \
                                           subline
                        return 0
                    
                    j += 1
                i = j
            
            elif line == '[moleculetype]':
                j = i + 1
                while True:
                    if self.protopfile[j].find('[') != -1 or j >= len(self.protopfile):
                        break
                    subline = self.protopfile[j]
                    subltmp = self.procomments(subline).split()
                    
                    if len(subltmp) == 0 or (len(subltmp) > 0 and subltmp[0][0] in ['#',';']):
                        j += 1
                        continue
                    if len(subltmp) == 2:
                        molndx.append(subltmp[0])
                    else:
                        self.log['nice'] = False
                        self.log['info'] = 'Error: wrong top file input\n' + \
                                           'Error: wrong entry,\n' + \
                                           subline
                        return 0
                    
                    j += 1
                i = j

            elif line == '[atoms]':
                ls = []
                j = i + 1
                while True:
                    if self.protopfile[j].find('[') != -1 or j >= len(self.protopfile):
                        break
                    subline = self.protopfile[j]
                    subltmp = self.procomments(subline).split()
                    
                    if len(subltmp) == 0 or (len(subltmp) > 0 and subltmp[0][0] in ['#',';']):
                        j += 1
                        continue
                    if len(subltmp) < 6 and len(subltmp) > 8:
                        self.log['nice'] = False
                        self.log['info'] = 'Error: wrong top file input\n' + \
                                           'Error: wrong entry,\n' + \
                                           subline
                        return 0
                    else:
                        ls.append(j)
                    
                    j += 1

                if len(ls) > 0:
                    atomndx.append(ls)
                i = j
                
            elif line == '[molecules]':
                j = i + 1
                while True:
                    if j >= len(self.protopfile) or self.protopfile[j].find('[') != -1:
                        break
                    subline = self.protopfile[j]
                    subltmp = self.procomments(subline).split()
                    
                    if len(subltmp) == 0 or (len(subltmp) > 0 and subltmp[0][0] in ['#',';']):
                        j += 1
                        continue
                    if len(subltmp) == 2:
                        syslist.append(subltmp[0])
                    else:
                        self.log['nice'] = False
                        self.log['info'] = 'Error: wrong top file input\n' + \
                                           'Error: wrong entry,\n' + \
                                           subline
                        return 0                        
                    j += 1
                i = j    
            
            else:
                i += 1

        if len(syslist) == 0 and len(molndx) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: topfile format is wrong, no [moleculetype] nor [molecules] entry is found!'
            return 0 


        # adjust the directives' sequence
        proatomndx = []
        if len(syslist) == 0: syslist = molndx
        for res in syslist:
            bool_ndx = True
            print('For top file, processing residue < {:s} > ... '.format(res))
            for cmp in atomndx:
                line = self.protopfile[cmp[0]]
                if res == line.split()[3]:
                    bool_ndx = False
                    proatomndx.append(cmp)
                    break
            if bool_ndx:
                self.log['nice'] = False
                self.log['info'] = 'Error: topfile format is wrong\n' + \
                                   '     : for residue' + res + 'the corresponded [atoms] directive is not found'
                return 0 

        # select the residue based on given parameter, self.reschoose
        # self.atomtypendx, self.atomndx
        self.atomtypendx = atomtypendx
        if self.reschoose.upper() != 'ALL':
            
            count = 0
            self.atomndx = []
            for choose in syslist:
                if choose.upper() == self.reschoose.upper():
                    print('\nFor top file, choosing residue < {:s} >\n'.format(self.reschoose))
                    self.atomndx = proatomndx[count]
                    break
                count += 1

            if len(self.atomndx) == 0:
                self.log['nice'] = False
                self.log['info'] = 'Error: wrong reschoose parameter\n' + \
                                   'Error: no residue was chosen\n' + \
                                   'Error: the available residues are;' + syslist
                return 0
        else:
            print('\nFor top file, choosing all residue\n')
            self.atomndx = [i for j in proatomndx for i in j]

        return 1



    def run(self):
        """combine the charge file and top file, the defined_class parameter, self.outfile"""

        # take care of self.symmetry_list
        refatomtype = []
        for i in self.symmetry_list:
            if isinstance(i,int):
                line = self.protopfile[self.atomndx[i-1]]
                refatomtype.append(line.split()[1])
            else:
                line_1 = self.protopfile[self.atomndx[i[0]-1]]
                atype = line_1.split()[1]
                if len(i) > 1:
                    for j in i[1:]:
                        line = self.protopfile[self.atomndx[j-1]]
                        if atype != line.split()[1]:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: the atom_types under [atoms] directive in top file is not equivalent\n' + \
                                               'Error: symmetry_list:\n' + line_1[:-1] + '\n' + line[:-1]
                            return 0
                refatomtype.append(atype)
        
        totatomtype = []
        for i in self.atomtypendx:
            ltmp = self.protopfile[i].split()
            totatomtype.append(ltmp[0])

        atomlist = []
        for i in self.atomndx:
            ltmp = self.protopfile[i].split()
            atomlist.append(ltmp[1])

        self.outfile = []
        for charge in self.prochargefile[:self.gennm]:

            # ATTENTION! Here is very important !!!
            # make a copy of self.protopfile, avoide the same memory address
            # This copy has the same effect like the DEEP copy due to its DATA TYPE
            topfile = self.protopfile[:]

            count = 0
            for pair in charge:
                atype = refatomtype[count]
                try:
                    ndx = totatomtype.index(atype)
                except:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: the atom_type in [atoms] is not defined in [atomtypes]\n' + \
                                       'Error:' + str(i)
                    return 0
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

        return 1


    def file_print(self):

        bo = False
        if len(self.outfile) == 0:
            print('Warning: no file is going to output')
            print('       : please try to change the input chargefile')
        else:
            print('\nOne sample of generated GROMACS_top files is:\n')
            print('  [ atoms ]')
            for i in self.atomndx:
                print(self.outfile[0][i],end='')
            
            print('\nDo you want to continue? ( {:} topfiles will be generated ). y/yes, else quit'.format(self.gennm))
            print('This will generate \'top\' files >',end='    ')
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
            
            with open(fnamelist,mode='wt') as f:
                f.write('# This is a collection of all the generated GROMACS topfile names \n')
                f.write('# The topfile used is:\n')
                f.write('#    {:s}\n'.format(self.toppath))
                f.write('# The charge_file used is:\n')
                f.write('#    {:s}\n\n'.format(self.file_line_chargepath))
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:s}\n\n'.format(str(self.symmetry_list)))
                for i in topnamelist:
                    f.write(i)
                    f.write('\n')


