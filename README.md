# Genetic Algorithm Machine Learning (GAML)

Genetic Algorithm Machine Learning (GAML) software package for automated force field parameterization.

Xiang Zhong and [Orlando Acevedo*](https://web.as.miami.edu/chemistrylabs/acevedogroup/research.html), University of Miami

This machine learning based software package automates the creation of force field (FF) parameters for molecular dynamics (MD) or Monte Carlo (MC) simulations. In the current build, atomic charge development is emphasized for solvent simulations using a genetic algorithm crossover/average/mutation method. GAML outputs GROMACS formatted files in the OPLS-AA formalism for use in MD simulations. The FF parameters are validated by default against user-supplied free energies of hydration (ΔG<sub>hyd</sub>), liquid densities, and heats of vaporization (ΔH<sub>vap</sub>). However, additional condensed phased physical properties are available (or under development) for training that include: heat capacity, viscosity, self-diffusivity, dipoles, surface tension, and solubility.


## Requirements

* [Gromacs](http://www.gromacs.org/Downloads)
* [Gaussian](http://www.gaussian.com)
* [Python 3](http://www.python.org)


## Download

```
git clone git://github.com/orlandoacevedo/GAML.git
```

## Installation

```
pip[3] install gaml
```

Or using source codes

```
python[3] setup.py install
```

## Usage

For helpful information, use

```
gaml
```

Or

```
gaml -h
```
Or, for sub-commands

```
gaml [command] -h
```


**Option 1**, use *settingfile.txt*

```
     Parameters                                    comments
===========================================       =====================================
command     = charge_gen_range                    # command to execute, required
charge_path = BPYR_BF4_charge_collection.txt      # input file path, required
atomnm      = 24                                  # the processed atom number, required
percent     = 0.8                                 # optional, default is 0.8
stepsize    = 0.01                                # optional, default is 0.01
nmround     = 3                                   # optional, default is 3
fname       = ChargeGenRange                      # optional, default is ChargeGenRange
```

The templates for the *settingfile.txt* can be found in the **sample/** directory.


**Option 2**, use the command line

```
Usage:

gaml
    charge_gen_range
    charge_gen_scheme
    file_gen_gaussian
    file_gen_gromacstop
    file_gen_mdpotential
    file_gen_scripts
    fss_analysis
    GAML
    GAML_autotrain


> gaml charge_gen_range

    -f, --charge_path           input charge file path
    -i, --atomnm                total atom numbers of single system
    -p, --percent               range from 0.0 ~ 1.0, default is 0.8
    -t, --stepsize              default is 0.01
    -nr, --nmround              decimal round-off number, default is 3
    -o, --fname                 output file name, default is ChargeRange


> gaml charge_gen_scheme

    -f, --charge_path           input charge file
    -sl, --symmetry_list        list contains atom's chemical equivalent, index starting from 1
    -ol, --offset_list          two offsets to fit charge constrain
    --offset_nm                 loop numbers to for offsets
    --cl, --counter_list        force total charges in this group to zero
    -tc, --total_charge         default is 1.0
    -nz, --bool_nozero          force no zero charges was generated, default is True
    -nu, --bool_neutral         force final calculated value scaled from 1 or not, default is True
    -q, --bool_limit            force charge sign, either positive or negative, default is None
    -nr, --nmround              decimal round number, default is 2
    -b, --in_keyowrd            the mark of start in the input file
    -nm, --gennm                output file numbers, default is 5
    -lim, --threshold           threshold for the charge value generation
    -o, --fname                 output file name, default is ChargeRandomGen


> gaml file_gen_gaussian

    -ftop, --toppath            GROMACS topology file
    -f, --file_path             GROMACS output pdb/gro file
    -sr, --select_range         Angstrom, default is 10
    -bs, --basis_set            Gaussian definition, default is # HF/6-31G(d) Pop=CHelpG
    -cs, --charge_spin          Gaussian definition, default is 0 1
    -nm, --gennm                output file numbers, default is 5
    -o, --fname                 output file name, default is GaussInput


> gaml file_gen_gromacstop

    -f, --charge_path           input charge file
    -ftop, --toppath            GROMACS topology file
    -sl, --symmetry_list        a python type list contains atom's chemical equivalent
    -res, --reschoose           choose residue, default is ALL,
    -b, --in_keyowrd            the mark of start in the input file
    -e, --cut_keyowrd           the mark of end in the input file
    -nm, --gennm                output file numbers, default is 5
    -o, --fname                 output file name, default is GromacsTopfile


> gaml GAML

    -f, --file_path             input MD file
    -fc, --charge_path          input charge file
    -sl, --symmetry_list        list contains atom's chemical equivalent, index starting from 1
    -ol, --offset_list          two offsets to fit charge constrain
    --offset_nm                 loop numbers to for offsets
    --cl, --counter_list        force total charges in this group to zero
    -tc, --total_charge         default is 0.0
    -nz, --bool_nozero          force no zero charges was generated, default is True
    -nu, --bool_neutral         force final calculated value scaled from 1 or not, default is True
    -q, --bool_limit            force charge sign, either positive or negative, default is None
    -nr, --nmround              decimal round number, default is 2
    -nm, --gennm                output file numbers, default is 5
    -lim, --threshold           threshold for the charge value generation
    -d, --error_tolerance       default is 0.8
    -ex, --charge_extend_by     the value to mutate charge range bound, default is 0.3
    -ro, --ratio                ratio among Cross-over to Average to Mutation. default is 7:2:1
    -abs, --bool_abscomp        use absolute value or not
    -e, --cut_keyowrd           the mark of end in the input file
    -o, --fname                 output file name, default is ChargeGen


> gaml fss_analysis

     -f, --file_path            input analyzing file
     -t, --stepsize             default is 0.01
     -d, --error_tolerance      default is 0.28
     -abs, --bool_abscomp       default is False, use the absolute value or not
     -p, --percent              range from 0.0 ~ 1.0, default is 0.95
     -e, --cut_keyword          the mark of the end in the input file, default is MAE
     -tl, --atomtype_list       correspondent atom types, note the character '#' is not supported
     -pn, --pallette_nm         number of pallettes used to plot the graph, default is 50
     -cm, --color_map           compatible with Matplotlib modules, default is rainbow
     -o, --fname                output file name, default is FSSPlot


> file_gen_mdpotential

    -f, --file_path FILE_PATH   MD simulation result file
    -s, --chargefile            Input charge file
    -lv, --literature_value     correspondent literature value
    -i, --atomnm                total number of molecules in liquid phase, default is 500
    --MAE                       mean-absolute-value, default is 0.05
    --temperature               unit in Kelvin
    --block                     mark for file process, default is COUNT
    --bool_gas                  gas phase calculation, default is False
    -kw, --kwlist               MD result keyword list, default is Density
    -o, --fname                 output file name, default is MDProcess


> file_gen_scripts

    -n, --number                which script to choose, sequenced by -a
    -a, --available             show available built-in scripts


> GAML_autotrain

    -f, --file_path             auto training parameters all-in-one file
    --bashinterfile             user defined Bash interface file
```


## Notes

A test for a 1-butylpyridinium-based ionic liquid can be found under the **sample/** directory.

The OPLS-AA parameters for 86 conventional solvents optimized by GAML can be found under the **Solvents/** directory. Files formatted for GROMACS.

Some features worth mentioning:
+ Customized selection range for Coulombic interactions with PBC removal
+ Two offsets as well as chemical equivalence considerations for random charge generation
+ The crossover/average/mutation method

## References

Zhong, X.; Velez, C.; Acevedo, O. "Partial Charges Optimized by Genetic Algorithms for Deep Eutectic Solvent Simulations" *J. Chem. Theory Comput.*, **2021**, *17*, 3078-3087. [doi:10.1021/acs.jctc.1c00047](http://pubs.acs.org/doi/abs/10.1021/acs.jctc.1c00047)

## About

**Contributing Authors**: Xiang Zhong and [Orlando Acevedo*](https://web.as.miami.edu/chemistrylabs/acevedogroup/research.html)

**Funding**: Gratitude is expressed to the National Science Foundation (CHE-1562205) for the support of this research.

**Software License**:
GAML. Genetic Algorithm Machine Learning (GAML) software package.
Copyright (C) 2021  Orlando Acevedo
