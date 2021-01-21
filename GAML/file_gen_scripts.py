"""Get pre-defined script files
"""
from GAML.functions import file_gen_new
import os
import shutil
from pkg_resources import resource_listdir, resource_filename


class File_gen_scripts:
    def __init__(self,*args,**kwargs):
        self.n = None
        if 'number' in kwargs and kwargs['number'] is not None:
            try:
                self.n = int(float(kwargs['number']))
            except ValueError:
                self.available = True
                print('Error: wrong choose')

        self.files = resource_listdir(__name__,'scripts/')
        # remove python cache folder
        if '__pycache__' in self.files: self.files.remove('__pycache__')

        self.available = True
        if self.n is not None and self.n <= len(files): self.available = False



    def run(self):
        """get built-in script file"""
        details = {
            'bash_analysesDES.sh'   : 'For DES result analyses',
            'bash_DES.sh'           : 'For DES training',
            'bash_GAML.sh'          : 'For conventional solvents training',
            'bash_genTopfiles.sh'   : 'For GROMACS topology file generations',
            'bash_rmfilesIndividual.sh': 'For folder cleanup',
            'bash_visAdd.sh'        : 'For viscosity property training',
            'bash_visAnalysisByFolder.sh': 'For viscosity property analyzing',
            'GAML-BASH-Interface.sh': 'For command GAML_autotrain',
            'py_bool_repeatsChk.py' : 'For charge pair repeats check out',
        }

        if self.available:
            print('Available scripts:')
            for cnt,f in enumerate(self.files):
                if f in details:
                    print('  {:2d} --> {:<30} {:}'.format(cnt+1,f,details[f]))
                else:
                    print('  {:2d} --> {:}'.format(cnt+1,f))
            print('\nWhich scripts do you want to get?')
            print('Please input its number. (Input q/quit to quit)')
            while True:
                tmp = input()
                if tmp.lower() in ['q','quit']: break
                try:
                    self.n = int(float(tmp))
                    if self.n <= 0:
                        self.n = None
                        raise ValueError
                except ValueError:
                    pass
                if isinstance(self.n,int) and self.n <= len(self.files):
                    self.available = False
                    break
                else:
                    print('Wrong choose. (Input q/quit to quit)')

        if self.available:
            print('You decided to quit..')
        else:
            cwd = os.getcwd()
            fname = self.files[self.n-1]
            fp = resource_filename(__name__,'scripts/'+fname)
            if os.path.isfile(fp):
                fname = file_gen_new(fname)
                print('Note: script file: < {:} >'.format(fname))
                shutil.copy(fp,cwd+'/'+fname)



    def file_print(self):
        """place holder"""
        pass



