from GAML.functions import file_size_check, file_gen_new, function_file_input

class File_gen_mdpotential(object):
    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,}
        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file = kwargs['file_path']
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: no file input'
            return
        log = file_size_check(self.file,fsize=100)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return

        if 'chargefile' in kwargs and kwargs['chargefile'] is not None:
            self.chargefile = kwargs['chargefile']
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: no charge file input'
            return
        log = file_size_check(self.chargefile,fsize=100)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return
        log, self.prochargefile = function_file_input(self.chargefile,bool_tail=False)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return
        
        if 'kwlist' in kwargs and kwargs['kwlist'] is not None:
            if len(kwargs['kwlist']) != 0:
                self.kwlist = kwargs['kwlist']
            else:
                self.kwlist = ['Density']
        else:
            self.kwlist = ['Density']

        if 'bool_gas' in kwargs and kwargs['bool_gas'] is not None:
            self.bool_gas = True if kwargs['bool_gas'] is True else False
        else:
            self.bool_gas = False
        if self.bool_gas and 'Potential' not in self.kwlist:
            self.kwlist.append('Potential')
        if 'Potential' in self.kwlist: self.bool_gas = True

        if 'temperature' in kwargs and kwargs['temperature'] is not None:
            try:
                self.temperature = float(kwargs['temperature'])
            except ValueError:
                self.temperature = 298.0
        else:
            self.temperature = 298.0

        if 'block' in kwargs and kwargs['block'] is not None:
            self.block = kwargs['block']
        else:
            self.block = 'COUNT'
        
        self.literature_value = []
        if 'literature_value' in kwargs and kwargs['literature_value'] is not None:
            for nm in kwargs['literature_value']:
                try:
                    t = float(nm)
                    self.literature_value.append(t)
                except ValueError:
                    pass
        if len(self.literature_value) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: no literature value inputs'
            return

        if len(self.literature_value) < len(self.kwlist):
            print('Warning: the number of properties in kwlist are bigger than\n')
            print('       : the number of literature value inputs, truncation\n')
            print('       : will happen')
            self.kwlist = self.kwlist[:len(self.literature_value)]
        elif len(self.literature_value) > len(self.kwlist):
            print('Warning: the number of literature value inputs are bigger\n')
            print('       : than the number of properties in kwlist,\n')
            print('       : truncation will happen')
            self.literature_value = self.literature[:len(self.kwlist)]

        if 'atomnm' in kwargs and kwargs['atomnm'] is not None:
            try:
                self.atomnm = int(float(kwargs['atomnm']))
            except ValueError:
                self.atomnm = 500
        else:
            self.atomnm = 500

        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname']
        else:
            self.fname = 'MAE_PAIR'

        if 'MAE' in kwargs and kwargs['MAE'] is not None:
            try:
                self.MAE = float(kwargs['MAE'])
            except ValueError:
                self.MAE = 0.05
        else:
            self.MAE = 0.05
            
        self._profile()
        self._pro_bool_gas()
       

    def file_print(self):
        pfname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        with open(pfname,mode='wt') as f:   
            f.write('# Simulation process result\n\n')
            f.write('# The input file used is:\n')
            f.write('#    {:}\n\n'.format(self.file))
            f.write('# The charge file used is:\n')
            f.write('#    {:}\n\n'.format(self.chargefile))
            f.write('# Note the used MAE value is < {:} >\n\n'.format(self.MAE))
            if self.bool_gas:
                f.write('# The total number of atoms are < {:} >\n'.format(self.atomnm))
                f.write('# The temperature is < {:} K >\n'.format(self.temperature))
                self.kwlist = ['HVAP' if i == 'Potential' else i for i in self.kwlist]

            f.write('\n\n')
            cnt = 0
            endlist = []
            for pair in self.prochargefile:
                bool_end = False
                line = 'PAIR  '
                for ch in pair:
                    line += '{:>7.4f} '.format(ch)
                    
                err = self.errlist[cnt]
                if 'NaN' in err:
                    line += 'MAE     NaN'
                else:
                    maerr = sum([abs(tmp) for tmp in err])/len(err)
                    if maerr <= self.MAE:
                        bool_end = True
                    line += 'MAE  {:>6.4f}'.format(maerr)

                ndx = 0
                for kw in self.kwlist:
                    line += '  {:}  '.format(kw)
                    line += '{:>7.4f}'.format(err[ndx])
                    ndx += 1
                f.write(line)
                f.write('\n')

                if bool_end:
                    endlist.append(line.replace('PAIR','HEAD'))
                cnt += 1

            if len(endlist) != 0:
                f.write('\n\n')
                f.write('# The training MAE requirement has been fulfilled\n')
                for t in endlist:
                    f.write(t)
                    f.write('\n')
                

    def _pro_bool_gas(self):
        self.errlist = []
        if self.bool_gas:
            if len(self.blockfile) % 2 != 0:
                print('Warning: the number of liquid simulation results are not\n')
                print('       : equal to the number of gas simulation results,\n')
                print('       : truncation will happen')
                tmp = self.blockfile.pop()
                
            i = 1
            while i < len(self.blockfile):
                ndx = 0
                lt = []
                for rv in self.blockfile[i-1]:
                    if rv[0] == 'Potential':
                        liq = rv[1]
                        gas = self.blockfile[i][ndx][1]
                        if liq is not None and gas is not None:
                            hvap = gas - liq/self.atomnm + 8.314*self.temperature/1000
                        else:
                            hvap = 'NaN'
                        lt.append(hvap)
                    else:
                        if rv[1] is not None:
                            lt.append(rv[1])
                        elif self.blockfile[i][ndx][1] is not None:
                            lt.append(self.blockfile[i][ndx][1])
                        else:
                            lt.append('NaN')
                    ndx += 1

                cnt = 0
                ls = []
                for cv in lt:
                    dv = self.literature_value[cnt]
                    if dv == 0 or cv == 'Nan':
                        ls.append(cv)
                    else:
                        ls.append( (cv-dv)/dv )
                    cnt += 1
                self.errlist.append(ls)
                i += 2
        else:
            for key in self.blockfile:
                cnt = 0
                ls = []
                for cv in key:
                    dv = self.literature_value[cnt]
                    if dv == 0 or cv[1] is None:
                        ls.append('NaN')
                    else:
                        ls.append( (cv[1]-dv)/dv )
                    cnt += 1
                self.errlist.append(ls)
                cnt += 1

    def _profile(self):
        """Process the MD result file"""
        
        with open(self.file,mode='rt') as f:
            infile = f.readlines()
        rawfile = []
        i = 0
        while i < len(infile):
            line = infile[i]
            if self.block in line:
                lt = []
                j = i + 1
                while j < len(infile):
                    line = infile[j]
                    if self.block in line: break
                    
                    for kw in self.kwlist:
                        if kw in line:
                            ltmp = line.split()
                            try:
                                v = float(ltmp[1])
                            except (ValueError,IndexError):
                                v = None
                            lt.append([kw,v])
                    j += 1

                if len(lt) != len(self.kwlist):
                    ltmp = [ t[0] for t in lt]
                    for kw in self.kwlist:
                        if kw not in ltmp:
                            lt.append([kw,None])
                rawfile.append(lt)
                i = j
            else:
                i += 1
        # Adjust sequence of rawfile to be corresponded to self.kwlist
        self.blockfile = []
        for rs in rawfile:
            lt = []
            for cmp in self.kwlist:
                for kw in rs:
                    if cmp == kw[0]:
                        lt.append(kw)
                        break
            self.blockfile.append(lt)



