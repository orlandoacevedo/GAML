from GAML.functions import file_size_check, file_gen_new, func_file_input

class File_gen_mdpotential(object):
    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,}
        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file = kwargs['file_path']
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: no file input'
            return
        self.log = file_size_check(self.file,fsize=100)
        if not self.log['nice']: return

        if 'chargefile' in kwargs and kwargs['chargefile'] is not None:
            self.chargefile = kwargs['chargefile']
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: no charge file input'
            return
        self.log = file_size_check(self.chargefile,fsize=100)
        if not self.log['nice']: return
        self.log, self.prochargefile = func_file_input(self.chargefile,bool_tail=False)
        if not self.log['nice']: return
        
        if 'kwlist' in kwargs and kwargs['kwlist'] is not None:
            if isinstance(kwargs['kwlist'],list) and len(kwargs['kwlist']) != 0:
                self.kwlist = [i.lower() for i in kwargs['kwlist']]
            else:
                self.kwlist = ['density']
        else:
            self.kwlist = ['density']

        if 'bool_gas' in kwargs and kwargs['bool_gas'] is not None:
            self.bool_gas = True if kwargs['bool_gas'] is True else False
        else:
            self.bool_gas = False
        if self.bool_gas and 'potential' not in self.kwlist:
            self.kwlist.append('potential')
        if 'potential' in [i.lower() for i in self.kwlist]: self.bool_gas = True

        if 'temperature' in kwargs and kwargs['temperature'] is not None:
            try:
                self.temperature = float(kwargs['temperature'])
            except ValueError:
                self.temperature = 298.0
        else:
            self.temperature = 298.0

        if 'block' in kwargs and kwargs['block'] is not None:
            self.block = kwargs['block'].lower() if isinstance(kwargs['block'],str) else 'count'
        else:
            self.block = 'count'
        
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
        
        self.literature_value, self.kwlist = self._checknm(self.literature_value,'literature_value',
                                                           self.kwlist,'kwlist')

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
        self._analysis()
       

    def file_print(self):
        pfname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        with open(pfname,mode='wt') as f:   
            f.write('# Simulation process result\n\n')
            f.write('# The input file used is:\n')
            f.write('#    {:}\n\n'.format(self.file))
            f.write('# The charge file used is:\n')
            f.write('#    {:}\n\n'.format(self.chargefile))
            f.write('# Note: the used MAE value is < {:} >\n'.format(self.MAE))
            if self.bool_gas:
                f.write('# Note: the total number of atoms are < {:} >\n'.format(self.atomnm))
                f.write('# Note: the temperature is < {:} K >\n'.format(self.temperature))
                self.kwlist = ['HVAP' if i == 'potential' else i.capitalize() for i in self.kwlist]
            f.write('\n')

            f.write('# Note: the used keywords and their corresponding literature values are:\n')
            f.write('#Keywords: ')
            for kw in self.kwlist: f.write(' {:>8} '.format(kw))
            f.write('\n#LiValues: ')
            for v in self.literature_value: f.write(' {:8} '.format(v))            
            f.write('\n\n\n')

            endlist = []
            lenkw = len(self.kwlist)
            for cnt, pair in enumerate(self.prochargefile):
                bool_end = False
                line = 'PAIR  '
                for ch in pair:
                    line += '{:>7.4f} '.format(ch)
                    
                err = self.errlist[cnt]
                if 'NaN' in err:
                    line += 'MAE     NaN'
                else:
                    maerr = sum([abs(tmp) for tmp in err]) / lenkw
                    if maerr <= self.MAE: bool_end = True
                    line += 'MAE  {:>6.4f}'.format(maerr)

                for ndx, kw in enumerate(self.kwlist):
                    line += '  {:}  '.format(kw)
                    if err[ndx] == 'NaN':
                        line += '    NaN'
                    else:
                        line += '{:>7.4f}'.format(err[ndx])
                f.write(line)
                f.write('\n')

                if bool_end:
                    endlist.append(line.replace('PAIR','HEAD'))

            if len(endlist) != 0:
                f.write('\n\n')
                f.write('# The training MAE requirement has been fulfilled\n')
                for t in endlist:
                    f.write(t)
                    f.write('\n')
                

    def _analysis(self):
        calclist = []
        if self.bool_gas:
            for p in self.blockfile:
                lt = []
                for kw in self.kwlist:
                    if kw == 'potential':
                        tmp = []
                        for s in p:
                            if s[0] == kw: tmp.append(s[1])
                        if len(tmp) == 2:
                            rst = tmp[1] - tmp[0]/self.atomnm + 0.008314*self.temperature
                        else:
                            rst = None
                    else:
                        rst = None
                        for s in p:
                            if s[0] == kw:
                                rst = s[1]
                                break
                    lt.append(rst)
                calclist.append(lt)
        else:
            for p in self.blockfile:
                lt = []
                for kw in self.kwlist:
                    rst = None
                    for s in p:
                        if s[0] == kw:
                            rst = s[1]
                            break
                    lt.append(rst)
                calclist.append(lt)

        self.errlist = []
        for c in calclist:
            lt = []
            for ndx,v in enumerate(self.literature_value):
                if c[ndx] is not None:
                    rst = (c[ndx]-v) / v
                else:
                    rst = 'NaN'
                lt.append(rst)
            self.errlist.append(lt)
    
    
    
    def _profile(self):
        """Process the MD result file"""
        
        with open(self.file,mode='rt') as f:
            infile = f.readlines()
        self.blockfile = []
        i = 0
        while i < len(infile):
            line = infile[i].lower()
            if self.block in line:
                lt = []
                j = i + 1
                while j < len(infile):
                    line = infile[j].lower()
                    if self.block in line: break
                    
                    for kw in self.kwlist:
                        if kw in line:
                            ltmp = line.split()
                            try:
                                v = float(ltmp[1])
                                lt.append([kw,v])
                            except (ValueError,IndexError):
                                pass
                    j += 1
                
                self.blockfile.append(lt)
                i = j
            else:
                i += 1
        
        self.blockfile,self.prochargefile = self._checknm(self.blockfile,'file_path',
                                                          self.prochargefile,'chargefile')


    
    def _checknm(self,m,m_str,n,n_str):
        t1 = len(m)
        t2 = len(n)
        if t1 != t2:
            if t1 < t2:
                smin = m_str
                smax = n_str
                n = n[:t1]
            else:
                smin = m_str
                smax = n_str
                m = m[:t2]
            print('Warning: the number of entries in {:} are more than'.format(smax))
            print('       : the number of {:} inputs, truncation will happen\n'.format(smin))
        return m,n


