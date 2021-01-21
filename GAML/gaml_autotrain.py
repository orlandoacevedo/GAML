from GAML.functions import file_size_check, file_gen_new
from GAML.file_gen_gromacstop import File_gen_gromacstop
from GAML.charge_gen_scheme import Charge_gen_scheme

import os
import shutil
from pkg_resources import resource_string


class GAML_autotrain(object):
    def __init__(self,*args,**kwargs):
        if 'file_path' not in kwargs or kwargs['file_path'] is None:
            raise ValueError('no inputs, file_path is missing')
        self.file = kwargs['file_path'].strip()
        file_size_check(self.file,fsize=2)

        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname'].strip()
            if len(self.fname) == 0: self.fname = 'bash_GAML_AutoTraining'
        else:
            self.fname = 'bash_GAML_AutoTraining'

        self.parameters = {
            'top_gas_path'              :   None,
            'top_liq_path'              :   None,
            'top_fep_path'              :   None,
            'gro_gas_path'              :   None,
            'gro_liq_path'              :   None,
            'gro_fep_path'              :   None,
            'grompp_min_gas_path'       :   None,
            'grompp_min_liq_path'       :   None,
            'grompp_nvt_liq_path'       :   None,
            'grompp_npt_liq_path'       :   None,
            'grompp_prod_gas_path'      :   None,
            'grompp_prod_liq_path'      :   None,
            'grompp_fep_min_steep_path' :   None,
            'grompp_fep_min_lbfgs_path' :   None,
            'grompp_fep_nvt_path'       :   None,
            'grompp_fep_npt_path'       :   None,
            'grompp_fep_prod_path'      :   None,
            'charge_range_path'         :   None,
            'gromacs_energy_kw'         :   'Density',
            'literature_value'          :   1000,
            'gmx'                       :   'gmx',
            'MAE'                       :   0.05,
            'training_total_nm'         :   5,
            'training_cnt'              :   1,
            'gennm'                     :   10,
            'error_tolerance'           :   0.5,
            'symmetry_list'             :   None,
            'pn_limit'                  :   None,
            'counter_list'              :   None,
            'offset_list'               :   None,
            'offset_nm'                 :   None,
            'ratio'                     :   None,
            'nmround'                   :   None,
            'total_charge'              :   0.0,
            'charge_extend_by'          :   None,
            'threshold'                 :   None,
            'bool_neutral'              :   None,
            'bool_nozero'               :   None,
            'bool_abscomp'              :   None,
            'reschoose'                 :   None,
            'analysis_begintime'        :   None,
            'analysis_endtime'          :   None,
        }


        # check for the bash scripts
        bo = True
        if 'bashinterfile' in kwargs and kwargs['bashinterfile'] is not None:
            self.bashinterfile = kwargs['bashinterfile'].strip()
            if len(self.bashinterfile) == 0:
                self.bashinterfile = 'GAML-BASH-Interface.sh'
            else:
                bo = False
        else:
            self.bashinterfile = 'GAML-BASH-Interface.sh'
        
        if bo:
            self.shfile = resource_string(__name__,'scripts/'+self.bashinterfile).decode('utf-8').replace('\r','')
        else:
            file_size_check(self.bashinterfile,fsize=10)
            with open(self.bashinterfile,mode='rt') as f: self.shfile = f.read()


        self.profile()
        self.proparameters()
        self.trial()



    def run(self):
        """method place holder"""
        pass



    def profile(self):
        """Process input auto-settingfile"""
        errinfo = 'Error: wrong defined settingfile\n'
        parlist = [k for k in self.parameters]
        with open(self.file,mode='rt') as f:
            while True:
                line = f.readline()
                if len(line) == 0:
                    break

                sub = line if line.find('#') == -1 else line[:line.find('#')]
                sub = sub.strip()
                if len(sub) == 0: continue
                
                if sub.find('=') == -1:
                    print(errinfo + 'Error line: ' + line)
                    raise ValueError('wrong input')

                lp = sub.split('=',maxsplit=1)
                partmp = lp[0].split()
                if len(partmp) != 1:
                    print(errinfo + 'Error line: ' + line)
                    raise ValueError('wrong input')

                key = partmp[0].lower()
                if key not in parlist:
                    print(errinfo + 'Error line: ' + line)
                    raise ValueError('wrong input')

                stmp = lp[1]
                lt = stmp.split()
                if len(lt) != 0:
                    # take care of python representation string list to real python list
                    if key == 'symmetry_list' or key == 'counter_list' or key == 'offset_list':
                        try:
                            s = eval(stmp)
                        except:
                            print(errinfo + 'Error line: ' + line)
                            raise ValueError('wrong input') 
                        self.parameters[key] = s

                        # special case for bash print out
                        self.parameters[key + 'RAW'] = stmp.strip()
                    elif key == 'pn_limit' or key == 'gromacs_energy_kw' or key == 'literature_value':
                        self.parameters[key] = ' '.join(lt)
                    elif len(lt) != 1:
                        print(errinfo + 'Error line: ' + line)
                        raise ValueError('wrong input')
                    else:
                        self.parameters[key] = lt[0]



    def proparameters(self):
        cwd = os.getcwd()
        for par,name in self.parameters.items():
            if 'path' in par and name is not None:
                filepath = self.parameters[par]
                head,base = os.path.split(filepath)
                if os.path.isfile(filepath):
                    if os.path.islink(base) or (not os.path.isfile(base)):
                        shutil.copy(filepath,cwd)
                    self.parameters[par] = base
                else:
                    print('Error: cannot find the file ' + self.parameters[par])
                    raise ValueError('wrong defined')



    def trial(self):
        # Make a copy and add a key for Charge_gen_scheme
        pardir = { **self.parameters }
        pardir['charge_path'] = pardir['charge_range_path']

        tp = Charge_gen_scheme(**pardir)
        tp.run()

        pardir['charge_path'] = tp.chargepair
        pardir['toppath'] = pardir['top_liq_path']
        tp = File_gen_gromacstop(**pardir)
        tp.run()



    def file_print(self):
        pf = file_gen_new(self.fname,fextend='sh')
        with open(pf,mode='wt') as f:
            f.write('#!/bin/bash\n')
            f.write('# -*- coding: utf-8 -*-\n\n')
            for key in sorted(self.parameters):
                if 'RAW' in key:
                    pass
                elif self.parameters[key] is None:
                    f.write("{:}= \n".format(key))
                else:
                    if key == 'symmetry_list' or key == 'counter_list' or key == 'offset_list':
                        f.write("{:}='{:}'\n".format(key,self.parameters[key+'RAW']))
                    elif key == 'pn_limit' or key == 'gromacs_energy_kw' or key == 'literature_value':
                        f.write("{:}='{:}'\n".format(key,self.parameters[key]))
                    else:
                        f.write('{:}={:}\n'.format(key,self.parameters[key]))
            f.write('\n\n\n')
            f.write(self.shfile)

        print('Note: new file < {:} >'.format(pf))
        print('it can be directly executed for auto-training')



