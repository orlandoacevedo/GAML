"""Parse command line input

Returns:
    log (dict):
        nice    :   False means error happens
        info    :   Error message

    procmd (dict):
        { key:value, key:value,  ...}
"""

import sys
import argparse
from GAML.__init__ import __version__


def parsecmd(args):
    """Parse command line input"""

    def text2list(value):
        if value is None or len(value) == 0:
            return None
        value = value.strip()
        if value[0] != '[': value = '[' + value
        if value[-1] != ']': value = value + ']'
        try:
            value = eval(value)
        except:
            value = False
        return value


    log = {'nice': True, 'info': ''}
    parser = argparse.ArgumentParser(description='Genetic Algorithm Machine Learning',allow_abbrev=False)
    parser.add_argument('-v','--version',action='version',version='GAML '+__version__)
    subparser = parser.add_subparsers()


    sub_1 = subparser.add_parser('charge_gen_range',help='Generate charge range based on input file')
    sub_1.set_defaults(command='charge_gen_range')
    sub_1.add_argument('-f','--charge_path',help='Input charge range file')
    sub_1.add_argument('-i','--atomnm',help='Total number of atoms in single system')
    sub_1.add_argument('-p','--percent',help='Range from 0.0 ~ 1.0, default is 0.8')
    sub_1.add_argument('-t','--stepsize',help='Default is 0.01')
    sub_1.add_argument('-nr','--nmround',help='Decimal round number, positive integer, default is 3')
    sub_1.add_argument('-o','--fname',help='Output file name, default is ChargeRange')


    sub_2 = subparser.add_parser('charge_gen_scheme',help='Generate charge scheme based on input charge-range')
    sub_2.set_defaults(command='charge_gen_scheme')
    sub_2.add_argument('-f','--charge_path',help='Input charge file')
    sub_2.add_argument('-sl','--symmetry_list',nargs='+', help='List contains chemical equivalent \
                        information of the system')
    sub_2.add_argument('-ol','--offset_list',nargs='+',help='Strong & weak offsets, maximum 2 values can be accepted')
    sub_2.add_argument('--offset_nm',nargs='+',help='Number of attemptions to generate charge falling within input \
                        charge range, used to fit charge constrains, valid only when symmetry_list is defined, \
                        default is 5')
    sub_2.add_argument('-cl','--counter_list',nargs='+',help='Summary of each defined group is zero')
    sub_2.add_argument('-nu','--bool_neutral',help='Boolean, force final calculated value scaled from 1',action='store_true')
    sub_2.add_argument('-nz','--bool_nozero',help='Boolean, filter out zero in results, default is True',action='store_true')
    sub_2.add_argument('-q','--pn_limit',nargs='+',help='Define whether value is positive or negative')
    sub_2.add_argument('-nm','--gennm',help='Output pair numbers, default is 5. This number is always no \
                        bigger than the input file frames')
    sub_2.add_argument('-nr','--nmround',help='Decimal round number, positive integer, default is 2')
    sub_2.add_argument('-tc','--total_charge',help='Default is 1.0')
    sub_2.add_argument('-b','--in_keyword',help='The mark of the start in the input file, default is ATOM')
    sub_2.add_argument('-lim','--threshold',help='Threshold for all values, positive number, default is 1.0')
    sub_2.add_argument('-o','--fname',help='Output file name, default is ChargePair')


    sub_3 = subparser.add_parser('file_gen_gaussian',help='Generate gaussian input file in selected range')
    sub_3.set_defaults(command='file_gen_gaussian')
    sub_3.add_argument('-ftop','--toppath',help='Gromacs top file, inside [atomtypes] directives, \
                        each entry must have atomtype defined using a \'-\' conjunct ')
    sub_3.add_argument('-f','--file_path',help='Gromacs type pdb or gro file')
    sub_3.add_argument('-nm','--gennm',help='Output file numbers, default is 5, This number is always no \
                        bigger than the input processed frames')
    sub_3.add_argument('-sr','--select_range',help='Default is 10')
    sub_3.add_argument('-bs','--basis_set',nargs='+', help='Default is [ # HF/6-31G(d) Pop=CHelpG ]')
    sub_3.add_argument('-cs','--charge_spin',nargs='+',help='Default is [ 0 1 ]')
    sub_3.add_argument('-o','--fname',help='Output file name, default is GaussInput')


    sub_4 = subparser.add_parser('file_gen_gromacstop',help='Generate gromacs top file')
    sub_4.set_defaults(command='file_gen_gromacstop')
    sub_4.add_argument('-ftop','--toppath',help='Template of gromacs top file')
    sub_4.add_argument('-f','--charge_path',help='Input charge file')
    sub_4.add_argument('-sl','--symmetry_list',nargs='+', help='List contains chemical equivalent \
                        information of the system')
    sub_4.add_argument('-nm','--gennm',help='Output file numbers, default is 5, This number is always no \
                        bigger than the input processed frames')
    sub_4.add_argument('-res','--reschoose',help='Residue needs to be processed, default is ALL')
    sub_4.add_argument('-b','--in_keyword',help='The mark of the start in the input file, default is PAIR')
    sub_4.add_argument('-e','--cut_keyword',help='The mark of the end in the input file')
    sub_4.add_argument('-o','--fname',help='Output file name, default is GromacsTopfile')


    sub_5 = subparser.add_parser('GAML',help='Start GAML')
    sub_5.set_defaults(command='gaml')
    sub_5.add_argument('-f','--file_path',help='Input training file')
    sub_5.add_argument('-fc','--charge_path',help='Input charge file')
    sub_5.add_argument('-sl','--symmetry_list',nargs='+', help='List contains chemical equivalent \
                        information of the system')
    sub_5.add_argument('-ol','--offset_list',nargs='+',help='Strong & weak offsets, maximum 2 values can be accepted')
    sub_5.add_argument('--offset_nm',nargs='+',help='Number of attemptions to generate charge falling within input \
                        charge range, used to fit charge constrains, valid only when symmetry_list is defined, \
                        default is 5')
    sub_5.add_argument('-cl','--counter_list',nargs='+',help='Summary of each defined group is zero')
    sub_5.add_argument('-nu','--bool_neutral',help='Boolean, force final calculated value scaled from 1',action='store_true')
    sub_5.add_argument('-nz','--bool_nozero',help='Boolean, filter out zero in results, default is True',action='store_true')
    sub_5.add_argument('-q','--pn_limit',nargs='+',help='Define whether value is positive or negative')
    sub_5.add_argument('-nm','--gennm',help='Output pair numbers, default is 5. This number is always no \
                        bigger than the input file frames')
    sub_5.add_argument('-nr','--nmround',help='Decimal round number, positive integer, default is 2')
    sub_5.add_argument('-lim','--threshold',help='Threshold for all values, positive number, default is 1.0')
    sub_5.add_argument('-ro','--ratio',help='Ratio among Cross-over : Average : Mutation. The number of pairs \
                        of normal charge range is equal to number of modified charge range. \
                        Default is 0.7:0.2:0.1',nargs='+')
    sub_5.add_argument('-d','--error_tolerance',help='Default is 0.8')
    sub_5.add_argument('-abs','--bool_abscomp',help='Boolean, use absolute values',action='store_true')
    sub_5.add_argument('-ex','--charge_extend_by',help='Default is 0.3, extend charge range bound')
    sub_5.add_argument('-e','--cut_keyword',help='The mark of the end in the input file')
    sub_5.add_argument('-tc','--total_charge',help='Total charge constrain, default is 0.0')
    sub_5.add_argument('-o','--fname',help='Output file name, default is ChargeGen')


    sub_6 = subparser.add_parser('fss_analysis',help='Start Feature Statistical Selection Analysis')
    sub_6.set_defaults(command='fss_analysis')
    sub_6.add_argument('-f','--file_path',help='Input analyzing file')
    sub_6.add_argument('-t','--stepsize',help='Default is 0.01')
    sub_6.add_argument('-d','--error_tolerance',help='Default is 0.28')
    sub_6.add_argument('-abs','--bool_abscomp',help='Boolean, use absolute values',action='store_true')
    sub_6.add_argument('-p','--percent',help='Range from 0.0 ~ 1.0, default is 0.95')
    sub_6.add_argument('-e','--cut_keyword',help='The mark of the end in the input file')
    sub_6.add_argument('-tl','--atomtype_list',help='Corresponding atom type of symmetry_list. \
                        Note the character \'#\' is not supported',nargs='+')
    sub_6.add_argument('-pn','--pallette_nm',help='Number of pallettes to plot graph, default is 50')
    sub_6.add_argument('-cm','--color_map',help='Compatible with Matplotlib, default is rainbow')
    sub_6.add_argument('-o','--fname',help='Output file name, default is FSSPlot')


    sub_7 = subparser.add_parser('file_gen_mdpotential', help='GAML auto-training')
    sub_7.set_defaults(command='file_gen_mdpotential')
    sub_7.add_argument('-f','--file_path',help='MD simulation result file')
    sub_7.add_argument('-s','--chargefile',help='Input charge file')
    sub_7.add_argument('-lv','--literature_value',help='Literature value',nargs='+')
    sub_7.add_argument('-i','--atomnm',help='Total number of molecules in liquid phase, default is 500')
    sub_7.add_argument('--MAE',help='Mean-absolute-value, default is 0.05')
    sub_7.add_argument('--temperature',help='Unit in Kelvin')
    sub_7.add_argument('--block',help='Mark for file process, default is COUNT')
    sub_7.add_argument('--bool_gas',help='Gas phase calculation, default is False',action='store_false')
    sub_7.add_argument('-kw','--kwlist',help='MD result keyword list, default is Density',nargs='+')
    sub_7.add_argument('-o','--fname',help='Output file name, default is MDProcess')


    sub_8 = subparser.add_parser('GAML_autotrain', help='To generate auto-training bash file')
    sub_8.set_defaults(command='gaml_autotrain')
    sub_8.add_argument('-f','--file_path',help='Auto training parameters all-in-one file')
    sub_8.add_argument('--bashinterfile',help='Input Bash interface file')

    args = parser.parse_args(args)

    if not vars(args):
        parser.print_help()
        sys.exit()

    procmd = {**vars(args)}

    if 'symmetry_list' in procmd:
        procmd['symmetry_list'] = text2list(procmd['symmetry_list'])
        log['nice'] = False
        log['info'] = 'Error: the parameter symmetry_list is wrong'

    if 'counter_list' in procmd:
        procmd['counter_list'] = text2list(procmd['counter_list'])
        log['nice'] = False
        log['info'] = 'Error: the parameter counter_list is wrong'

    if 'offset_list' in procmd:
        procmd['offset_list'] = text2list(procmd['offset_list'])
        log['nice'] = False
        log['info'] = 'Error: the parameter offset_list is wrong'

    if ('atomtype_list' in procmd) and (procmd['atomtype_list'] is not None):
        value = procmd['atomtype_list'].replace('"',' ').replace("'",' ')
        value = value.replace(';',' ').replace(",",' ').strip()
        if len(value) != 0 and value[0] == '[':
            value = value[1:].strip()
        if len(value) != 0 and value[-1] == ']':
            value = value[:len(value)].strip()
        if len(value) == 0:
            value = None
        else:
            value = value.split()
        procmd['atomtype_list'] = value

    return log, procmd



