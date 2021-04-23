from GAML.functions import file_gen_new, file_size_check
import random


class File_gen_gaussian(object):
    """Generate Gaussian com files based on input file

    Args:
        topfile   (str) :   GROMACS template topology file
        file_path (str) :   equilibrated Box, (pdb|gro)

    Specially, the [atomtypes] directive of input can be edited to
    identify the real atom type.

    For example, if we have some inputs like;

    [ atomtypes ]
    ; type    mass    charge  ptype  sigma(nm)  epsilon(kj/mol)
       CY    12.011   0.032     A      0.355      0.29288

    It can be modified like;

    [ atomtypes ]
    ; type    mass    charge  ptype  sigma(nm)  epsilon(kj/mol)
      CY-C   12.011   0.032     A      0.355      0.29288

    Note: this modification is not mandatory.

    To make multi-molecular system generation more precise and meaningful,
    the shortest distance between any molecules will be no larger than
    select range, by default, this number is set to 10 Angstrom.
    Besides, the basis_set and charge_spin can also be defined.
    """
    def __init__(self,*args,**kwargs):
        if 'toppath' in kwargs and kwargs['toppath'] is not None:
            self.toppath = kwargs['toppath']
            file_size_check(self.toppath,fsize=10)
        else:
            raise ValueError('toppath is missing')

        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file_path = kwargs['file_path']
            file_size_check(self.file_path,fsize=500)
        else:
            raise ValueError('file_path is missing')

        self.pro_toppath(self.toppath)
        self.pro_file_path(self.file_path)

        if 'select_range' in kwargs and kwargs['select_range'] is not None:
            try:
                self.select_range = float(kwargs['select_range'])
                if self.select_range <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError('select_range has to be a positive number')
        else:
            self.select_range = 10

        if 'reschoose' in kwargs and kwargs['reschoose'] is not None:
            tmp = kwargs['reschoose'].strip()
            self.reschoose = 'all' if len(tmp) == 0 else tmp.lower()
        else:
            self.reschoose = 'all'

        if 'gennm' in kwargs and kwargs['gennm'] is not None:
            try:
                self.gennm = int(kwargs['gennm'])
                if self.gennm <= 0: raise ValueError
            except ValueError:
                raise ValueError('gennm has to be positive integer')
        else:
            self.gennm = 5

        self.pro_selections()

        if 'basis_set' in kwargs and kwargs['basis_set'] is not None:
            self.basis_set = kwargs['basis_set'].strip()
        else:
            self.basis_set = '# HF/6-31G(d) Pop=CHelpG'

        if 'charge_spin' in kwargs and kwargs['charge_spin'] is not None:
            self.charge_spin = kwargs['charge_spin'].strip()
        else:
            self.charge_spin = '0 1'

        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname'].strip()
        else:
            self.fname = 'GaussInput'



    def pro_toppath(self,toppath):
        """process topology file

        Attributes:
            self.mol        :   List[[res, molnm, atomnm]]
            self.atom       :   List[[atomtype, ...]]
        """
        def get_atomtype(atom):
            """get real atom type

            No inert gases and radioactive elements

            None    :   means not found
            """
            if atom is None or len(atom) == 0:
                return None
            pt = [
                'Li','Be','Na','Mg','Al','Si','Cl','Ca','Sc','Ti','V','Cr',
                'Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br',
                'Rb','Sr','Y','Zr','Nb','Mo','Ru','Pd','Ag','Cd','In','Sn',
                'Sb','Te','Cs','Ba','Lu','Hf','Ta','W','Re','Os','Ir','Pt',
                'Au','Tl','Pb','Bi','Po','At','Fr','Ra','H','B','C','N',
                'O','F','P','S','I','K',
            ]
            lp = [i.lower() for i in pt]

            if len(atom) == 1:
                if atom.lower() in lp:
                    return pt[lp.index(atom.lower())]
                return None

            atom = atom if len(atom) <= 2 else atom[:2]
            if atom.lower() in lp:
                return pt[lp.index(atom.lower())]
            if len(atom) > 1:
                atom = atom[0]
                if atom.lower() in lp:
                    return pt[lp.index(atom.lower())]
            return None


        def func_atomtype(atomtype):
            """check and verify the atomtype"""
            print('The following atom type will be used for com files')
            count = 1
            proatomtype = []
            for i in atomtype:
                if i[1] is None:
                    at = get_atomtype(i[0])
                    if at is None: at = i[0]
                    print('No. {:2}  {:9} --> {:}'.format(count,i[0],at))
                    proatomtype.append([i[0],at])
                else:
                    proatomtype.append(i)
                    print('No. {:2}  {:9}  -->  {:}'.format(count,i[0],i[1]))
                count += 1

            return proatomtype


        with open(toppath,mode='rt') as f: infile = f.readlines()

        i = 0
        atomtype = []
        atom = []
        self.mol = []
        while i < len(infile):
            line = infile[i]
            line = line if line.find(';') == -1 else line[:line.find(';')]

            if line.find('[') != -1:
                line = line.strip().replace(' ','')

            if line == '[atomtypes]':
                j = i + 1
                while j < len(infile):
                    line = infile[j]
                    l = line if line.find(';') == -1 else line[:line.find(';')]
                    l = l.strip()
                    if len(l) == 0 or l[0] == '#':
                        j += 1
                        continue

                    if l[0] == '[': break

                    ltmp = l.split()
                    if len(ltmp) == 6 or len(ltmp) == 7:
                        p = ltmp[0].split('-')
                        if len(p) == 1:
                            atomtype.append([ltmp[0],None])
                        elif len(p) == 2:
                            atomtype.append(p)
                        else:
                            print(line)
                            raise ValueError('wrong defined entry')
                    else:
                        print(line)
                        raise ValueError('wrong defined entry')
                    j += 1
                i = j
            elif line == '[atoms]':
                j = i + 1
                while j < len(infile):
                    line = infile[j]
                    l = line if line.find(';') == -1 else line[:line.find(';')]
                    l = l.strip()
                    if len(l) == 0 or l[0] == '#':
                        j += 1
                        continue

                    if l[0] == '[': break

                    ltmp = l.split()
                    if len(ltmp) >= 6:
                        atom.append([ltmp[1],ltmp[3]])
                    else:
                        print(line)
                        raise ValueError('wrong defined entry')
                    j += 1
                i = j
            elif line == '[molecules]':
                j = i + 1
                while j < len(infile):
                    line = infile[j]
                    l = line if line.find(';') == -1 else line[:line.find(';')]
                    l = l.strip()
                    if len(l) == 0 or l[0] == '#':
                        j += 1
                        continue

                    if l[0] == '[': break

                    ltmp = l.split()
                    if len(ltmp) == 2:
                        self.mol.append([ltmp[0],int(ltmp[1])])
                    else:
                        print(line)
                        raise ValueError('wrong defined entry')
                    j += 1
                i = j
            else:
                i += 1

        # adjust [atoms] parameters sequence
        # to make it correspond to the [systems] directive sequence
        proatom = []
        for sys in self.mol:
            ltmp = []
            for t in atom:
                if t[1] == sys[0]:
                    ltmp.append(t[0])
            if len(ltmp) != 0:
                proatom.append(ltmp)

        if len(proatom) != len(self.mol):
            print('Error: at least one residue name is wrong')
            print(self.mol)
            print('Error: all the atoms residues are:')
            print(atom)
            raise ValueError('not corresponded')

        if sum([len(i) for i in proatom]) != len(atom):
            print('Error: [atom] directive is wrong defined')
            raise ValueError('wrong defined')

        # check atom types between [atom] and [atomtype]
        for i in proatom:
            for t in i:
                bo = True
                for j in atomtype:
                    if t == j[0]:
                        bo = False
                        break
                if bo:
                    print(t)
                    raise ValueError('not found')

        # prompt to modify the atom type
        while True:
            atomtype = func_atomtype(atomtype)
            print('Do you want to make a modification? y/yes, else continue')
            gt = input()
            if gt.lower() == 'y' or gt.lower() == 'yes':
                print('Please label which atom type do you want to change?')
                print('Multiple inputs are supported, please use comma separate them')
                print('For example, "2-C" or "2 - C" or "2-C, 5 - O, 6-H"')
                while True:
                    gstr = input()
                    ltmp = gstr.split(',')
                    bo = False
                    for i in ltmp:
                        label = i.split('-')
                        if len(label) == 2:
                            try:
                                nm = int(label[0])
                                if nm > len(atomtype):
                                    print('Warning: the input number is too large, the atomtype is not defined')
                                    bo = True
                            except ValueError:
                                print('Warning: the input is wrong, only integer is accepted. Please input again')
                                bo = True
                        else:
                            print('Warning: the input is wrong, please input again')
                            bo = True

                        if bo:
                            break
                        atomtype[nm-1][1] = label[1]

                    if not bo:
                        print()
                        break
            else:
                break

        for i in range(len(self.mol)): self.mol[i].append(len(proatom[i]))

        # self.atom
        self.atom = []
        for i in proatom:
            ltmp = []
            for latom in i:
                for j in range(len(atomtype)):
                    if latom == atomtype[j][0]:
                        ltmp.append(atomtype[j][1])
                        break
            self.atom.append(ltmp)



    def pro_file_path(self,file_path):
        """process input file

        As well as check its relation with the input topfile

        Attributes:
            self.prototlist         :   List[List[List[[x,y,z]]]]
            self.avercorlist        :   List[List[[float,float,float]]]
            self.box_half_length    :   float
        """
        # Attention!
        # Here may have bugs if file is not generated by GROMACS program

        if file_path.find('.') == -1 or file_path.rfind('.')+1 >= len(file_path):
            ext = 'pdb'
        else:
            ext = file_path[file_path.rfind('.')+1:].lower()

        totlist = []
        if ext == 'pdb':
            with open(file_path,mode='rt') as f:
                box_length = 0
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    if len(line) >= 54 and (line[:4].upper() == 'ATOM' or line[:6].upper() == 'HETATM'):
                        ltmp = []
                        ltmp.append(float(line[30:38]))
                        ltmp.append(float(line[38:46]))
                        ltmp.append(float(line[46:54]))
                        box_length = max(box_length,*ltmp)
                        totlist.append(ltmp)
        elif ext == 'gro':
            with open(file_path,mode='rt') as f:
                title = f.readline()
                nm = int(f.readline().split()[0])
                i = 0
                while i < nm:
                    line = f.readline()
                    ltmp = []
                    ltmp.append(float(line[20:28])*10)
                    ltmp.append(float(line[28:36])*10)
                    ltmp.append(float(line[36:44])*10)
                    totlist.append(ltmp)
                    i += 1
                box_length = float(f.readline().split()[0]) * 10
        else:
            raise ValueError('only pdb & gro files are supported')

        # self.box_half_length
        self.box_half_length = box_length / 2

        if len(totlist) != sum([t[1]*t[2] for t in self.mol]):
            print('length of totlist and number of atomnm')
            raise ValueError('not corresponded')


        self.prototlist = []
        self.avercorlist = []
        count = 0
        for res in self.mol:
            ls = []
            lt = []
            for i in range(res[1]):
                xyz = []
                for j in range(res[2]):
                    xyz.append(totlist[count])
                    count += 1

                # take care of minimum image convention
                for cnt in range(len(xyz)):
                    if xyz[cnt][0] - xyz[0][0] > self.box_half_length:
                        xyz[cnt][0] -= self.box_half_length * 2
                    elif xyz[cnt][0] - xyz[0][0] < -self.box_half_length:
                        xyz[cnt][0] += self.box_half_length * 2

                    if xyz[cnt][1] - xyz[0][1] > self.box_half_length:
                        xyz[cnt][1] -= self.box_half_length * 2
                    elif xyz[cnt][1] - xyz[0][1] < -self.box_half_length:
                        xyz[cnt][1] += self.box_half_length * 2

                    if xyz[cnt][2] - xyz[0][2] > self.box_half_length:
                        xyz[cnt][2] -= self.box_half_length * 2
                    elif xyz[cnt][2] - xyz[0][2] < -self.box_half_length:
                        xyz[cnt][2] += self.box_half_length * 2

                xtot = [i[0] for i in xyz]
                ytot = [i[1] for i in xyz]
                ztot = [i[2] for i in xyz]

                xage = sum(xtot) / len(xtot)
                yage = sum(ytot) / len(ytot)
                zage = sum(ztot) / len(ztot)

                ls.append(xyz)
                lt.append([xage, yage, zage])

            self.prototlist.append(ls)
            self.avercorlist.append(lt)



    def pro_selections(self):
        """based on the given select_range, get all the combined residues

        Attributes:
            self.chooselist    :   List[List[[resnm,molnm], ...]]
        """

        # determine which residue to choose
        if len(self.mol) == 1:
            self.reschoose = self.mol[0][0].lower()
        if self.reschoose != 'all':
            tmp = [res[0].lower() for res in self.mol]
            if self.reschoose not in tmp:
                print('available residues: ',tmp)
                raise ValueError('not found')
            ndx = tmp.index(self.reschoose)
            self.prototlist = [self.prototlist[ndx],]
            self.avercorlist = [self.avercorlist[ndx],]
            self.atom = [self.atom[ndx],]
            self.mol = [self.mol[ndx],]

        # format: List[List[List[[resnm,molnm]]]]
        #              res  mol      index
        # !! searching is based on an increasing order
        ndxlist = []
        dselrange = self.select_range**2
        for rnm,res in enumerate(self.avercorlist):
            lp = []
            for m,v in enumerate(res):
                ls = []
                # self
                n = m + 1
                while n < len(res):
                    d = [v[tmp]-res[n][tmp] for tmp in range(3)]
                    if d[0]**2 + d[1]**2 + d[2]**2 <= dselrange:
                        ls.append([rnm,n])
                    n += 1

                # cross
                cnt = rnm + 1
                while cnt < len(self.avercorlist):
                    ces = self.avercorlist[cnt]
                    for y,p in enumerate(ces):
                        d = [v[tmp]-p[tmp] for tmp in range(3)]
                        if d[0]**2 + d[1]**2 + d[2]**2 <= dselrange:
                            ls.append([cnt,y])
                    cnt += 1
                lp.append(ls)
            ndxlist.append(lp)
        
        # for each mol in every residue, get all its surroundings
        for i in range(len(ndxlist)):
            s = i
            while s >= 0:
                for j in range(len(ndxlist[i])):
                    t = j - 1
                    while t > 0:
                        # list in list operation
                        if [i,j] in ndxlist[s][t]:
                            ndxlist[i][j].append([s,t])
                        t -= 1
                s -= 1

        ratiolist = self.gen_ratiolist()
        self.chooselist = self.gen_reflist(ndxlist,ratiolist,self.gennm)
        
        if len(self.chooselist) != self.gennm:
            # no matter how is the result, try this certain of time
            for _ in range(10):
                newlist = self.gen_reflist(ndxlist,ratiolist,self.gennm)
                # number of outputs are not enough
                bo = False
                # dynamically update
                for new in newlist:
                    bo = True
                    for chk in self.chooselist:
                        if len(new) == len(chk):
                            bo = False
                            for g in new:
                                if not g in chk:
                                    bo = True
                                    break
                            if not bo:
                                break
                    if bo:
                        self.chooselist.append(new)
                        bo = True if len(self.chooselist) >= self.gennm else False
                if bo:
                    break
        
        if len(self.chooselist) == 0:
            print('Warning: please try to increase select range')
            raise RuntimeError('no generation')



    def gen_ratiolist(self):
        """generate minimum choose molnm for each residue

        This list can be used for future updates
        """
        if len(self.mol) > 1:
            reslist = sorted([i[1] for i in self.mol])
            gcd = reslist[0]
            # calculate greatest common divisor
            for t in reslist[1:]:
                while gcd != 0:
                    t, gcd = gcd, t%gcd
                gcd = t
            ratiolist = [i[1]//gcd for i in self.mol]
        else:
            ratiolist = [1,]

        return ratiolist



    def gen_reflist(self,ndxlist,ratiolist,gennm=5,maxtry=1000000):
        """generate referring list based on surrounding list

        Args:
            ndxlist: List[List[List[[resnm,molnm]]]]
                          res  mol   surroundings
            maxtry  :   int :   maximum number of trying

        Returns:
            reflist :   List[[resnm,molnm,[molndx]], ...]]
        """
        if maxtry <= gennm*10: maxtry = gennm * 2

        # format: dict{dict{int}}
        #       resnm: molnm: surnm
        ndxdict = {}
        for i,res in enumerate(ndxlist):
            ndxdict[i] = {}
            for j,mol in enumerate(res):
                if len(mol) != 0:
                    ndxdict[i][j] = len(mol)

        reskeyndxlist = [ k for k in ndxdict if len(ndxdict[k]) != 0 ]

        reflist = []
        trycnt = 0
        while len(reflist) < gennm:
            if trycnt > maxtry:
                #raise RuntimeError('maximum trying is reached')
                break
            trycnt += 1

            # first, randomly choose res
            resnm = random.choice(reskeyndxlist)

            # second, randomly choose mol
            molnm = random.choice([k for k in ndxdict[resnm]])

            # third, number of molecules
            tot = ndxdict[resnm][molnm]
            nm = min(6,tot)
            ndx = random.sample(range(tot),nm)

            # fourth, get all their circles
            # make sure every entry is unique
            ref = ndxlist[resnm][molnm]
            add = []
            for t in ndx:
                sur = ref[t]
                for s in ndxlist[sur[0]][sur[1]]:
                    if s not in ref and s not in add:
                        add.append(s)
            
            # fifth, categorize them
            catlist = []
            for i in range(len(ratiolist)):
                ls = []
                for p in ref:
                    if p[0] == i:
                        ls.append(p)
                for p in add:
                    if p[0] == i:
                        ls.append(p)
                catlist.append(ls)
            
            # sixth, number of clusters
            selectlist = [len(i) for i in catlist]
            if 0 in selectlist: continue

            n = random.randrange(1,6)
            while n >= 1:
                bo = True
                for a, num in enumerate(selectlist):
                    if ratiolist[a]*n > num:
                        bo = False
                        break
                if bo:
                    break
                else:
                    n -= 1
            if n <= 0: continue

            chooselist = [i*n for i in ratiolist]

            # seventh, choosing
            # format: 2D: List[[resnm,mol]]
            new = []
            for c, pie in enumerate(catlist):
                for r in random.sample(pie,chooselist[c]):
                    new.append(r)
            
            # finally, make sure no repeats
            bo = True
            for chk in reflist:
                if len(chk) == len(new):
                    # assume it is not unique
                    bo = False
                    for g in new:
                        if not g in chk:
                            bo = True
                            break
                    if not bo:
                        break
            if not bo: continue

            reflist.append(new)

        return reflist



    def run(self):
        """Prepare for write

        Attributes:
            self.prototlist
            self.chooselist
            self.fname
            self.atom
            self.basis_set
            self.charge_spin

        Returns:
            self.outfile    :   List[file, ...]
        """
        self.outfile = []
        for res in self.chooselist:
            line = self.basis_set + '\n\n'
            line += '{:} Charge Analysis\n\n'.format(self.fname)
            line += self.charge_spin + '\n'
            for ndx in res:
                mol = self.prototlist[ndx[0]][ndx[1]]
                j = 0
                for t in mol:
                    v1 = round(t[0],4)
                    v2 = round(t[1],4)
                    v3 = round(t[2],4)
                    line += '{:5}  {:>7} {:>7} {:>7}\n'.format(self.atom[ndx[0]][j],v1,v2,v3)
                    j += 1
            line += '\n\n\n'
            self.outfile.append(line)



    def file_print(self):
        """writing to file"""

        print('One sample of generated Gaussian_com files is:\n')
        print(self.outfile[0],end='')
        print('Do you want to continue?  y/yes, else quit')
        line = 'This will generate < {:} > files'.format(len(self.outfile))
        print(line)
        tmp = input()
        if tmp.lower() != 'y' and tmp.lower != 'yes':
            print('Note: exiting...')
            return
        print('\nGreat! Going to generate files ...\n')


        fnamelist = []
        for line in self.outfile:
            filename = file_gen_new(self.fname,fextend='com',foriginal=False)
            fnamelist.append(filename)
            new = filename[:filename.rfind('.')]
            line = '%chk={:}.chk\n'.format(new) + line

            with open(filename,'wt') as f: f.write(line)


        pf = self.fname + '_namelist'
        pf = file_gen_new(pf,fextend='txt',foriginal=False)
        print('Note: please check file: < {:} >'.format(pf))
        with open(pf,mode='wt') as f:
            f.write('# Collection of generated file names\n\n')
            f.write('# The topfile is:\n')
            f.write('#    {:}\n\n'.format(self.toppath))
            f.write('# The pdbfile is:\n')
            f.write('#    {:}\n\n'.format(self.file_path))
            f.write('# The select_range is < {:} > Angstrom\n'.format(self.select_range))

            f.write('# Reference format: [residue-index, molecule-index]\n\n')

            for i,j in enumerate(fnamelist):
                line = ''
                for t in self.chooselist[i]:
                    line += '[' + str(t[0]+1) + ',' + str(t[1]+1) + ']  '
                line = line.strip()
                f.write('{:<6d}: {:} \n'.format(i+1,line))



