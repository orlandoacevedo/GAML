from GAML.functions import file_size_check, file_gen_new
from GAML.file_gen_gromacstop import File_gen_gromacstop
from GAML.charge_gen_scheme import Charge_gen_scheme

import os
import shutil
from pkg_resources import resource_string

class GAML_autotrain(object):
    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,}
        if 'file_path' not in kwargs or kwargs['file_path'] is None:
            self.log['nice'] = False
            self.log['info'] = 'Error: no file inputs'
            return
        self.file = kwargs['file_path']
        log = file_size_check(self.file,fsize=2)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return
        
        self.fname = 'PAIR_Charge'
        self.parameters = { 'top_gas_path'        : None,
                            'top_liq_path'        : None,
                            'gro_gas_path'        : None,
                            'gro_liq_path'        : None,
                            'grompp_min_gas_path' : None,
                            'grompp_min_liq_path' : None,
                            'grompp_npt_liq_path' : None,
                            'grompp_prod_gas_path': None,
                            'grompp_prod_liq_path': None,
                            'charge_range_path'   : None,
                            'gromacs_energy_kw'   : 'Density',
                            'literature_value'    : 1000,
                            'gmx'                 : 'gmx',
                            'MAE'                 : 0.05,
                            'training_total_nm'   : 5,
                            'training_cnt'        : 1,
                            'gennm'               : 10,
                            'error_tolerance'     : 0.5,
                            'symmetry_list'       : None,
                            'pn_limit'            : None,
                            'counter_list'        : None,
                            'offset_list'         : None,
                            'offset_nm'           : None,
                            'ratio'               : None,
                            'nmround'             : None,
                            'total_charge'        : 0.0,
                            'charge_extend_by'    : None,
                            'threshold'           : None,
                            'bool_neutral'        : None,
                            'bool_nozero'         : None,
                            'bool_abscomp'        : None,
                         }
        
        self._profile()
        if not self.log['nice']: return
        self._proparameters()
        if not self.log['nice']: return
        self._try_file_generations()
        if not self.log['nice']: return

        # check for the bash scripts
        if 'bashinterfile' in kwargs and kwargs['bashinterfile'] is not None:
            self.bashinterfile = kwargs['bashinterfile']
            log = file_size_check(self.bashinterfile,fsize=10)
            if not log['nice']:
                self.log['nice'] = False
                self.log['info'] = log['info']
                return
            with open(self.bashinterfile,mode='rt') as f:
                self._shfile = f.read()
        else:
            self.bashinterfile = 'GAML-BASH-Interface.sh'
            self._shfile = resource_string(__name__,'shell/'+self.bashinterfile).decode('utf-8').replace('\r','')


        
    def _profile(self):
        """Process input auto-settingfile"""

        def procomments(string):
            if string.find('#') != -1:
                return string[:string.find('#')]
            return string

        errinfo = 'Error: wrong defined settingfile\n'
        parlist = [k for k in self.parameters]
        with open(self.file,mode='rt') as f:
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                else:
                    subline = procomments(line)
                    if len(subline.split()) != 0:
                        if subline.find('=') == -1:
                            self.log['nice'] = False
                            self.log['info'] = errinfo + 'Error line: ' + line
                            return
                        lp = subline.split('=',maxsplit=1)
                        partmp = lp[0].split()
                        if len(partmp) != 1:
                            self.log['nice'] = False
                            self.log['info'] = errinfo + 'Error line: ' + line
                            return
                            
                        parname = partmp[0]
                        if parname not in parlist:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: wrong defined parameter\n' + \
                                               'Error parameter: ' + parname
                            return

                        stmp = lp[1]
                        lt = stmp.split()
                        if len(lt) != 0:
                            # take care of python representation string list to real python list
                            if parname == 'symmetry_list' or parname == 'counter_list' or \
                               parname == 'offset_list':
                                try:
                                    s = eval(stmp)
                                except:
                                    self.log['nice'] = False
                                    self.log['info'] = errinfo + 'Error line: ' + line
                                    return
                                self.parameters[parname] = s

                                #Special case for bash print out
                                self.parameters[parname + 'RAW'] = stmp.strip()
                            elif parname == 'pn_limit' or parname == 'gromacs_energy_kw' or \
                                 parname == 'literature_value':
                                st = ''
                                for c in lt: st += c + ' '
                                self.parameters[parname] = st
                            elif len(lt) != 1:
                                self.log['nice'] = False
                                self.log['info'] = errinfo + 'Error line: ' + line
                                return
                            else:
                                self.parameters[parname] = lt[0]

                                
    def _proparameters(self):
        cwd = os.getcwd()
        for par,name in self.parameters.items():
            if 'path' in par and name is not None:
                filepath = self.parameters[par]
                filehead,filetail = os.path.split(filepath)
                if os.path.isfile(filepath):
                    if os.path.islink(filetail) or (not os.path.isfile(filetail)):
                        shutil.copy(filepath,cwd)
                    self.parameters[par] = filetail
                else:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: cannot find the file ' + self.parameters[par]
                    return
                

    def _try_file_generations(self):
        # Make a copy and add a key for Charge_gen_scheme
        pardir = { **self.parameters }
        pardir['charge_path'] = pardir['charge_range_path']
        
        cs = Charge_gen_scheme(**pardir)
        if not cs.log['nice']:
            self.log['nice'] = False
            self.log['info'] = cs.log['info']
            return
        
        pardir['charge_path'] = cs.chargepair
        pardir['toppath'] = pardir['top_liq_path']
        fg = File_gen_gromacstop(**pardir)
        if not fg.log['nice']:
            self.log['nice'] = False
            self.log['info'] = fg.log['info']
            return

    def file_print(self):
        pf = file_gen_new('bash_GAML_AutoTraining',fextend='sh')
        with open(pf,mode='wt') as f:
            f.write('#!/bin/bash\n')
            f.write('# -*- coding: utf-8 -*-\n\n')
            for key in sorted(self.parameters):
                if 'RAW' in key:
                    pass
                elif self.parameters[key] is None:
                    f.write("{:}=''\n".format(key))
                else:
                    if key == 'symmetry_list' or key == 'counter_list' or \
                       key == 'offset_list':
                        f.write("{:}='{:}'\n".format(key,self.parameters[key+'RAW']))
                    elif key == 'pn_limit' or key == 'gromacs_energy_kw' or \
                         key == 'literature_value':
                        f.write("{:}='{:}'\n".format(key,self.parameters[key]))
                    else:
                        f.write('{:}={:}\n'.format(key,self.parameters[key]))
            f.write('\n\n\n')
            f.write(self._shfile)
                
        print('Note: the file < {:} > has been generated, '.format(pf))
        print('    : which can be directly executed for auto-training')
        

