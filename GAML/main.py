from GAML.functions import file_size_check
from GAML.charge_gen_range import Charge_gen_range
from GAML.charge_gen_scheme import Charge_gen_scheme
from GAML.file_gen_gaussian import File_gen_gaussian
from GAML.file_gen_gromacstop import File_gen_gromacstop
from GAML.GAML_main import GAML_main
from GAML.file_gen_mdpotential import File_gen_mdpotential
from GAML.GAML_autotrain import GAML_autotrain
from GAML.fss_analysis import FSS_analysis
from GAML.__init__ import __version__

import sys
from sys import exit
import argparse


# The collection of all the parameters and their default settings
# The string MUST is used as the place holder, which means the parameter is required

par_GAML = {'command'           :   'GAML',
            'charge_path'       :   None,
            'file_path'         :   None,
            'symmetry_list'     :   None,
            'offset_list'       :   None,
            'counter_list'      :   None,
            'error_tolerance'   :   0.12,
            'bool_abscomp'      :   True,
            'cut_keyword'       :   'MAE',
            'charge_extend_by'  :   0.3,
            'gennm'             :   20,
            'offset_nm'         :   5,
            'nmround'           :   2,
            'total_charge'      :   1.0,
            'bool_neutral'      :   True,
            'bool_nozero'       :   True,
            'pn_limit'          :   None,
            'threshold'         :   1.0,
            'ratio'             :   '0.7:0.2:0.1',  #ML:AV:MU
            'fname'             :   'ChargeRandomGen',
            }

par_charge_gen_scheme = {'command'        :   'charge_gen_scheme',
                         'charge_path'    :   None,
                         'symmetry_list'  :   None,
                         'counter_list'   :   None,
                         'offset_list'    :   None,
                         'gennm'          :   5,
                         'nmround'        :   2,
                         'total_charge'   :   0.0,
                         'fname'          :   'ChargeRandomGen',
                         'in_keyword'     :   'ATOM',
                         'bool_neutral'   :   True,
                         'bool_nozero'    :   True,
                         'pn_limit'       :   None,
                         'threshold'      :   1.0,
                         'offset_nm'      :   5,
                         }

par_charge_gen_range = {'command'      :   'charge_gen_range',
                        'charge_path'  :   'MUST',
                        'atomnm'       :   'MUST',
                        'percent'      :    0.8,
                        'stepsize'     :    0.01,
                        'nmround'      :    3,
                        'fname'        :    'ChargeGenRange',
                        }


par_file_gen_gaussian = {'command'      :   'file_gen_gaussian',
                         'toppath'      :   'MUST',
                         'file_path'    :   'MUST',
                         'select_range' :   10,
                         'gennm'        :   5,
                         'basis_set'    :   '# HF/6-31G(d) Pop=CHelpG',
                         'charge_spin'  :   '0 1',
                         'fname'        :   'GaussInput',
                         }


par_file_gen_gromacstop = {'command'        :   'file_gen_gromacstop',
                           'toppath'        :   'MUST',
                           'charge_path'    :   'MUST',
                           'symmetry_list'  :   None,
                           'reschoose'      :   'ALL',
                           'in_keyword'     :   'PAIR',
                           'cut_keyword'    :   'MAE',
                           'gennm'          :   None,
                           'fname'          :   'GenGromacsTopfile',
                           }

par_fss_analysis = {'command'          :     'fss_analysis',
                    'file_path'        :     'MUST',
                    'atomtype_list'    :     'None',
                    'stepsize'         :     0.01,
                    'error_tolerance'  :     0.28,
                    'bool_abscomp'     :     True,
                    'percent'          :     0.95,
                    'cut_keyword'      :     'MAE',
                    'pallette_nm'      :     50,
                    'color_map'        :    'rainbow',
                    'fname'            :    'FSS_analysis',
                    }

#Note: this method is not loaded to settingfile
par_GAML_autotrain = {'command'       :  'GAML_autotrain',
                     }

#Note: this method is not loaded to settingfile
par_file_gen_mdpotential = {'command' :  'file_gen_mdpotential',
                           }

# For double check and validation
# this list should be updated if any future modification happen.

parname_list = [    par_charge_gen_scheme,
                    par_charge_gen_range,
                    par_GAML,
                    par_file_gen_gromacstop,
                    par_file_gen_gaussian,
                    par_fss_analysis,       
                    par_GAML_autotrain,
                    par_file_gen_mdpotential,
]


par_cmdlist = [ddict['command'].lower() for ddict in parname_list]


#
# Now, the legendary of main code part
#

def sub_eval(string):
    """This method is exclusively designed to evaluate python reserverd word
       In here, they are, None, False and True"""

    if string.lower() == 'true':
        string = True
    elif string.lower() == 'false':
        string = False
    elif string.lower() == 'none':
        string = None

    return string



def pro_settingfile(settingfile):
    """Process the input settingfile"""

    def f_remove_comment(string):
        if string.find('#') == -1:
            return string.strip()
        return string[:string.find('#')]

    log = file_size_check(settingfile,fsize=5)
    if not log['nice']:
        print(log['info'])
        exit()
    
    # this universal string is used to exit prompt
    error_info = 'Error: the input setting file is wrong'

    infile = []
    with open(settingfile,mode='rt') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            else:
                lt = line.split()
                if len(lt) == 0 or lt[0] == '#' or (len(lt[0]) > 1 and lt[0][0] == '#'):
                    continue
                else:
                    if line.find('=') == -1:
                        print(error_info)
                        print('Error line: ',line)
                        exit()
                    else:
                        lp = line.split('=',maxsplit=1)
                        partmp = lp[0].split()
                        if len(partmp) != 1:
                            print(error_info)
                            print('Error line: ',line)
                            exit()
                            
                        parname = partmp[0].lower()

                        ls = []
                        ls.append(parname)

                        # take care of 'basis_set' comment exception
                        if parname != 'basis_set':
                            
                            # take care of python representation string list to real python list
                            if parname == 'symmetry_list' or parname == 'counter_list' or \
                                 parname == 'offset_list' or parname == 'atomtype_list':
                                stmp = f_remove_comment(lp[1])
                                if len(stmp.split()) == 0:
                                    ls.append(None)
                                else:
                                    try:
                                        s = eval(stmp)
                                    except:
                                        print('Error: the wrong defined python representation parameter')
                                        print('Error line: ',line)
                                        exit()
                                    ls.append(s)

                            # take care of charge_spin exception
                            elif parname == 'charge_spin':
                                stmp = f_remove_comment(lp[1])
                                lr = stmp.split()
                                if len(lr) == 0:
                                    ls.append('0 1')
                                elif len(lr) == 2:
                                    ls.append( lr[0] + ' ' + lr[1] )
                                else:
                                    print('Error: the wrong definition of charge_spin parameter')
                                    print('Error line: ',line)
                                    exit()
                                    
                            # take care of pn_limit exception
                            elif parname == 'pn_limit':
                                stmp = f_remove_comment(lp[1])
                                if len(stmp.split()) == 0:
                                    ls.append(None)
                                else:
                                    ls.append(stmp)
      
                            else:
                                stmp = f_remove_comment(lp[1])
                                lr = stmp.split()
                                if len(lr) == 0:
                                    ls.append(None)
                                elif len(lr) == 1:
                                    ls.append(sub_eval(lr[0]))
                                else:
                                    print(error_info)
                                    print('Error line: ',line)
                                    exit()
                        else:
                            ndx_first = lp[1].find('#') 
                            if ndx_first == -1:
                                ltmp = ''
                                for i in lp[1].split():
                                    ltmp += i + ' '
                                ls.append(ltmp)
                            elif ndx_first == len(lp[1]):
                                ls.append('#')
                            else:
                                ndx_second = lp[1][ndx_first+1:].find('#')
                                if ndx_second == -1:
                                    ltmp = ''
                                    for i in lp[1].split():
                                        ltmp += i + ' '
                                    ls.append(ltmp)
                                else:
                                    ltmp = ''
                                    for i in lp[1][:ndx_first+ndx_second+1].split():
                                        ltmp += i + ' '
                                    ls.append(ltmp)
                        infile.append(ls)


    # process the infile to different blocks
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
        print('Error: no command is found')
        exit()

        
    # process the command
    prodict = []
    for i in profile:
        
        # check the command
        cmd = i[0][1].lower() 
        if not (cmd in par_cmdlist):
            print('Error: the command < {:} > is not defined'.format(i[0][1]))
            exit()

        # ATTENTION! Because of the python 'functionality', here it is very important
        # to force python to make a new memory copy of list or dict 'reference'
        # to avoid any 'same-memory-reference' allocating

        for par in parname_list:
            if par['command'].lower() == cmd:
                break
        fgetdict = { **par }


        parlist = [j for j,s in fgetdict.items()]
        for name in i:
            if not name[0] in parlist:
                print('Error: the parameter is not defined')
                print('     : In command < {:} >'.format(fgetdict['command']))
                print('Error parameter: ',name[0])
                exit()
            else:
                fgetdict[name[0]] = name[1]
        
        prodict.append(fgetdict)

    return prodict



def pro_argparse():
    
    parser = argparse.ArgumentParser(description='Genetic Algorithm Machine Learning',allow_abbrev=False)
    parser.add_argument('-v','--version',action='version',version='GAML Package '+__version__)
    subparser = parser.add_subparsers()

    
    sub_1 = subparser.add_parser('charge_gen_range',help='To generate charge range based on input files')
    sub_1.set_defaults(command='charge_gen_range') 
    sub_1.add_argument('-f','--charge_path',help='input charge file path',required=True)
    sub_1.add_argument('-i','--atomnm',help='the total atom numbers of single system',required=True)
    sub_1.add_argument('-p','--percent',help='range from 0.0 ~ 1.0, default is 0.8')
    sub_1.add_argument('-t','--stepsize',help='default is 0.01')
    sub_1.add_argument('-nr','--nmround',help='decimal round number, positive integer, default is 3')
    sub_1.add_argument('-o','--fname',help='output file name, default is ChargeGenRange')

    
    sub_2 = subparser.add_parser('charge_gen_scheme',help='To generate charge scheme based on input charge-range')
    sub_2.set_defaults(command='charge_gen_scheme')
    sub_2.add_argument('-f','--charge_path',help='the input charge file',required=True)
    sub_2.add_argument('-sl','--symmetry_list',nargs='+', help='symmetry_list, a list contains chemical equivalent information \
                        of the system, default is None')
    sub_2.add_argument('-ol','--offset_list',nargs='+',help='the two offsets in it have to be uniquely and properly defined, \
                        default is None')
    sub_2.add_argument('--offset_nm',nargs='+',help='the attemption numbers to generate charge falling within input charge range, \
                        it is used to fit charge constrains, it is valid only when symmetry_list is defined, default is 5')
    sub_2.add_argument('-cl','--counter_list',nargs='+',help='counter_list,a list showing the sum of the group is zero')
    sub_2.add_argument('-nu','--bool_neutral',help='bool, force the final calculated value scaled from 1 or not, default is False')
    sub_2.add_argument('-nz','--bool_nozero',help='bool, do not allow 0 exist in the final result or not, default is True')
    sub_2.add_argument('-q','--pn_limit',nargs='+',help='bool, to define the value range, whether positive or negative, default is None')
    sub_2.add_argument('-nm','--gennm',help='output file numbers, default is 5. This number is always no \
                        bigger than the input file frames')
    sub_2.add_argument('-nr','--nmround',help='decimal round number, positive integer, default is 2')
    sub_2.add_argument('-tc','--total_charge',help='default is 1.0')
    sub_2.add_argument('-b','--in_keyword',help='the mark of the start in the input file')
    sub_2.add_argument('-o','--fname',help='output file name, default is ChargeRandomGen')
    sub_2.add_argument('-lim','--threshold',help='positive number, set the limit for each entries value, default is 1.0')

    
    sub_3 = subparser.add_parser('file_gen_gaussian',help='To generate gaussian_input file in selected range')
    sub_3.set_defaults(command='file_gen_gaussian')
    sub_3.add_argument('-ftop','--toppath',help='gromacs top file, inside [atomtypes] directives, every entry must have atomtype \
                       defined using a \'-\' conjunct ',required=True)
    sub_3.add_argument('-f','--file_path',help='gromacs type pdb or gro file',required=True)
    sub_3.add_argument('-nm','--gennm',help='output file numbers, default is 5, This number is always no bigger than the final \
                        processed frames')
    sub_3.add_argument('-sr','--select_range',help='default is 10')
    sub_3.add_argument('-o','--fname',help='output file name, default is GaussInput')
    sub_3.add_argument('-bs','--basis_set',nargs='+', help='the basis_set, default is [ # HF/6-31G(d) Pop=CHelpG ]. Its format \
                        has to be gaussian input format')
    sub_3.add_argument('-cs','--charge_spin',nargs='+',help='the charge_spin, default is [ 0 1 ]. Its format has to be gaussian \
                        input format')
    

    sub_4 = subparser.add_parser('file_gen_gromacstop',help='To generate gromacs top file')
    sub_4.set_defaults(command='file_gen_gromacstop')
    sub_4.add_argument('-ftop','--toppath',help='the template of gromacs top file',required=True)
    sub_4.add_argument('-f','--charge_path',help='the input charge file',required=True)
    sub_4.add_argument('-sl','--symmetry_list',nargs='+', help='symmetry_list, the two offsets in it have to be \
                        uniquely and properly defined, default is None')
    sub_4.add_argument('-nm','--gennm',help='output file numbers, default is all, This number is always no bigger than the final \
                        processed frames')
    sub_4.add_argument('-res','--reschoose',help='default is all, it has to be corresponded with the symmetry_list')
    sub_4.add_argument('-b','--in_keyword',help='the mark of the start in the input file, default is PAIR')
    sub_4.add_argument('-e','--cut_keyword',help='the mark of the end in the input file, default is MAE')
    sub_4.add_argument('-o','--fname',help='output file name, default is GenGromacsTopfile')


    sub_5 = subparser.add_parser('GAML',help='To start GAML')
    sub_5.set_defaults(command='gaml')
    sub_5.add_argument('-f','--file_path',help='the input total MD file, default is None')
    sub_5.add_argument('-fc','--charge_path',help='the input charge range file, default is None')
    sub_5.add_argument('-sl','--symmetry_list',nargs='+', help='symmetry_list, a list contains chemical equivalent information \
                        of the system, default is None')
    sub_5.add_argument('-ol','--offset_list',nargs='+',help='the two offsets in it have to be uniquely and properly defined, \
                        default is None')
    sub_5.add_argument('--offset_nm',nargs='+',help='the attemption numbers to generate charge falling within input charge range, \
                        it is used to fit charge constrains, it is valid only when symmetry_list is defined, default is 5')
    sub_5.add_argument('-cl','--counter_list',nargs='+',help='counter_list,a list showing the sum of the group is zero')
    sub_5.add_argument('-nu','--bool_neutral',help='bool, force the final calculated value scaled from 1 or not, default is False')
    sub_5.add_argument('-nz','--bool_nozero',help='bool, do not allow 0 exist in the final result or not, default is True')
    sub_5.add_argument('-q','--pn_limit',nargs='+',help='bool, to define the value range, whether positive or negative, default is None')
    sub_5.add_argument('-lim','--threshold',help='positive number, set the limit for each entries value, default is 1.0')
    sub_5.add_argument('-nm','--gennm',help='output file numbers, default is 5, This number is always no bigger than the final \
                        processed frames')
    sub_5.add_argument('-ro','--ratio',help='Ratio among Cross-over to Average to Mutation. The number of pair generations of \
                        normal charge range is always equal to number of modified charge range, default is 0.7:0.2:0.1',nargs='+')
    sub_5.add_argument('-d','--error_tolerance',help='default is 0.8')
    sub_5.add_argument('-nr','--nmround',help='decimal round number, positive integer, default is 2')
    sub_5.add_argument('-abs','--bool_abscomp',help='default is False, use the absolute value or not')
    sub_5.add_argument('-ex','--charge_extend_by',help='default is 0.3, used to change the charge range bound')
    sub_5.add_argument('-e','--cut_keyword',help='the mark of the end in the input file, default is MAE')
    sub_5.add_argument('-tc','--total_charge',help='default is 1.0')
    sub_5.add_argument('-o','--fname',help='output file name, default is ChargeRandomGen')


    sub_6 = subparser.add_parser('fss_analysis',help='To start Feature Statistical Selection Analysis')
    sub_6.set_defaults(command='fss_analysis')
    sub_6.add_argument('-f','--file_path',help='the input analyzing file',required=True)
    sub_6.add_argument('-t','--stepsize',help='default is 0.01')
    sub_6.add_argument('-d','--error_tolerance',help='default is 0.28')
    sub_6.add_argument('-abs','--bool_abscomp',help='default is False, use the absolute value or not')
    sub_6.add_argument('-p','--percent',help='range from 0.0 ~ 1.0, default is 0.95')
    sub_6.add_argument('-e','--cut_keyword',help='the mark of the end in the input file, default is MAE')
    sub_6.add_argument('-tl','--atomtype_list',help='correspondent atom types, note the character \'#\' is not supported',nargs='+')
    sub_6.add_argument('-pn','--pallette_nm',help='number of pallettes used to plot the graph, default is 50')
    sub_6.add_argument('-cm','--color_map',help='this is a key word compatible with Matplotlib modules, default is rainbow')
    sub_6.add_argument('-o','--fname',help='output file name, default is FSS_analysis')

    sub_7 = subparser.add_parser('file_gen_mdpotential', help='Command to use GAML auto-training')
    sub_7.set_defaults(command='file_gen_mdpotential')
    sub_7.add_argument('-f','--file_path',help='MD simulation result file',required=True)
    sub_7.add_argument('-i','--atomnm',help='the total number of atoms in single system, default is 500')
    sub_7.add_argument('-o','--fname',help='output file name, default is MAE_PAIR')
    sub_7.add_argument('--MAE',help='mean-absolute-value, default is 0.05')
    sub_7.add_argument('--temperature',help='Unit in Kelvin')
    sub_7.add_argument('-s','--chargefile',help='input charge file',required=True)
    sub_7.add_argument('--block',help='mark for file process, default is COUNT')
    sub_7.add_argument('-lv','--literature_value',help='corresponded values, number',nargs='+',required=True)
    sub_7.add_argument('--bool_gas',help='Exclusive for Heat-of-vaporization, gas phase calculation, default is False')
    sub_7.add_argument('-kw','--kwlist',help='MD result key-word list, default is Density',nargs='+')

    sub_8 = subparser.add_parser('GAML_autotrain', help='To generate auto-training bash file')
    sub_8.set_defaults(command='gaml_autotrain')
    sub_8.add_argument('-f','--file_path',help='Auto training parameters all-in-one file',required=True)
    sub_8.add_argument('--bashinterfile',help='A bash interface file to be used to override default outputs')

    args = parser.parse_args()

    if not vars(args):
        parser.print_help()
        exit()

    fgetdict = {**vars(args)}


    if ('symmetry_list' in fgetdict) and (fgetdict['symmetry_list'] is not None):
        try:
            fgetdict['symmetry_list'] = eval(*fgetdict['symmetry_list'])
        except:
            print('Error: the parameter symmetry_list is wrong')
            print(fgetdict['symmetry_list'])
            exit()       

    if ('counter_list' in fgetdict) and (fgetdict['counter_list'] is not None):
        try:
            fgetdict['counter_list'] = eval(*fgetdict['counter_list'])
        except:
            print('Error: the parameter counter_list is wrong')
            print(fgetdict['counter_list'])
            exit() 

    if ('offset_list' in fgetdict) and (fgetdict['offset_list'] is not None):
        try:
            fgetdict['offset_list'] = eval(*fgetdict['offset_list'])
        except:
            print('Error: the parameter offset_list is wrong')
            print(fgetdict['offset_list'])
            exit()

    if ('atomtype_list' in fgetdict) and (fgetdict['atomtype_list'] is not None):
        line = ''
        for i in fgetdict['atomtype_list']: line += i
        stmp = line.replace(',',' ').replace('[','[ ').replace(']',' ]').strip()
        stmp = stmp.replace('"',' ').replace("'",' ').replace(';',' ')
        bo = False
        if len(stmp) < 4:
            bo = True
        elif len(stmp) == 4:
            if stmp[0] == '[' and stmp[-1] == ']':
                fgetdict['atomtype_list'] = None
            else:
                bo = True
        else:
            if stmp[0] == '[' and stmp[-1] == ']':
                stmp = stmp.replace('[',' ').replace(']',' ')
                fgetdict['atomtype_list'] = stmp.split()
            else:
                bo = True

        if bo:
            print('Error: the parameter atomtype_list is wrong')
            print(fgetdict['atomtype_list'])
            exit() 

    return fgetdict



def cmd_run(fdict):
    """This is the combined method to actually run the command, which by default assumes the input directory
       has been properly processed. For any future update, this method should also be updated."""

    cmd = fdict['command'].lower()
    if  cmd in ['charge_gen_range','charge_gen_scheme','file_gen_gromacstop','gaml']:
        if cmd == 'charge_gen_range':
            fp = Charge_gen_range(**fdict)
        elif cmd == 'charge_gen_scheme':
            fp = Charge_gen_scheme(**fdict)
        elif cmd == 'file_gen_gromacstop':
            fp = File_gen_gromacstop(**fdict)
        else:
            fp = GAML_main(**fdict)
        if fp.log['nice']: fp.run()
    elif cmd == 'file_gen_gaussian':
        fp = File_gen_gaussian(**fdict)
    elif cmd == 'fss_analysis':
        fp = FSS_analysis(**fdict)
    elif fdict['command'].lower() == 'file_gen_mdpotential':
        fp = File_gen_mdpotential(**fdict)
    elif fdict['command'].lower() == 'gaml_autotrain':
        fp = GAML_autotrain(**fdict)
    else:
        # Normally, this information will never be output. However, it is still defined
        print('Error: no command is executed')
        exit()
    
    if fp.log['nice']:
        fp.file_print()
    else:
        print(fp.log['info'])
        exit()


def run(fdict):
    """By default, the fdict either can be a list which contains many dictionaries, or a dictionary"""
    
    if isinstance(fdict,list):
        for i in fdict: cmd_run(i)
    else:
        cmd_run(fdict)


def cmd_line_runner():

    if len(sys.argv) == 1:
        print('\nGAML package, either can be input using the command line or using the setting file.')
        print('For more information, please refer the sample directory\n\n')
        print('Option 1, use the setting file:\n')
        print('python GAML_package.py settingfile\n\n')
        print('Option 2, use the command line: \n')
        dump_value = pro_argparse()
    else:
        if sys.argv[1].lower() in ['-v','--version','-h','--help',*par_cmdlist]:
            fdict = pro_argparse()
        else:
            fdict = pro_settingfile(sys.argv[1])
            
        run(fdict)

if __name__ == '__main__':
    cmd_line_runner()


