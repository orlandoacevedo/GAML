# Genetic Algorithm Machine Learning (GAML) 
=================================================

Genetic Algorithm Machine Learning (GAML) software package for automated force field parameterization.

[Orlando Acevedo](http://www.acevedoresearch.com), University of Miami

This machine learning-based software package automates the force field parameterization of solvents for molecular dynamics (MD) or Monte Carlo (MC) simulations. New OPLS-AA atomic charges and 12-6 Lennard-Jones terms are parameterized for any solvent using a genetic algorithm crossover/average/mutation method. GAML outputs GROMACS formatted files (with additional packages under development, e.g., LAMPPS and AMBER).The parameters are validated by default against user-supplied free energies of hydration (ΔGhyd), liquid densities, and heats of vaporization (ΔHvap).

The user can to choose additional physical properties to optimize, e.g., heat capacity, viscosity, self-diffusivity, dipoles, and solubility. (However, this is still under development and not included in the current build here.)

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
pip install GAML (still under development, so please install from the source codes)
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
      
      ``gaml [charge_gen_range, charge_gen_scheme, file_gen_gaussian, file_gen_gromacstop, GAML_main]``


      + ``gaml charge_gen_range``
           
           -f, --filepath    input charge file path
           -i, --atomnm      the number of atoms in system
           -p, --percent     range from 0.0~1.0, default is 0.8
           -t, --stepsize    default is 0.01
           -nr, --nmround    decimal round number, default is 3
           -o, --fname       output file name, default is ChargeGenRange


      + ``gaml charge_gen_scheme``
           
           -f, --filepath          input charge file
           -sl, --symmetry_list    a python type list contains atom's chemical equivalent
           -c, --offset            the attemption numbers to generate charge
           -tc, --total_charge     default is 1.0
           -nr, --nmround          decimal round number, default is 2
           -b, --in_keyowrd        the mark of start in the input file
           -nm, --gennm            output file numbers, default is 5
           -o, --fname             output file name, default is ChargeRandomGen


      + ``gaml file_gen_gaussian``
           
           -ftop, --topfile       the Gromacs topology file with some editions
           -fpdb, --pdbfile       the Gromacs output pdb file
           -sr, --select_range    Angstrom, default is 10
           -bs, --basis_set       Gaussian definition, default is ``# HF/6-31G(d) Pop=CHelpG``
           -cs, --charge_spin     Gaussian definition, default is ``0 1`` 
           -nm, --gennm           output file numbers, default is 5
           -o, --fname            output file name, default is GaussInput


      + ``gaml file_gen_gromacstop``

           -f, --chargefile       input charge file
           -ftop, --topfile       the Gromacs topology file
           -sl, --symmetry_list   a python type list contains atom's chemical equivalent
           -res, --reschoose      the choose residue, default is ``ALL``,  
           -b, --in_keyowrd       the mark of start in the input file
           -e, --cut_keyowrd      the mark of end in the input file
           -nm, --gennm           output file numbers, default is 5
           -o, --fname            output file name, default is GenGromacsTopfile


      + ``gaml GAML_main``

           -f, --filepath             input total MD file
           -fc, --chargerangefile     the defined charge range file
           -sl, --symmetry_list       a python type list contains atom's chemical equivalent
           -d, --error_tolerance      default is 0.8
           -ex, --charge_extend_by    the value to change the charge range bound, default is 0.3
           -abs, --bool_abscomp       use absolute value or not 
           -nr, --nmround             decimal round number, default is 2
           -tc, --total_charge        default is 1.0
           -b, --in_keyowrd           the mark of start in the input file
           -e, --cut_keyowrd          the mark of end in the input file
           -nm, --gennm               output file numbers, default is 5
           -o, --fname                output file name, default is ML_chargeRandomGen

## Notes
----------
The most recent version of the software is GAML v.04 and is still heavily under development. Lennard-Jones optimization has not been implemented in this GitHub version.
A test for a 1-butylpyridinium-based ionic liquid can be found under the ``sample/`` directory
Some features worth mentioning:
+ Customized selection range for Coulombic interactions with PBC removal
+ Mode number starting of partial subset chosen in total dataset
+ Two offsets as well as chemical equivalence considerations for random charge generations
+ The crossover/average/mutation method

## References
----------
Zhong, X.; Acevedo, O. "Genetic Algorithm Machine Learning (GAML) software package for automated force field parameterization of solvents." (in preparation for submission)

## About
-----
**Contributing Authors**: Xiang Zhong and Orlando Acevedo*

**Funding**: Gratitude is expressed to the National Science Foundation for funding the project.

**Software License**:
GAML. Genetic Algorithm Machine Learning (GAML) software package.
Copyright (C) 2018  Orlando Acevedo
