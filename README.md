# Genetic Algorithm Machine Learning (GAML) 
=================================================

Genetic Algorithm Machine Learning (GAML) software package for automated force field parameterization.

[Orlando Acevedo](http://www.acevedoresearch.com) and Xiang Zhong, University of Miami

This machine learning based software package automates the creation of force field (FF) parameters for molecular dynamics (MD) or Monte Carlo (MC) simulations. In the current build, atomic charge development is emphasized for solvent simulations using a genetic algorithm crossover/average/mutation method. GAML outputs GROMACS formatted files in the OPLS-AA formalism for use in MD simulations. The FF parameters are validated by default against user-supplied free energies of hydration (ΔGhyd), liquid densities, and heats of vaporization (ΔHvap). However, additional condensed phased physical properties are available (or under development) for training that include: heat capacity, viscosity, self-diffusivity, dipoles, surface tension, and solubility.

## Requirements
------------
* [Gromacs](http://www.gromacs.org/Downloads)
* [Gaussian](http://www.gaussian.com)
* [Python 3](http://www.python.org)
    
## Download
-----
```
git clone git://github.com/orlandoacevedo/GAML.git
```

## Installation
-----
```
pip install GAML (still under development, so please install from the source code)
```
or
```
python setup.py install
```

## Usage
--------
For helpful information, use
```
gaml
```
or
```
gaml -h
```
or
```
gaml [command] -h
```

 **Option 1**, use a *settingfile.txt* file (plain text file)
      
      For example,

        ==========================================   =====================================
        **# Parameters**                              **# comments**
        ==========================================   =====================================
        command   = charge_gen_range                 # command to execute, required
        filepath  = BPYR_BF4_charge_collection.txt   # input file path, required
        atomnm    = 24                               # the processed atom number, required
        percent   = 0.8                              # optional, default is 0.8
        stepsize  = 0.01                             # optional, default is 0.01
        nmround   = 3                                # optional, default is 3
        fname     = ChargeGenRange                   # optional, default is ChargeGenRange
        ==========================================   =====================================    
   
  A template for the *settingfile.txt* can be found in the ``sample/`` directory.

  **Option 2**, use the command line
      
      Usage:
      
      ``gaml [charge_gen_range, charge_gen_scheme, file_gen_gaussian, file_gen_gromacstop, GAML, fss_analysis]``


      + ``gaml charge_gen_range``
           
           -f, --charge_path          input charge file path
           -i, --atomnm               the total atom numbers of single system
           -p, --percent              range from 0.0~1.0, default is 0.8
           -t, --stepsize             default is 0.01
           -nr, --nmround             decimal round number, default is 3
           -o, --fname                output file name, default is ChargeGenRange


      + ``gaml charge_gen_scheme``
           
           -f, --charge_path          input charge file
           -sl, --symmetry_list       a python type list contains atom's chemical equivalent
           -ol, --offset_list         two offsets to fit charge constrain
           --offset_nm                the attemption numbers to generate charge
           --cl, --counter_list       a group of two atom charges are zero
           -tc, --total_charge        default is 1.0
           -nz, --bool_nozero         no zero charges was generated, default is True
           -nu, --bool_neutral        force the final calculated value scaled from 1 or not, default is True
           -q, --bool_limit           uses to define the charge range, whether positive or negative, default is None
           -nr, --nmround             decimal round number, default is 2
           -b, --in_keyowrd           the mark of start in the input file
           -nm, --gennm               output file numbers, default is 5
           -lim, --threshold          the limit for the charge value generation
           -o, --fname                output file name, default is ChargeRandomGen


      + ``gaml file_gen_gaussian``
           
           -ftop, --toppath           the Gromacs topology file
           -f, --pdbpath              the Gromacs output pdb file
           -sr, --select_range        Angstrom, default is 10
           -bs, --basis_set           Gaussian definition, default is ``# HF/6-31G(d) Pop=CHelpG``
           -cs, --charge_spin         Gaussian definition, default is ``0 1`` 
           -nm, --gennm               output file numbers, default is 5
           -o, --fname                output file name, default is GaussInput


      + ``gaml file_gen_gromacstop``

           -f, --charge_path          input charge file
           -ftop, --toppath           the Gromacs topology file
           -sl, --symmetry_list       a python type list contains atom's chemical equivalent
           -res, --reschoose          the choose residue, default is ``ALL``,  
           -b, --in_keyowrd           the mark of start in the input file
           -e, --cut_keyowrd          the mark of end in the input file
           -nm, --gennm               output file numbers, default is 5
           -o, --fname                output file name, default is GenGromacsTopfile


      + ``gaml GAML``

           -f, --file_path            input MD file
           -fc, --charge_path         the defined charge range file
           -sl, --symmetry_list       a python type list contains atom's chemical equivalent
           -ol, --offset_list         two offsets to fit charge constrain
           --offset_nm                the attemption numbers to generate charge
           --cl, --counter_list       a group of two atom charges are zero
           -d, --error_tolerance      default is 0.8
           -nz, --bool_nozero         no zero charges was generated, default is True
           -nu, --bool_neutral        force the final calculated value scaled from 1 or not, default is True
           -q, --bool_limit           uses to define the charge range, whether positive or negative, default is None
           -ex, --charge_extend_by    the value to change the charge range bound, default is 0.3
           -ro, --ratio               ratio among Cross-over to Average to Mutation. The number of pair generations of 
                                      normal charge range is always equal to number of modified charge range, default is 7:2:1
           -lim, --threshold          the limit for the charge value generation
           -abs, --bool_abscomp       use absolute value or not 
           -nr, --nmround             decimal round number, default is 2
           -tc, --total_charge        default is 1.0
           -e, --cut_keyowrd          the mark of end in the input file
           -nm, --gennm               output file numbers, default is 5
           -o, --fname                output file name, default is ML_chargeRandomGen


	+ ``gaml fss_analysis``

           -f, --file_path            input analyzing file                        
           -t, --stepsize             default is 0.01
           -d, --error_tolerance      default is 0.28
           -abs, --bool_abscomp       default is False, use the absolute value or not
           -p, --percent              range from 0.0 ~ 1.0, default is 0.95
           -e, --cut_keyword          the mark of the end in the input file, default is MAE
           -tl, --atomtype_list       correspondent atom types, note the character '#' is not supported
           -pn, --pallette_nm         number of pallettes used to plot the graph, default is 50
           -cm, --color_map           this is a key word compatible with Matplotlib modules, default is rainbow
           -o, --fname                output file name, default is FSS_analysis



## Notes
----------
The most recent version of the software is GAML v0.7 and is still under development.
A test for a 1-butylpyridinium-based ionic liquid can be found under the ``sample/`` directory
Some features worth mentioning:
+ Customized selection range for Coulombic interactions with PBC removal
+ Mode number starting of partial subset chosen in total dataset
+ Two offsets as well as chemical equivalence considerations for random charge generations
+ The crossover/average/mutation method

## References
----------
Zhong, X.; Acevedo, O. "Partial Charges Optimized by Genetic Algorithms for Deep Eutectic Solvent Simulations." (in preparation for submission)

## About
-----
**Contributing Authors**: Xiang Zhong and Orlando Acevedo*

**Funding**: Gratitude is expressed to the National Science Foundation for funding the project.

**Software License**:
GAML. Genetic Algorithm Machine Learning (GAML) software package.
Copyright (C) 2020  Orlando Acevedo
