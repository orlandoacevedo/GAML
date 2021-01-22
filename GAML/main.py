from GAML.charge_gen_range import Charge_gen_range
from GAML.charge_gen_scheme import Charge_gen_scheme
from GAML.file_gen_gaussian import File_gen_gaussian
from GAML.file_gen_gromacstop import File_gen_gromacstop
from GAML.gaml import GAML
from GAML.file_gen_mdpotential import File_gen_mdpotential
from GAML.gaml_autotrain import GAML_autotrain
from GAML.fss_analysis import FSS_analysis
from GAML.parsecmd import parsecmd
from GAML.parsefile import parsefile
from GAML.defaults import parlist
from GAML.file_gen_scripts import File_gen_scripts

import sys
from sys import exit


def run(fdict):
    """Execute command
    
    assumes input directory has been properly processed.

    This method should be updated for future updates
    """
    cmd = fdict['command']
    if cmd == 'file_gen_gaussian':
        fp = File_gen_gaussian(**fdict)
    elif cmd == 'gaml_autotrain':
        fp = GAML_autotrain(**fdict)
    elif cmd == 'charge_gen_range':
        fp = Charge_gen_range(**fdict)
    elif cmd == 'charge_gen_scheme':
        fp = Charge_gen_scheme(**fdict)
    elif cmd == 'file_gen_gromacstop':
        fp = File_gen_gromacstop(**fdict)
    elif cmd == 'gaml':
        fp = GAML(**fdict)
    elif cmd == 'fss_analysis':
        fp = FSS_analysis(**fdict)
    elif cmd == 'file_gen_mdpotential':
        fp = File_gen_mdpotential(**fdict)
    elif cmd == 'file_gen_scripts':
        fp = File_gen_scripts(**fdict)
    else:
        # Normally, this part will never be executed.
        # However, it is still defined
        print('Error: no command is executed')
        exit()

    fp.run()
    fp.file_print()



def cmd_line_runner():
    cmdlist = [i['command'].lower() for i in parlist]

    if len(sys.argv) == 1:
        print('GAML package\n\n')
        print('Option 1, using setting file:\ngaml settingfile\n\n')
        print('Option 2, using command line:\n')
        s,t = parsecmd('')
        exit()

    if sys.argv[1].lower() in ['-v','--version','-h','--help',*cmdlist]:
        log, args = parsecmd(sys.argv[1:])
        if log['nice']:
            for fdict in parlist:
                if fdict['command'] == args['command'].lower():
                    for key in args:
                        if args[key] is not None:
                            fdict[key] = args[key]
                    run(fdict)
        else:
            print(log['info'])
            exit()
    else:
        log, profile = parsefile(sys.argv[1])
        if not log['nice']:
            print(log['info'])
            exit()

        for block in profile:
            for i in block:
                if i[0] == 'command':
                    cmd = i[1]
                    break

            for fdict in parlist:
                if fdict['command'] == cmd.lower():
                    for ndx in block:
                        if ndx[0] in fdict:
                            fdict[ndx[0]] = ndx[1]
                        else:
                            print('Error: ',ndx[2])
                            exit()
                    run(fdict)



if __name__ == '__main__':
    cmd_line_runner()



