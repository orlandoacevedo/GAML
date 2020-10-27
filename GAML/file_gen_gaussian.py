from GAML.functions import file_gen_new, file_size_check
import itertools
import random


class File_gen_gaussian(object):
    """
    This class is used to generate Gaussian com files based on input file. Since this input file
    specifically comes from GROMACS MD simulation, so its corresponded topfile has to be given.

    Specially, the [atomtypes] directive in topfile can be added a name string to identify
    the real_atom type. For example, if we has some inputs like;

    [ atomtypes ]
    ; type    mass    charge  ptype  sigma(nm)  epsilon(kj/mol)
       CY    12.011   0.032     A      0.355      0.29288

    It can be modified like;

    [ atomtypes ]
    ; type    mass    charge  ptype  sigma(nm)  epsilon(kj/mol)
      CY-C   12.011   0.032     A      0.355      0.29288

    However, this modification is not a mandatory.


    To make multi-molecular system generation more precise and meaningful, the shortest distance
    between any molecules is no bigger than select_range, by default, this number is set to 10 Angstrom.
    Besides, the basis_set and charge_spin can also be defined.
    """

    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,'info':''}

        if 'toppath' in kwargs and kwargs['toppath'] is not None:
            self.toppath = kwargs['toppath']
            self.log = file_size_check(self.toppath,fsize=10)
            if not self.log['nice']: return
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter toppath is missing'
            return

        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file_path = kwargs['file_path']
            self.log = file_size_check(self.file_path,fsize=500)
            if not self.log['nice']: return
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter file_path is missing'
            return

        self.pro_toppath(self.toppath)
        if not self.log['nice']: return

        self.pro_file_path(self.file_path)
        if not self.log['nice']: return

        self.func_remove_periodic()

        if 'select_range' in kwargs and kwargs['select_range'] is not None:
            try:
                self.select_range = float(kwargs['select_range'])
                if self.select_range <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter select_range has to be a positve number'
                return
        else:
            self.select_range = 10

        self.pro_selections()

        if 'gennm' in kwargs and kwargs['gennm'] is not None:
            try:
                self.gennm = int(kwargs['gennm'])
                if self.gennm > len(self.prolist) or self.gennm <= 0:
                    self.gennm = len(self.prolist)
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter gennm has to be a number\n' + \
                                   'Error gennm: ' + kwargs['gennm']
                return
        elif len(self.prolist) < 5:
            self.gennm = len(self.prolist)
        else:
            self.gennm = 5

        self.random_selections()


        if 'basis_set' in kwargs and kwargs['basis_set'] is not None:
            self.basis_set = kwargs['basis_set']
        else:
            self.basis_set = '# HF/6-31G(d) Pop=CHelpG'


        if 'charge_spin' in kwargs and kwargs['charge_spin'] is not None:
            self.charge_spin = str(kwargs['charge_spin'])
        else:
            self.charge_spin = '0 1'


        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = str(kwargs['fname'])
        else:
            self.fname = 'GaussInput'

        self._prefile()
        if not self.log['nice']: return


    def pro_toppath(self,toppath):
        """process the input top_file, the defined_class parameters are, self.mol,
           self.mollist, self.atom, self.atomnm"""

        def check_periodic_table(atom_name_string):
            """This is a collection of the periodic table, but without the inert gases and
               radioactive elements"""

            atom_name_list = ['Li','Be','Na','Mg','Al','Si','Cl','Ca','Sc','Ti','V','Cr','Mn',
                              'Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y',
                              'Zr','Nb','Mo','Ru','Pd','Ag','Cd','In','Sn','Sb','Te','Cs','Ba',
                              'Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Tl','Pb','Bi','Po',
                              'At','Fr','Ra','H','B','C','N','O','F','P','S','I','K']

            return (atom_name_string.upper() in [i.upper() for i in atom_name_list])


        def func_atomtype(atomtype):
            """This method is used to check and verify the atomtype"""

            print('The following real_atom_type will be used for the com file generations')
            count = 1
            proatomtype = []
            for i in atomtype:
                if len(i) == 1:
                    if len(i[0]) == 1:
                        proatomtype.append([i[0],i[0]])
                        print('Number ',count,'  ',i[0],' --> ',i[0])
                    else:
                        if check_periodic_table(i[0][:2]):
                            proatomtype.append([i[0],i[0][:2]])
                            print('Number ',count,'  ',i[0],' --> ',i[0][:2])
                        elif check_periodic_table(i[0][0]):
                            proatomtype.append([i[0],i[0][0]])
                            print('Number ',count,'  ',i[0],' --> ',i[0][0])
                        else:
                            proatomtype.append([i[0],i[0]])
                            print('Number ',count,'  ',i[0],' --> ','N/A')
                else:
                    proatomtype.append(i)
                    print('Number ',count,'  ',i[0],' --> ',i[1])
                count += 1

            return proatomtype


        with open(toppath,mode='rt') as f:
            infile = f.readlines()

        i = 0
        atomtype = []
        atom = []
        self.mol = []
        while i < len(infile):
            line = infile[i]
            line = line[:line.find(';')]

            if line.find('[') != -1:
                strtmp = ''
                for char in line:
                    if char != ' ' and char != '\t':
                        strtmp += char
                line = strtmp

            if line == '[atomtypes]':
                j = i + 1
                while True:
                    if infile[j].find('[') != -1:
                        break
                    else:
                        line = infile[j]
                        ltmp = line[:line.find(';')].split()
                        if len(ltmp) == 0 or (len(ltmp) > 0 and ltmp[0][0] == '#'):
                            j += 1
                            continue
                        if len(ltmp) == 6 or len(ltmp) == 7:
                            atomtype.append(ltmp[0].split('-'))
                        else:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: wrong defined topfiles\n' + \
                                               '     :' + line
                            return
                        j += 1
                i = j

            elif line == '[atoms]':
                j = i + 1
                while True:
                    if infile[j].find('[') != -1:
                        break
                    else:
                        line = infile[j]
                        ltmp = line[:line.find(';')].split()
                        if len(ltmp) == 0 or (len(ltmp) > 0 and ltmp[0][0] == '#'):
                            j += 1
                            continue
                        if len(ltmp) >= 6:
                            ls = [ltmp[1],ltmp[3]]
                            atom.append(ls)
                        else:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: wrong defined topfiles\n' + \
                                               '     :' + line
                            return
                        j += 1
                i = j

            elif line == '[molecules]':
                j = i + 1
                while True:
                    if j >= len(infile):
                        break
                    else:
                        line = infile[j]
                        ltmp = line[:line.find(';')].split()
                        if len(ltmp) == 0 or (len(ltmp) > 0 and ltmp[0][0] == '#'):
                            j += 1
                            continue
                        if len(ltmp) == 2:
                            ls = [ltmp[0],int(ltmp[1])]
                            self.mol.append(ls)
                        else:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: wrong defined topfiles\n' + \
                                               '     :' + line
                            return
                        j += 1
                i = j

            else:
                i += 1


        # adjust [atoms] parameters sequence to correspond to the [systems] directive sequence
        proatom = []
        for sys in self.mol:
            i = 0
            ltmp = []
            while i < len(atom):
                if atom[i][1] == sys[0]:
                    ltmp.append(atom[i][0])
                i += 1
            proatom.append(ltmp)

        if len(proatom) != len(self.mol):
            self.log['nice'] = False
            line = 'Error: at least one residue name is wrong \n' + \
                   '     : all the residues are: \n'
            for i in self.mol:
                line += i + '    '
            line += '\nError, all the atoms residues are: \n'
            for i in atom:
                line += i + '    '
            self.log['info'] = line
            return

        for i in proatom:
            for latom in i:
                atomndx = True
                for j in range(len(atomtype)):
                    if latom == atomtype[j][0]:
                        atomndx = False
                        break
                if atomndx:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: one of atomtype in pdb file is not defined in the top file\n' + \
                                       'Error atomtype: ' + latom
                    return


        # modify the atom_type
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
                    bool_input = False
                    for i in ltmp:
                        label = i.split('-')
                        if len(label) == 2:
                            try:
                                nm = int(label[0])
                                if nm > len(atomtype):
                                    print('Warning: the input number is too large, the atomtype is not defined')
                                    bool_input = True
                            except ValueError:
                                print('Warning: the input is wrong, only integer is accepted. Please input again')
                                bool_input = True
                        else:
                            print('Warning: the input is wrong, please input again')
                            bool_input = True

                        if bool_input:
                            break
                        atomtype[nm-1][1] = label[1]

                    if not bool_input:
                        print()
                        break
            else:
                break


        # self.mollist, self.atomnm
        self.mollist = []
        self.atomnm = 0
        i = 0
        while i < len(self.mol):
            self.mollist.append(self.mol[i][1])
            self.atomnm += len(proatom[i]) * self.mol[i][1]
            self.mol[i].append(len(proatom[i]))
            i += 1


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
        """process the pdbfile, as well as check its relation with the input topfile,
           the defined_class parameters are, self.box_half_length, self.totlist"""

        # Attention! Here may have bugs if the pdb file is not generated by GROMACS program

        FEXTEND = file_path[file_path.rfind('.')+1:].upper()

        # self.totlist
        self.totlist = []

        if FEXTEND == 'PDB':
            with open(file_path,mode='rt') as f:
                box_length = 0
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    else:
                        if len(line) >= 54 and (line[:4] == 'ATOM' or line[:6] == 'HETATM'):
                            ltmp = []
                            ltmp.append(float(line[30:38]))
                            ltmp.append(float(line[38:46]))
                            ltmp.append(float(line[46:54]))
                            box_length = max(box_length,*ltmp)
                            self.totlist.append(ltmp)

        elif FEXTEND == 'GRO':
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
                    self.totlist.append(ltmp)
                    i += 1
                box_length = float(f.readline().split()[0]) * 10
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: only pdb file and gro files are supported'
            return

        # self.box_half_length
        self.box_half_length = box_length / 2

        if len(self.totlist) != self.atomnm:
            self.log['nice'] = False
            self.log['info'] = 'Error: Top and pdb file are not corresponded'
            return


    def func_remove_periodic(self):
        """remove the periodic molecules, as well as get the Center-Of-Coordinates,
           the defined_class parameters are, self.prototlist, self.avercorlist"""

        self.prototlist = []
        self.avercorlist = []
        count = 0
        for res in self.mol:
            i = 0
            ls = []
            lt = []
            while i < res[1]:
                j = 0
                ltmp = []
                x_cor = []
                y_cor = []
                z_cor = []
                while j < res[2]:
                    ltmp.append(self.totlist[count])
                    x_cor.append(self.totlist[count][0])
                    y_cor.append(self.totlist[count][1])
                    z_cor.append(self.totlist[count][2])
                    j += 1
                    count += 1

                lp = []
                if max(x_cor) - min(x_cor) < self.box_half_length and \
                    max(y_cor) - min(y_cor) < self.box_half_length and \
                    max(z_cor) - min(z_cor) < self.box_half_length:

                    lp.append(sum(x_cor)/len(x_cor))
                    lp.append(sum(y_cor)/len(y_cor))
                    lp.append(sum(z_cor)/len(z_cor))

                    ls.append(ltmp)
                    lt.append(lp)

                i += 1
            self.prototlist.append(ls)
            self.avercorlist.append(lt)



    def pro_selections(self):
        """based on the given select_range, get all the combined residues,
           the defined_class parameters are, self.prolist, the module used, itertools"""

        if len(self.mollist) == 1:
            self.prolist = list(range(len(self.prototlist[0])))
        else:
            self.prolist = []
            reflist = itertools.product(*[range(len(i)) for i in self.prototlist])

            for refcor in reflist:
                x_cor = []
                y_cor = []
                z_cor = []
                count = 0
                for j in refcor:
                    x_cor.append(self.avercorlist[count][j][0])
                    y_cor.append(self.avercorlist[count][j][1])
                    z_cor.append(self.avercorlist[count][j][2])
                    count += 1

                x_cor = sorted(x_cor)
                y_cor = sorted(y_cor)
                z_cor = sorted(z_cor)
                xindex = True
                i = 1
                while i < len(x_cor):
                    if x_cor[i] - x_cor[i-1] > self.select_range:
                        xindex = False
                        break
                    i += 1

                if xindex:
                    yindex = True
                    i = 1
                    while i < len(y_cor):
                        if y_cor[i] - y_cor[i-1] > self.select_range:
                            yindex = False
                            break
                        i += 1

                    if yindex:
                        zindex = True
                        i = 1
                        while i < len(z_cor):
                            if z_cor[i] - z_cor[i-1] > self.select_range:
                                zindex = False
                                break
                            i += 1

                        if zindex:
                            self.prolist.append(refcor)



    def random_selections(self):
        """choose the residues, based on given 'gennm' parameters,
           the defined_class parameters are, self.reflist, the module used, random"""

        # randomly choose the defined_class residue combinations
        self.reflist = []
        lth = len(self.prolist)
        if self.gennm <= lth / 2:
            while len(self.reflist) < self.gennm:
                ndx = random.randrange(lth)
                self.reflist.append(ndx)
                self.reflist = list(set(self.reflist))
        else:
            self.reflist = list(range(lth))
            while len(self.reflist) > self.gennm:
                ndx = random.randrange(len(self.reflist))
                self.reflist.remove(self.reflist[ndx])


    # public method
    def residue_selections(self):

        lp = []
        for ndx in self.reflist:
            ls = []
            count = 0
            for i in self.prolist[ndx]:
                for j in self.prototlist[count][i]:
                    ls.append(j)
                count += 1
            lp.append(ls)


        i = 0
        proatom = []
        while i < len(self.atom):
            proatom += self.atom[i]
            i += 1


        chooselist = []
        count = 1
        for res in lp:
            ltmp = []
            ltmp.append( '%chk={:s}_{:d}.chk'.format(self.fname,count) )
            ltmp.append( self.basis_set )
            ltmp.append( '\n{:s} Charge Analysis\n'.format(self.fname) )
            ltmp.append( self.charge_spin )
            count += 1

            lt = []
            j = 0
            for rxyz in res:
                line = ('{:2}  {:>7} {:>7} {:>7}'.format(proatom[j],rxyz[0],rxyz[1],rxyz[2]))
                ltmp.append(line)
                j += 1
            ltmp.append('\n\n')
            lt.append(ltmp)
            chooselist.append(lt)

        return chooselist


    def _prefile(self):
        """Prepare for print"""

        # the self.resnmprint is used to identify the position of the chosen_residue
        profile = []
        self.resnmprint = []
        for ndx in self.reflist:
            ls = []
            count = 0
            line = ''
            for i in self.prolist[ndx]:
                line += '{:6d}'.format(i)
                for j in self.prototlist[count][i]:
                    ls.append(j)
                count += 1
            profile.append(ls)
            self.resnmprint.append(line)

        i = 0
        proatom = []
        while i < len(self.atom):
            proatom += self.atom[i]
            i += 1


        self.outfile = []
        pfname = self.fname + '_SYS_ALL'
        for res in profile:
            ltmp = []
            ltmp.append( '%chk=check_{:s}.chk'.format(pfname) )
            ltmp.append( self.basis_set )
            ltmp.append( '\n{:s} Charge Analysis\n'.format(pfname) )
            ltmp.append( self.charge_spin )
            count += 1

            ls = []
            j = 0
            for rxyz in res:
                line = ('{:2}  {:>7} {:>7} {:>7}'.format(proatom[j],rxyz[0],rxyz[1],rxyz[2]))
                ltmp.append(line)
                j += 1
            ltmp.append('\n\n')
            ls.append(ltmp)
            self.outfile.append(ls)

        if len(self.outfile) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Warning: no file is going to output\n' + \
                               '       : please try to change the input pdb file'
            return
        else:
            print('\nOne sample of generated Gaussian_com files is:\n')
            for sample in self.outfile[0]:
                for line in sample:
                    print(line)
            print('Do you want to continue?  y/yes, else quit')
            print('    this will generate \'com\' files >',end='    ')
            get_input = input()
            if get_input.upper() != 'Y' and get_input.upper != 'YES':
                self.log['nice'] = False
                self.log['info'] = '\nWarning: you have decided to quit ...\n' + \
                                   '       : nothing is generated\n'
                return
            else:
                print('\nGreat! Going to generate files ...\n')


    def file_print(self):
        """the module used, file_gen_new"""

        fnamelist = []
        for sys in self.outfile:
            filename = file_gen_new(self.fname,fextend='com',foriginal=False)
            fnamelist.append(filename)
            with open(filename,mode='wt') as f:
                for res in sys:
                    for line in res:
                        f.write(line)
                        f.write('\n')


        pfname = self.fname + '_namelist'
        pfname = file_gen_new(pfname,fextend='txt',foriginal=False)
        with open(pfname,mode='wt') as f:
            f.write('# This file is a name_list of chosen_residue \n\n')

            f.write('# The topfile used is:\n')
            f.write('#    {:s}\n\n'.format(self.toppath))

            f.write('# The pdbfile used is:\n')
            f.write('#    {:s}\n\n'.format(self.file_path))

            f.write('# The value corresponds to the input pdb file residue number \n')
            f.write('# The select_range used is < {:} > Angstrom\n'.format(self.select_range))

            f.write('\n  [namelist] \n\n')
            f.write('#   nm  res_1  res_2  ...    filename\n\n')

            j = 1
            count = 0
            for i in fnamelist:
                f.write('{:>6d} {:s}    {:>20s} \n'.format(j,self.resnmprint[count],i))
                count += 1
                j += 1


