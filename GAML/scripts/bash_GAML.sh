#!/bin/bash
# -*- coding: utf-8 -*-

#BSUB -n 1
#BSUB -q gpu_arg
#BSUB -W 168:00
#BSUB -J IL
#BSUB -P ionic
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -m usr18

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# version 0.1   Add LV_DES LV_HVAP LV_FEP; top; gro
# version 0.2   Add bool_equil
# version 0.3   Add built-in files gas.[top,gro]; liq.[top,gro]; fep.[top,gro]
# version 0.4   Fix some bugs
# version 0.5   Fix bugs of old bash array [-1] index
# version 0.6   more robust for files identifying
# version 0.7   Add bool_gamlout
# version 0.8   Add bool_check -- for manually training
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

nmround=3
symmetry_list=''
pn_limit=''
counter_list=
offset_list=

gromacs_energy_kw="Density Potential FEP"
# Density(kg/m^3)  Hvap(kJ/mol)  FEP(kJ/mol)
literature_value=''

error_tolerance=0.5
gennm=20
gmx=gmx_old                         # default: gmx
packmol=packmol                     # default: packmol


total_charge=0.0
training_cnt=1


training_total_nm=
#
# For manually training
#
bool_check=true
training_total_nm=$training_cnt


MAE=0.05
analysis_begintime=20               # default: 0 ps
analysis_endtime=-1                 # default: -1 ps


charge_range_path=                  # generate by existing top file


top_fep_path=
top_gas_path=
top_liq_path=

itp_path=MOL.itp

reschoose=MOL                   # default: MOL

gro_fep_path=
gro_gas_path=
gro_liq_path=

pdb_path=MOL.pdb


solvent_pdb_path=TIP4.pdb
solvent_itp_atomtypes=TIP4_atomtypes.itp
solvent_itp_bonds=TIP4_bonded.itp
solvent_resname=                # default: SOL
solvent_molecules_number=       # default: 1500
solvent_molecules_mass=         # default: 18 g/mol
solvent_box_length=             # generate by calculation
solvent_density=                # default: 1000 kg/m3


# Adding parameters
molecules_mass=                 # generate by existing top file
molecules_number=               # default: 500
box_length=                     # Angstrom; Integer


grompp_fep_min_lbfgs_path=
grompp_fep_min_steep_path=grompp_fep_min_fix.mdp
grompp_fep_npt_path=grompp_fep_npt_fix.mdp
grompp_fep_nvt_path=
grompp_fep_prod_path=grompp_fep_prod.mdp


grompp_min_liq_path=grompp_gaml_min_liq.mdp
grompp_npt_liq_path=grompp_gaml_npt_liq.mdp
grompp_nvt_liq_path=
grompp_prod_liq_path=grompp_gaml_prod_liq.mdp


grompp_min_gas_path=grompp_gaml_min_gas.mdp
grompp_prod_gas_path=grompp_gaml_prod_gas.mdp


bool_abscomp=
bool_neutral=
bool_nozero=
charge_extend_by=
offset_nm=
ratio=
threshold=

# overall control: if it is true, any non-setup is forced to true
# if it is false, any its descendent is true, it is true;
# only works on training_cnt = 1
bool_equil=false                 # default: false

bool_equil_liq=
grompp_equil_min_liq_path=grompp_equil_min_liq.mdp
grompp_equil_npt_liq_path=grompp_equil_npt_liq.mdp

bool_equil_gas=
grompp_equil_min_gas_path=grompp_equil_min_gas.mdp
grompp_equil_prod_gas_path=grompp_equil_prod_gas.mdp

bool_equil_fep=true
grompp_equil_min_fep_path=grompp_equil_min_fep.mdp
grompp_equil_npt_fep_path=grompp_equil_npt_fep.mdp



# gmx-top [defaults] parameters
defaults_nbfunc=            # default: 1
defaults_combrule=          # default: 3
defaults_genpair=           # default: yes
defaults_fudgelj=           # default: 0.5
defaults_fudgeqq=           # default: 0.5


# debug mode
bool_gamlout=true




#
# END of user inputs
#


if $bool_check; then bool_gamlout=false; fi

# Check if the commands exist or not, if not, set `G_EXESTAT=false'
# arguments: cmd-1 cmd-2 cmd-3 ...
#
# Note: it first will initialize global variable `G_EXESTAT' to true,
# then check the input commands, if any one of them is not found, 
# it will set this global variable `G_EXESTAT' to false
G_EXESTAT=true
cmdchk(){
if (( $# > 0 ))
then
    for cmd in $@
    do
        type $cmd > /dev/null 2>&1 || \
            { 
                echo "Error: command < $cmd > is not found"
                  G_EXESTAT=false
                  break
            }
    done
fi
}

gmx=${gmx:=gmx}
packmol=${packmol:=packmol}

cmd_array=( gaml $gmx $packmol cd mkdir kill sleep ps grep cat sed wc bc )
cmdchk ${cmd_array[*]}

if ! $G_EXESTAT; then exit 1; fi



# Kill a process by Using its pid after given amount time
# two arguments: 1_pid 2_sleep_time(integer, in seconds)
#
# Note, this function will check the existence of global
# variable `G_EXETIME', if not, set it to `5' 
pktime(){
if [[ -z $G_EXETIME ]]
then
    G_EXETIME=30
fi

if (( $# <= 0 )); then return 1; fi

if (( $# < 2 ))
then
    sleep $G_EXETIME
else
    if [[ $2 =~ ^[0-9]+$ ]]
    then
        sleep $2
    else
        sleep $G_EXETIME
    fi
fi

if $( ps -p $1 > /dev/null 2>&1 )
then
    kill $1
fi
}



# Check simulation types based on provided files and parameters

kw=($gromacs_energy_kw)
lenkw=${#kw[*]}
lv=($literature_value)
lenlv=${#lv[*]}
if (( $lenkw < $lenlv )); then lenmin=$lenkw; else lenmin=$lenlv; fi

#NOTE: DEBUG: add other properties
LV_DES=''
LV_HVAP=''
LV_FEP=''
for ((i=0; $i < $lenmin; i++))
do
    if [[ -n $(echo ${kw[$i]} | grep -i 'pot') ]]; then LV_HVAP=${lv[$i]}; fi
    if [[ -n $(echo ${kw[$i]} | grep -i 'den') ]]; then LV_DES=${lv[$i]}; fi
    if [[ -n $(echo ${kw[$i]} | grep -i 'fe') ]]; then LV_FEP=${lv[$i]}; fi
done


if [[ -z "$grompp_prod_liq_path" ]]
then
    if [[ -n "$LV_HVAP" || -n "$LV_DES" ]]
    then
        echo "Warning: Liquid Prod mdp file does not exist"
        echo "Note: Setting LV_HVAP and LV_DES to false"
        LV_HVAP=''
        LV_DES=''
    fi
fi

if [[ -z "$grompp_prod_gas_path" && -n "$LV_HVAP" ]]
then
    echo "Warning: Gas Prod mdp file does not exist"
    echo "Note: Setting LV_HVAP to false"
    LV_HVAP=''
fi

if [[ -z "$grompp_fep_prod_path" && -n "$LV_FEP" ]]
then
    echo "Warning: FEP Prod mdp file does not exist"
    echo "Note: Setting LV_FEP to false"
    LV_FEP=''
fi


training_cnt=${training_cnt:=1}
training_total_nm=${training_total_nm:=5}


if (( $training_cnt != 1 ))
then
    echo ''
    echo "Note: Resuming the training -- Setting gro & top files"
    if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
    then
        if [[ -f equil_liq_npt.gro ]]
        then
            echo "Note: Setting equil_liq_npt.gro --> gro_liq_path"
            echo "Note: Setting bool_equil_liq to false"
            gro_liq_path=equil_liq_npt.gro
            bool_equil_liq=false
        fi
        if [[ -z $top_liq_path && -f liq.top ]]
        then
            echo "Note: Setting liq.top --> top_liq_path"
            top_liq_path=liq.top
        fi

        if [[ -n "$LV_HVAP" ]]
        then
            if [[ -f equil_gas_prod.gro ]]
            then
                echo "Note: Setting equil_gas_prod.gro --> gro_gas_path"
                echo "Note: Setting bool_equil_gas to false"
                gro_gas_path=equil_gas_prod.gro
                bool_equil_gas=false
            fi
            if [[ -z "$top_gas_path" && -f gas.top ]]
            then
                echo "Note: Setting gas.top --> top_gas_path"
                top_gas_path=gas.top
            fi
        fi
    fi
    if [[ -n "$LV_FEP" ]]
    then
        if [[ -f equil_fep_prod.gro ]]
        then
            echo "Note: Setting equil_fep_prod.gro --> gro_fep_path"
            echo "Note: Setting bool_equil_fep to false"
            gro_fep_path=equil_fep_prod.gro
            bool_equil_fep=false
        fi
        if [[ -z "$top_fep_path" && -f fep.top ]]
        then
            echo "Note: Setting fep.top --> top_fep_path"
            top_fep_path=fep.top
        fi
    fi

    if [[ -z "$charge_range_path" && -f charge_range.txt ]]
    then
        echo "Note: Setting charge_range.txt --> charge_range_path"
        charge_range_path=charge_range.txt
    fi
    echo ''
fi

defaults_nbfunc=${defaults_nbfunc:=1}
defaults_combrule=${defaults_combrule:=3}
defaults_genpair=${defaults_genpair:=yes}
defaults_fudgelj=${defaults_fudgelj:=0.5}
defaults_fudgeqq=${defaults_fudgeqq:=0.5}


defaults="[ defaults ]
;nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
$defaults_nbfunc  $defaults_combrule  $defaults_genpair  $defaults_fudgelj  $defaults_fudgeqq
"

reschoose=${reschoose:=MOL}
molecules_number=${molecules_number:=500}

systems_liq="
[ system ]
; Name
Neat $reschoose

[ molecules ]
$reschoose $molecules_number

"

systems_gas="
[ system ]
; Name
Neat $reschoose

[ molecules ]
$reschoose 1

"

if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
then
    if [[ -z "$top_liq_path" ]]
    then
        echo "Warning: Liquid top file does not exist"
        if [[ -f liq.top ]]
        then
            echo "Note: Using found file: liq.top  -->  top_liq_path"
            top_liq_path=liq.top
        elif [[ -n "$top_gas_path" ]]
        then
            echo "Note: Generating Liquid top file based on gas-top file"
            cp $top_gas_path liq.top
            molnm=($(grep -e "^[[:space:]]*$reschoose[[:space:]]*[[:digit:]]" liq.top))
            tmp=${#molnm[*]}
            ((tmp=$tmp-1))
            molnm=${molnm[$tmp]}
            nm=($(sed -n "/^[[:space:]]*$reschoose/=" liq.top))
            tmp=${#nm[*]}
            ((tmp=$tmp-1))
            nm=${nm[$tmp]}
            #NOTE: DEBUG
            sed -i "${nm}s/$molnm/$molecules_number/" liq.top
            top_liq_path=liq.top
        elif [[ -n "$itp_path" ]]
        then
            echo "Note: Generating Liquid top file based on itp file"
            echo "$defaults" > liq.top
            cat $itp_path >> liq.top
            echo "$systems_liq" >> liq.top
            top_liq_path=liq.top
        else
            echo "Error: Parameter top_liq_path is not defined"
            echo "Note: Setting LV_HVAP and LV_DES to false"
            LV_HVAP=''
            LV_DES=''
        fi
    fi
fi

if [[ -n "$LV_HVAP" ]]
then
    if [[ -z "$top_gas_path" ]]
    then
        echo "Warning: Gas top file does not exist"
        if [[ -f gas.top ]]
        then
            echo "Note: Using found file: gas.top  -->  top_gas_path"
            top_gas_path=gas.top
        elif [[ -n "$itp_path" ]]
        then
            echo "Note: Generating Gas top file based on itp file"
            echo "$defaults" > gas.top
            cat $itp_path >> gas.top
            echo "$systems_gas" >> gas.top
            top_gas_path=gas.top
        elif [[ -n "$top_liq_path" ]]
        then
            echo "Note: Generating Gas top file based on liquid-top file"
            cp $top_liq_path gas.top
            molnm=($(grep -e "^[[:space:]]*$reschoose[[:space:]]*[[:digit:]]" gas.top))
            tmp=${#molnm[*]}
            ((tmp=$tmp-1))
            molnm=${molnm[$tmp]}
            nm=($(sed -n "^[[:space:]]*$reschoose" gas.top))
            tmp=${#nm[*]}
            ((tmp=$tmp-1))
            nm=${nm[$tmp]}
            sed -i "${nm}s/$molnm/1/" gas.top
            top_gas_path=gas.top
        else
            echo "Error: Parameter top_gas_path is not defined"
            echo "Note: Setting LV_HVAP to false"
            LV_HVAP=''
        fi
    fi
fi



# For packmol single molecule
inputfile_s="
tolerance 2.0        # tolerance distance
output liq.pdb       # output file name
filetype pdb         # output file type

#
# Structure
#
structure VAR_PDB
number $molecules_number       # Number of molecules
inside cube 0. 0. 0. VAR_box   # cube with coordinates (x,y,z) = (0,0,0) to (d,d,d) Angstrom
end structure
"
bool_packmol=false
if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
then
    if [[ -z "$gro_liq_path" ]]
    then
        echo "Warning: Liquid gro file does not exist"
        if [[ -f equil_liq_npt.gro ]]
        then
            echo "Note: Using found file: equil_liq_npt.gro  -->  gro_liq_path"
            echo "Note: Setting bool_equil_liq to false"
            gro_liq_path=equil_liq_npt.gro
            bool_equil_liq=false
        elif [[ -f liq.gro ]]
        then
            echo "Note: Using found file: liq.gro  -->  gro_liq_path"
            gro_liq_path=liq.gro
        elif [[ -f liq.pdb ]]
        then
            echo "Note: Using found file: liq.pdb  -->  gro_liq_path"
            $gmx editconf -f liq.pdb -o liq.gro
            gro_liq_path=liq.gro
        elif [[ -n "$gro_gas_path" || -n "$pdb_path" ]]
        then
            echo "Note: Generating Liquid gro file"
            if [[ -n "$gro_gas_path" ]]
            then
                $gmx editconf -f $gro_gas_path -o gen_s.pdb
                pdb=gen_s.pdb
            else
                pdb=$pdb_path
            fi
            echo "$inputfile_s" > input_s.inp
            sed -i "s/VAR_PDB/$pdb/" input_s.inp
            bool_packmol=true
        else
            echo "Error: Parameter gro_liq_path is not defined"
            echo "Note: Setting LV_HVAP and LV_DES to false"
            LV_HVAP=''
            LV_DES=''
        fi
    fi
fi

bool_error=false
if $bool_packmol && [[ -z "$molecules_mass" && -z "$box_length" ]]
then
    if [[ -n "$top_gas_path" ]]; then top=$top_gas_path; else top=$top_liq_path; fi

    nmatoms=$(sed -n '/atoms/=' $top)
    nmbonds=$(sed -n '/bonds/=' $top)

    if [[ -n "$nmatoms" && -n "$nmbonds" ]]
    then
        if (( $nmbonds - 1 <= $nmatoms )); then bool_packmol=false; fi
    else
        bool_packmol=false
    fi
    
    if ! $bool_packmol; then { echo "Error: Inside bool_packmol-nmatoms"; bool_error=true; } fi
fi

if $bool_packmol && [[ -z "$molecules_mass" && -z "$box_length" ]]
then
    IFS=$'\n'
    atomstr=''
    for line in $(sed -n "$nmatoms,${nmbonds}p" gas.top)
    do
        IFS=' '; line=($line)
        if (( ${#line[*]} <= 1 )); then continue; fi

        if ! [[ ${line[0]} =~ \;.* ]]
        then
            atomstr="$atomstr ${line[4]}"
        fi
    done
    unset IFS

    nmC=0
    nmH=0
    nmO=0
    nmN=0
    nmF=0
    nmP=0
    nmS=0
    nmI=0
    nmBr=0
    nmCl=0
    for i in $atomstr
    do
        if [[ -n $(echo $i | grep -i '^C') ]]; then ((nmC++)); fi
        if [[ -n $(echo $i | grep -i '^H') ]]; then ((nmH++)); fi
        if [[ -n $(echo $i | grep -i '^O') ]]; then ((nmO++)); fi
        if [[ -n $(echo $i | grep -i '^N') ]]; then ((nmN++)); fi
        if [[ -n $(echo $i | grep -i '^F') ]]; then ((nmF++)); fi
        if [[ -n $(echo $i | grep -i '^P') ]]; then ((nmP++)); fi
        if [[ -n $(echo $i | grep -i '^S') ]]; then ((nmS++)); fi
        if [[ -n $(echo $i | grep -i '^I') ]]; then ((nmI++)); fi
        if [[ -n $(echo $i | grep -i '^Br') ]]; then ((nmBr++)); fi
        if [[ -n $(echo $i | grep -i '^Cl') ]]; then ((nmCl++)); fi
    done

    # consider special cases
    (( nmC = $nmC - $nmCl ))

    #echo $atomstr
    #echo "nmC=$nmC; nmH=$nmH; nmO=$nmO; nmN=$nmN; nmF=$nmF"
    #echo "nmP=$nmP; nmS=$nmS; nmI=$nmI; nmBr=$nmBr; nmCl=$nmCl"

    mw=0
    mw=$(echo "$mw + $nmC*12.011 + $nmH*1.008 + $nmO*16" | bc -l)
    mw=$(echo "$mw + $nmN*14.007 + $nmF*19 + $nmP*31" | bc -l)
    mw=$(echo "$mw + $nmS*32.066 + $nmI*126.91 + $nmBr*79.90" | bc -l)
    mw=$(echo "$mw + $nmCl*35.5" | bc -l)
    molecules_mass=$mw

    tmp=$(echo "$mw-1" | bc -l | grep '-' )
    if [[ -n "$tmp" ]]; then { echo "Error: Inside bool_packmol-mw"; bool_packmol=false; bool_error=true; \
                               molecules_mass=UNDEF; } fi
fi


if $bool_packmol
then
    if [[ -z "$box_length" ]]
    then
        tmp=$(echo "$molecules_number*$molecules_mass*10/6.02/$LV_DES" | bc -l)
        box=$(echo "e(1/3*l($tmp))" | bc -l)      # Nanometer
        box=$(echo "($box+0.03) * 10" | bc -l)    # Angstrom
    else
        box=$(echo "$box_length+0.03" | bc -l)    # Angstrom
    fi
    box_length=${box%.*}  # Angstrom, Integer

    sed -i "s/VAR_box/$box_length/" input_s.inp

    #NOTE: DEBUG: packmol -- for $pdb contines blank spaces
    $packmol < input_s.inp
    
    if [[ -f liq.pdb ]]
    then
        ((bh=($box_length+2)/10))
        ((bl=($box_length%10)+1))
        bm="$bh.$bl"
        $gmx editconf -f liq.pdb -bt cubic -box $bm $bm $bm -o liq.gro
        gro_liq_path=liq.gro
    else
        echo "Error: Inside bool_packmol-inputs_s.inp"
        bool_packmol=false
        bool_error=true
    fi
fi

if $bool_error
then
    echo "Note: Setting LV_HVAP and LV_DES to false"
    LV_HVAP=''
    LV_DES=''
fi



if [[ -n "$LV_HVAP" && -z "$gro_gas_path" ]]
then
    echo "Warning: Gas gro file does not exist"
    if [[ -f equil_gas_prod.gro ]]
    then
        echo "Note: Using found file: equil_gas_prod.gro  -->  gro_gas_path"
        echo "Note: Setting bool_equil_gas to false"
        gro_gas_path=equil_gas_prod.gro
        bool_equil_gas=false
    elif [[ -f gas.gro ]]
    then
        echo "Note: Using found file: gas.gro  -->  gro_gas_path"
        gro_gas_path=gas.gro
    elif [[ -n "$pdb_path" ]]
    then
        echo "Note: Generating Gas gro file"
        ((bh=($box_length+2)/10))
        ((bl=($box_length%10)+1))
        bm="$bh.$bl"
        $gmx editconf -f $pdb_path -bt cubic -box $bm $bm $bm -o gas.gro
        gro_gas_path=gas.gro
    else
        echo "Error: Parameter gro_gas_path is not defined"
        echo "Note: Setting LV_HVAP to false"
        LV_HVAP=''
    fi
fi


if ! [[ -d Test ]]; then mkdir Test; fi


if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
then
    cd Test
    if ! [[ -f test_prod_liq.tpr ]]
    then
        $gmx grompp -f ../$grompp_prod_liq_path -c ../$gro_liq_path -p ../$top_liq_path -o test_prod_liq.tpr
        if ! [[ -f test_prod_liq.tpr ]]
        then
            echo "Error: on Testing Liquid prod tpr Generating"
            echo "Note: Setting LV_HVAP and LV_DES to false"
            LV_DES=''
            LV_HVAP=''
        fi
    fi
    
    if [[ -n "$LV_HVAP" ]]
    then
        if ! [[ -f test_prod_gas.tpr ]]
        then
            $gmx grompp -f ../$grompp_prod_gas_path -c ../$gro_gas_path -p ../$top_gas_path -o test_prod_gas.tpr
            if ! [[ -f test_prod_gas.tpr ]]
            then
                echo "Error: on Testing Gas prod tpr Generating"
                echo "Note: Setting LV_HVAP to false"
                LV_HVAP=''
            fi
        fi
    fi
    cd ../
fi


if [[ -n "$LV_FEP" ]]
then
    # Get the longest FEP settings for LJ and Coulombic
    vdw=$(grep '^[[:blank:]]\{0,\}vdw[-_]lambdas[[:blank:]]\{0,\}=' $grompp_fep_prod_path)
    vdw=${vdw#*=}
    vdw=${vdw%%;*}
    vdw=( $vdw )
    lenvdw=${#vdw[*]}

    coul=$(grep '^[[:blank:]]\{0,\}coul[-_]lambdas[[:blank:]]\{0,\}=' $grompp_fep_prod_path)
    coul=${coul#*=}
    coul=${coul%%;*}
    coul=( $coul )
    lencoul=${#coul[*]}

    fep=$(grep '^[[:blank:]]\{0,\}fep[-_]lambdas[[:blank:]]\{0,\}=' $grompp_fep_prod_path)
    fep=${fep#*=}
    fep=${fep%%;*}
    fep=( $fep )
    lenfep=${#fep[*]}

    if (( $lenvdw == 0 && $lencoul == 0 ))
    then
        LENLAMBDAS=$lenfep
    elif (( $lenvdw > $lencoul ))
    then
        LENLAMBDAS=$lenvdw
    else
        LENLAMBDAS=$lencoul
    fi
    
    if (( $LENLAMBDAS < 2 ))
    then
        echo "Error: on LENLAMBDAS identifying"
        echo "Note: Setting LV_FEP to false"
        LV_FEP=''
    fi
fi


solvent_resname=${solvent_resname:=SOL}
solvent_molecules_number=${solvent_molecules_number:=1500}
solvent_molecules_mass=${solvent_molecules_mass:=18}
solvent_density=${solvent_density:=1000}


# For packmol two molecules
inputfile_d="
tolerance 2.0           # tolerance distance
output fep.pdb          # output file name
filetype pdb            # output file type

#
# Structure
#
structure VAR_PDB
number 1                # Number of molecules
inside cube 0. 0. 0. VAR_box   # cube with coordinates (x,y,z) = (0,0,0) to (d,d,d) Angstrom
end structure

structure $solvent_pdb_path
number $solvent_molecules_number      # Number of molecules
inside cube 0. 0. 0. VAR_box   # cube with coordinates (x,y,z) = (0,0,0) to (d,d,d) Angstrom
end structure
"
bool_packmol_solvent=false
if [[ -n "$LV_FEP" && -z "$gro_fep_path" ]]
then
    echo "Warning: FEP gro file does not exist"
    if [[ -f equil_fep_prod.gro ]]
    then
        echo "Note: Using found file: equil_fep_prod.gro -->  gro_fep_path"
        echo "Note: Setting bool_equil_fep to false"
        gro_fep_path=equil_fep_prod.gro
        bool_equil_fep=false
    elif [[ -f fep.gro ]]
    then
        echo "Note: Using found file: fep.gro  -->  gro_fep_path"
        gro_fep_path=fep.gro
    elif [[ -f fep.pdb ]]
    then
        echo "Note: Using found file: fep.pdb  -->  gro_fep_path"
        $gmx editconf -f fep.pdb -o fep.gro
        gro_fep_path=fep.gro
    elif [[ -n "$solvent_pdb_path" ]]
    then
        echo "Note: Generating FEP gro file using $packmol"
        pdb=''
        if [[ -n "$pdb_path" ]]
        then
            pdb=$pdb_path
        elif [[ -n "$gro_gas_path" ]]
        then
            $gmx editconf -f $gro_gas_path -o gen_d.pdb
            pdb=gen_d.pdb
        fi
        
        if [[ -n "$pdb" ]]
        then
            echo "$inputfile_d" > input_d.inp
            sed -i "s/VAR_PDB/$pdb/" input_d.inp
            bool_packmol_solvent=true
        else
            echo "Error: Inside solvent_pdb_path"
            echo "Note: Setting LV_FEP to false"
            LV_FEP=''
        fi
    else
        echo "Error: Parameter gro_fep_path is not defined"
        echo "Note: Setting LV_FEP to false"
        LV_FEP=''
    fi
fi


if $bool_packmol_solvent
then
    if [[ -z "$solvent_box_length" ]]
    then
        tmp=$(echo "$solvent_molecules_number*$solvent_molecules_mass*10/6.02/$solvent_density" | bc -l)
        box=$(echo "e(1/3*l($tmp))" | bc -l)     # Nanometer
        box=$(echo "($box+0.03) * 10" | bc -l)   # Angstrom
    else
        box=$(echo "$solvent_box_length+0.03" | bc -l)   # Angstrom
    fi
    solvent_box_length=${box%.*}    # Angstrom, Integer

    sed -i "s/VAR_box/$solvent_box_length/" input_d.inp

    $packmol < input_d.inp
    
    if [[ -f fep.pdb ]]
    then
        ((bh=($solvent_box_length+2)/10))
        ((bl=($solvent_box_length%10)+1))
        bm="$bh.$bl"
        $gmx editconf -f fep.pdb -bt cubic -box $bm $bm $bm -o fep.gro
        gro_fep_path=fep.gro
    else
        bool_packmol_solvent=false
        echo "Error: Inside bool_packmol_solvent-inputs_d.inp"
        echo "Note: Setting LV_FEP to false"
        LV_FEP=''
    fi
fi



# Gromacs top file generation
systems_fep="
[ molecules ]
$reschoose   1
$solvent_resname $solvent_molecules_number

"
if [[ -n "$LV_FEP" && -z "$top_fep_path" ]]
then
    echo "Warning: FEP top file does not exist"
    if [[ -f fep.top ]]
    then
        echo "Note: Using found file: fep.top  -->  top_fep_path"
        top_fep_path=fep.top
    elif [[ -n "$solvent_itp_atomtypes" && -n "$solvent_itp_bonds" ]]
    then
        echo "Note: Generating FEP top file"
        if [[ -n "$top_gas_path" || -n "$top_liq_path" ]]
        then
            if [[ -n "$top_gas_path" ]]; then top=$top_gas_path; else top=$top_liq_path; fi
            echo "Note: Geting FEP top [ defaults ] based on $top"
            nm=($(sed -n '/^[[:space:]]*\[[[:space:]]*atomtypes[[:space:]]*\]/=' $top))
            nm=${nm[0]}
            nm=${nm:=2}
            ((nm=$nm-1))
            cp -f $top fep_tmp.top
            head -n $nm fep_tmp.top > fep.top
            cat $solvent_itp_atomtypes >> fep.top
            sed -i "1,${nm}d" fep_tmp.top
            cat fep_tmp.top >> fep.top
            rm -f fep_tmp.top
            
            ab=($(sed -n '/^[[:space:]]*\[[[:space:]]*molecules[[:space:]]*\]/=' fep.top))
            ab=${ab[0]}
            ab=${ab:=10000}
            sed -i "$ab,\$d" fep.top
            cat $solvent_itp_bonds >> fep.top
            echo "$systems_fep" >> fep.top
            top_fep_path=fep.top
        else
            echo "Error: Inside solvent_itp_atomtypes and solvent_itp_bonds"
            echo "Note: Setting LV_FEP to false"
            LV_FEP=''
        fi
    else
        echo "Error: Parameter top_fep_path is not defined"
        echo "Note: Setting LV_FEP to false"
        LV_FEP=''
    fi
fi


if [[ -n "$LV_FEP" ]]
then
    cd Test
    if ! [[ -f test_prod_fep.tpr ]]
    then
        cp ../$grompp_fep_prod_path test_grompp_fep_prod.mdp
        moltype=$(grep '^[[:blank:]]*couple[-_]moltype' test_grompp_fep_prod.mdp)
        if [[ -n "$moltype" ]]
        then
            sed -i "s@$moltype@couple-moltype    = $reschoose@" test_grompp_fep_prod.mdp
        fi
        initlambda=$(grep '^[[:blank:]]*init_lambda_state' test_grompp_fep_prod.mdp)
        if [[ -n "$initlambda" ]]
        then
            sed -i "s@$initlambda@init_lambda_state    = 0@" test_grompp_fep_prod.mdp
        fi
        
        $gmx grompp -f test_grompp_fep_prod.mdp -c ../$gro_fep_path -p ../$top_fep_path -o test_prod_fep.tpr
        if ! [[ -f test_prod_fep.tpr ]]
        then
            echo "Error: on Testing FEP prod tpr Generating"
            echo "Note: Setting LV_FEP to false"
            LV_FEP=''
        fi
    fi
    cd ../
fi


if [[ -z "$LV_HVAP" && -z "$LV_DES" && -z "$LV_FEP" ]]
then
    echo 'Fatal Error: No simulation type is correctly defined'
    exit 1
fi


bool_equil=${bool_equil:=false}
if $bool_equil
then
    if [[ -z "$bool_equil_gas" ]]; then bool_equil_gas=true; fi
    if [[ -z "$bool_equil_liq" ]]; then bool_equil_liq=true; fi
    if [[ -z "$bool_equil_fep" ]]; then bool_equil_fep=true; fi
else
    bool_equil_gas=${bool_equil_gas:=false}
    bool_equil_liq=${bool_equil_liq:=false}
    bool_equil_fep=${bool_equil_fep:=false}
    if $bool_equil_gas; then bool_equil=true; fi
    if $bool_equil_liq; then bool_equil=true; fi
    if $bool_equil_fep; then bool_equil=true; fi
fi


if $bool_equil
then
    echo "Note: starting equilibrations..."
    if $bool_equil_gas && [[ -n "$LV_HVAP" ]]
    then
        bool_index=false
        if [[ -z "$grompp_equil_min_gas_path" ]]
        then
            echo "Warning: grompp_equil_min_gas_path does not exist"
            if [[ -n "$grompp_min_gas_path" ]]
            then
                echo "Note: Using found file: grompp_min_gas_path=$grompp_min_gas_path  -->  grompp_equil_min_gas_path"
                grompp_equil_min_gas_path=$grompp_min_gas_path
                bool_index=true
            else
                echo "Warning: grompp_equil_min_gas_path is not setup"
            fi
        else
            bool_index=true
        fi

        if [[ -z "$grompp_equil_prod_gas_path" ]]
        then
            echo "Warning: grompp_equil_prod_gas_path does not exist"
            if [[ -n "$grompp_prod_gas_path" ]]
            then
                echo "Note: Using found file: grompp_prod_gas_path=$grompp_prod_gas_path  -->  grompp_equil_prod_gas_path"
                grompp_equil_prod_gas_path=$grompp_prod_gas_path
                bool_index=true
            else
                echo "Warning: grompp_equil_prod_gas_path is not setup"
            fi
        else
            bool_index=true
        fi

        if ! $bool_index
        then
            echo "Error: Due to lacking of mdp-files, bool_equil_gas is turned off"
            bool_equil_gas=false
        fi
    else
        echo "Note: bool_equil_gas is turned off"
        bool_equil_gas=false
    fi


    if $bool_equil_liq && [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
    then
        bool_index=false
        if [[ -z "$grompp_equil_min_liq_path" ]]
        then
            echo "Warning: grompp_equil_min_liq_path does not exist"
            if [[ -n "$grompp_min_liq_path" ]]
            then
                echo "Note: Using found file: grompp_min_liq_path=$grompp_min_liq_path  -->  grompp_equil_min_liq_path"
                grompp_equil_min_liq_path=$grompp_min_liq_path
                bool_index=true
            else
                echo "Warning: grompp_equil_min_liq_path is not setup"
            fi
        else
            bool_index=true
        fi

        if [[ -z "$grompp_equil_npt_liq_path" ]]
        then
            echo "Warning: grompp_equil_npt_liq_path does not exist"
            if [[ -n "$grompp_npt_liq_path" ]]
            then
                echo "Note: Using found file: grompp_npt_liq_path=$grompp_npt_liq_path  -->  grompp_equil_npt_liq_path"
                grompp_equil_npt_liq_path=$grompp_npt_liq_path
                bool_index=true
            else
                echo "Warning: grompp_equil_npt_liq_path is not setup"
            fi
        else
            bool_index=true
        fi

        if ! $bool_index
        then
            echo "Error: Due to lacking of mdp-files, bool_equil_liq is turned off"
            bool_equil_liq=false
        fi
    else
        echo "Note: bool_equil_liq is turned off"
        bool_equil_liq=false
    fi


    if $bool_equil_fep && [[ -n "$LV_FEP" ]]
    then
        bool_index=false
        if [[ -z "$grompp_equil_min_fep_path" ]]
        then
            echo "Note: grompp_equil_min_fep_path does not exist"
            if [[ -n "$grompp_min_liq_path" ]]
            then
                echo "Note: Using found file: grompp_min_liq_path=$grompp_min_liq_path  -->  grompp_equil_min_fep_path"
                grompp_equil_min_fep_path=$grompp_min_liq_path
                bool_index=true
            else
                echo "Warning: grompp_equil_min_fep_path is not setup"
            fi
        else
            bool_index=true
        fi

        if [[ -z "$grompp_equil_npt_fep_path" ]]
        then
            echo "Note: grompp_equil_npt_fep_path does not exist"
            if [[ -n "$grompp_npt_liq_path" ]]
            then
                echo "Note: Using found file: grompp_npt_liq_path=$grompp_npt_liq_path  -->  grompp_equil_npt_fep_path"
                grompp_equil_npt_fep_path=$grompp_npt_liq_path
                bool_index=true
            else
                echo "Warning: grompp_equil_npt_fep_path is not setup"
            fi
        else
            bool_index=true
        fi

        if ! $bool_index
        then
            echo "Error: Due to lacking of mdp-files, bool_equil_fep is turned off"
            bool_equil_fep=false
        fi
    else
        echo "Note: bool_equil_fep is turned off"
        bool_equil_fep=false
    fi
fi


if $bool_equil_gas || $bool_equil_liq || $bool_equil_fep
then
    cd Test/
    i=1
    while true
    do
        if ! [[ -d Equil_$i ]]; then break; fi
        ((i++))
    done
    mkdir Equil_$i
    cd Equil_$i

    if $bool_equil_gas
    then
        equil_gas_gro=''
        if [[ -n "$grompp_equil_min_gas_path" ]]
        then
            $gmx grompp -f ../../$grompp_equil_min_gas_path -c ../../$gro_gas_path -p ../../$top_gas_path -o equil_gas_min.tpr
            
            if [[ -f equil_gas_min.tpr ]]
            then
                $gmx mdrun -deffnm equil_gas_min
                
                if [[ -f equil_gas_min.gro ]]
                then
                    equil_gas_gro=equil_gas_min.gro
                else
                    echo "Warning: Equilibrations failed at Gas Min simulation"
                fi
            else
                echo "Error: Equilibrations failed at Gas Min preparation"
            fi
        fi

        if [[ -n "$grompp_equil_prod_gas_path" ]]
        then
            if [[ -n "$equil_gas_gro" ]]
            then
                $gmx grompp -f ../../$grompp_equil_prod_gas_path -c $equil_gas_gro -p ../../$top_gas_path -o equil_gas_prod.tpr
            else
                echo "Note: Trying to use gro_gas_path=$gro_gas_path as inputs"
                $gmx grompp -f ../../$grompp_equil_prod_gas_path -c ../../$gro_gas_path -p ../../$top_gas_path -o equil_gas_prod.tpr
            fi

            if [[ -f equil_gas_prod.tpr ]]
            then
                $gmx mdrun -deffnm equil_gas_prod
                
                if [[ -f equil_gas_prod.gro ]]
                then
                    equil_gas_gro=equil_gas_prod.gro
                else
                    echo "Warning: Equilibrations failed at Gas Prod simulation"
                fi
            else
                echo "Error: Equilibrations failed at Gas Prod preparation"
            fi
        fi

        if [[ -n "$equil_gas_gro" ]]
        then
            echo "Note: replacing gro_gas_path: $gro_gas_path with equil_gas_gro: $equil_gas_gro..."
            gro_gas_path=$equil_gas_gro
            cp -f $equil_gas_gro ../../
        fi
    fi


    if $bool_equil_liq
    then
        equil_liq_gro=''
        if [[ -n "$grompp_equil_min_liq_path" ]]
        then
            $gmx grompp -f ../../$grompp_equil_min_liq_path -c ../../$gro_liq_path -p ../../$top_liq_path -o equil_liq_min.tpr
            
            if [[ -f equil_liq_min.tpr ]]
            then
                $gmx mdrun -deffnm equil_liq_min
                
                if [[ -f equil_liq_min.gro ]]
                then
                    equil_liq_gro=equil_liq_min.gro
                else
                    echo "Warning: Equilibrations failed at Liquid Min simulation"
                fi
            else
                echo "Error: Equilibrations failed at Liquid Min preparation"
            fi
        fi

        if [[ -n "$grompp_equil_npt_liq_path" ]]
        then
            if [[ -n "$equil_liq_gro" ]]
            then
                $gmx grompp -f ../../$grompp_equil_npt_liq_path -c $equil_liq_gro -p ../../$top_liq_path -o equil_liq_npt.tpr
            else
                echo "Note: Trying to use gro_liq_path=$gro_liq_path as inputs"
                $gmx grompp -f ../../$grompp_equil_npt_liq_path -c ../../$gro_liq_path -p ../../$top_liq_path -o equil_liq_npt.tpr
            fi

            if [[ -f equil_liq_npt.tpr ]]
            then
                $gmx mdrun -deffnm equil_liq_npt
                
                if [[ -f equil_liq_npt.gro ]]
                then
                    equil_liq_gro=equil_liq_npt.gro
                else
                    echo "Warning: Equilibrations failed at Liquid Prod simulation"
                fi
            else
                echo "Error: Equilibrations failed at Liquid Prod preparation"
            fi
        fi

        if [[ -n "$equil_liq_gro" ]]
        then
            echo "Note: replacing gro_liq_path: $gro_liq_path with equil_liq_gro: $equil_liq_gro..."
            gro_liq_path=$equil_liq_gro
            cp -f $equil_liq_gro ../../
        fi
    fi

    if $bool_equil_fep
    then
        equil_fep_gro=''
        if [[ -n "$grompp_equil_min_fep_path" ]]
        then
            $gmx grompp -f ../../$grompp_equil_min_fep_path -c ../../$gro_fep_path -p ../../$top_fep_path -o equil_fep_min.tpr
            
            if [[ -f equil_fep_min.tpr ]]
            then
                $gmx mdrun -deffnm equil_fep_min
                
                if [[ -f equil_fep_min.gro ]]
                then
                    equil_fep_gro=equil_fep_min.gro
                else
                    echo "Warning: Equilibrations failed at FEP Min simulation"
                fi
            else
                echo "Error: Equilibrations failed at FEP Min preparation"
            fi
        fi

        if [[ -n "$grompp_equil_npt_fep_path" ]]
        then
            if [[ -n "$equil_fep_gro" ]]
            then
                $gmx grompp -f ../../$grompp_equil_npt_fep_path -c $equil_fep_gro -p ../../$top_fep_path -o equil_fep_prod.tpr
            else
                echo "Note: Trying to use gro_fep_path=$gro_fep_path as inputs"
                $gmx grompp -f ../../$grompp_equil_npt_fep_path -c ../../$gro_fep_path -p ../../$top_fep_path -o equil_fep_prod.tpr
            fi

            if [[ -f equil_fep_prod.tpr ]]
            then
                $gmx mdrun -deffnm equil_fep_prod
                
                if [[ -f equil_fep_prod.gro ]]
                then
                    equil_fep_gro=equil_fep_prod.gro
                else
                    echo "Warning: Equilibrations failed at FEP Prod simulation"
                fi
            else
                echo "Error: Equilibrations failed at FEP Prod preparation"
            fi
        fi

        if [[ -n "$equil_fep_gro" ]]
        then
            echo "Note: replacing gro_fep_path: $gro_fep_path with equil_fep_gro: $equil_fep_gro..."
            gro_fep_path=$equil_fep_gro
            cp -f $equil_fep_gro ../../
        fi
    fi

    cd ../../
fi


# Based on LV_HVAP, LV_DES, LV_FEP
if [[ -z "$charge_range_path" ]]
then
    if ! [[ -f charge_range.txt ]]
    then
        echo "Warning: charge_range_path is not setup, now generating..."
        if [[ -n "$top_gas_path" ]]
        then
            top=$top_gas_path
        elif [[ -n "$top_liq_path" ]]
        then
            top=$top_liq_path
        else
            top=$top_fep_path
        fi

        if ! $bool_packmol
        then
            nmatoms=$(sed -n '/atoms/=' $top)
            nmbonds=$(sed -n '/bonds/=' $top)
            IFS=$'\n'
            atomstr=''
            for line in $(sed -n "$nmatoms,${nmbonds}p" gas.top)
            do
                IFS=' '; line=($line)
                if (( ${#line[*]} <= 1 )); then continue; fi

                if ! [[ ${line[0]} =~ \;.* ]]
                then
                    atomstr="$atomstr 1"
                fi
            done
            unset IFS
        fi
        nm=($atomstr)

        #NTOE: DEBUG: maybe duplicated on "atoms" or "bonds"
        echo '# charge_range Generated by GAML' > charge_range.txt
        for ((i=1; $i <= ${#nm[*]}; i++))
        do
            echo "ATOM @  -0.8  0.8" >> charge_range.txt
        done
    fi
    echo "Note: Setting charge_range_path to < charge_range.txt >"
    charge_range_path=charge_range.txt
fi



if [[ $training_cnt == 1 && ! -f PAIR_Charge_$training_cnt.txt ]]
then
    # Initialization
    echo "# GAML_Initialization
command       = charge_gen_scheme
charge_path   = $charge_range_path
offset_list   = $offset_list
counter_list  = $counter_list
symmetry_list = $symmetry_list
pn_limit      = $pn_limit
gennm         = $gennm
nmround       = $nmround
total_charge  = $total_charge
fname         = PAIR_Charge_$training_cnt
threshold     = $threshold
offset_nm     = $offset_nm
bool_neutral  = $bool_neutral
bool_nozero   = $bool_nozero
in_keyword    = ATOM
" > GAML_settingfile-init.txt

    for i in {2..5}
    do
        ((t=$i*3))
        echo y | gaml GAML_settingfile-init.txt &
        pid_gaml=$!
        pktime $pid_gaml $t
        
        if [[ -f PAIR_Charge_$training_cnt.txt ]] 
        then
            break
        fi
    done

    # Check for Initialization
    bool_error=false
    if [[ -f PAIR_Charge_$training_cnt.txt ]]
    then
        tmp=$(cat PAIR_Charge_$training_cnt.txt | grep '^PAIR' | wc -l)
        if (( $tmp <= 0 )); then bool_error=true; fi
    else
        bool_error=true
    fi
    if $bool_error
    then
        echo 'Fatal Error: GAML initialization is failed'
        exit 1
    fi
fi



# fitting file -- VAR_title && VAR_error
TRAININGFILE="# VAR_title
command          = gaml
charge_path      = $charge_range_path
offset_list      = $offset_list
counter_list     = $counter_list
symmetry_list    = $symmetry_list
pn_limit         = $pn_limit
file_path        = MAE_PAIR_total.txt
gennm            = $gennm
nmround          = $nmround
total_charge     = $total_charge
error_tolerance  = VAR_error
fname            = PAIR_Charge
charge_extend_by = $charge_extend_by
threshold        = $threshold
bool_neutral     = $bool_neutral
bool_nozero      = $bool_nozero
bool_abscomp     = $bool_abscomp
cut_keyword      =                  # default: MAE
"

# top file setting -- VAR_toppath && VAR_title && VAR_nm && VAR_stat
TOPPAR="# VAR_title
command       = file_gen_gromacstop 
symmetry_list = $symmetry_list
toppath       = VAR_toppath
charge_path   = PAIR_Charge_VAR_nm.txt
reschoose     = $reschoose
fname         = Topfile_VAR_stat
gennm         =                  # default: None
in_keyword    = PAIR
cut_keyword   =                  # default: MAE
"


# file for GAML_AutoTrain
if ! [[ -f GAML_settingfile-training.txt ]]
then
    echo "$TRAININGFILE" > GAML_settingfile-training.txt
    sed -i "s/VAR_title/GAML_Training/" GAML_settingfile-training.txt
    sed -i "s/VAR_error/$error_tolerance/" GAML_settingfile-training.txt
fi


bool_gamlout=${bool_gamlout:=true}
if $bool_gamlout
then
    echo ""
    k=1
    while true
    do
        if [[ -f gamlout_$k.txt ]]; then ((k++)); else break; fi
    done
    filegaml=gamlout_$k.txt
    echo "Note: GAML IP file: $filegaml"
    echo "# Note: GAML Internal Parameters for training_cnt=$training_cnt

# Overall training parameter control
training_cnt=$training_cnt
training_total_nm=$training_total_nm

gennm=$gennm
error_tolerance=$error_tolerance
MAE=$MAE
nmround=$nmround


# keywords and literature values
gromacs_energy_kw='$gromacs_energy_kw'
literature_value='$literature_value'


# lists being used
symmetry_list='$symmetry_list'
pn_limit='$pn_limit'
counter_list='$counter_list'
offset_list='$offset_list'


# charge range path
charge_range_path=$charge_range_path


# topfiles
top_liq_path=$top_liq_path
top_gas_path=$top_gas_path
top_fep_path=$top_fep_path


# grofiles
gro_liq_path=$gro_liq_path
gro_gas_path=$gro_gas_path
gro_fep_path=$gro_fep_path


# mdpfiles -- Liquid
grompp_min_liq_path=$grompp_min_gas_path
grompp_npt_liq_path=$grompp_npt_liq_path
grompp_nvt_liq_path=$grompp_nvt_liq_path
grompp_prod_liq_path=$grompp_prod_liq_path


# mdpfiles -- Gas
grompp_min_gas_path=$grompp_min_gas_path
grompp_prod_gas_path=$grompp_prod_gas_path


# mdpfiles -- FEP
grompp_fep_min_lbfgs_path=$grompp_fep_min_lbfgs_path
grompp_fep_min_steep_path=$grompp_fep_min_steep_path
grompp_fep_npt_path=$grompp_fep_npt_path
grompp_fep_nvt_path=$grompp_fep_nvt_path
grompp_fep_prod_path=$grompp_fep_prod_path


# Residue
reschoose=$reschoose
molecules_number=$molecules_number
molecules_mass=$molecules_mass
box_length=$box_length


# solvents
solvent_resname=$solvent_resname
solvent_molecules_number=$solvent_molecules_number
solvent_molecules_mass=$solvent_molecules_mass
solvent_density=$solvent_density
solvent_box_length=$solvent_box_length


# package commands
gmx=$gmx
packmol=$packmol


# pre-equilibrations
bool_equil=$bool_equil

bool_equil_liq=$bool_equil_liq
grompp_equil_min_liq_path=$grompp_equil_min_liq_path
grompp_equil_npt_liq_path=$grompp_equil_npt_liq_path

bool_equil_gas=$bool_equil_gas
grompp_equil_min_gas_path=$grompp_equil_min_gas_path
grompp_equil_prod_gas_path=$grompp_equil_prod_gas_path

bool_equil_fep=$bool_equil_fep
grompp_equil_min_fep_path=$grompp_equil_min_fep_path
grompp_equil_npt_fep_path=$grompp_equil_npt_fep_path


# gmx-top [defaults] parameters
defaults_nbfunc=$defaults_nbfunc
defaults_combrule=$defaults_combrule
defaults_genpair=$defaults_genpair
defaults_fudgelj=$defaults_fudgelj
defaults_fudgeqq=$defaults_fudgeqq

# some other parameters
bool_abscomp=$bool_abscomp
bool_neutral=$bool_neutral
bool_nozero=$bool_nozero
charge_extend_by=$charge_extend_by
offset_nm=$offset_nm
ratio=$ratio
threshold=$threshold

#bool_packmol=$bool_packmol
#bool_packmol_solvent=$bool_packmol_solvent
#LENLAMBDAS=$LENLAMBDAS
#LV_DES=$LV_DES
#LV_FEP=$LV_FEP
#LV_HVAP=$LV_HVAP
" > $filegaml

fi


if $bool_check
then
    CWD=$(pwd)
    CWD=${CWD##*/}
    echo "Note: Current Work Directory < $CWD >"
    echo "LV_DES  = < $LV_DES >"
    echo "LV_HVAP = < $LV_HVAP >"
    echo "LV_FEP  = < $LV_FEP >"
    echo "LENLAMBDAS   = < $LENLAMBDAS >"
	echo "training_cnt = < $training_cnt >"
    echo ""
    echo "Checking-Done"
    exit 0
fi


while (( $training_cnt <= $training_total_nm ))
do


# Avoid any duplicated training
while true
do
    # Gromacs topology files generation
    TOPFILE=Topfile_train_$training_cnt

    if [[ -d $TOPFILE ]]
    then
        echo "Note: Altering training_cnt by increasing by one"
        ((training_cnt++))
    else
        break
    fi
done


if [[ $training_cnt != 1 && ! -f PAIR_Charge_$training_cnt.txt ]]
then
    for i in {1..3}
    do
        ((t=$i*5))
        echo y | gaml GAML_settingfile-training.txt &
        pid_gaml=$!
        pktime $pid_gaml $t
        
        if [[ -f PAIR_Charge_$training_cnt.txt ]] 
        then
            break
        fi
    done

    # Check for training file generation
    if ! [[ -f PAIR_Charge_$training_cnt.txt ]]
    then
        echo 'Warning: GAML training is failed at training number'
        echo "      $training_cnt"
        echo "GAML: Fitting the error_tolerance parameters"

        for tmp in 0.8 1.0 1.2 1.6 2.0 3.0 nan
        do
            echo "$TRAININGFILE" > GAML_settingfile-training-fit.txt
            sed -i "s/VAR_title/GAML_Training-fitting/" GAML_settingfile-training-fit.txt
            sed -i "s/VAR_error/$tmp/" GAML_settingfile-training-fit.txt
            
            echo y | gaml GAML_settingfile-training-fit.txt &
            pid_gaml=$!
            pktime $pid_gaml 30

            if [[ -f PAIR_Charge_$training_cnt.txt ]] 
            then
                break
            fi
        done
    fi
fi


bool_error=false
if [[ -f PAIR_Charge_$training_cnt.txt ]]
then
    tmp=$(cat PAIR_Charge_$training_cnt.txt | grep '^PAIR' | wc -l)
    if (( $tmp <= 0 )); then bool_error=true; fi
else
    bool_error=true
fi
if $bool_error
then
    echo "Fatal Error: GAML training is failed at training_cnt=$training_cnt"
    exit 1
fi


mkdir $TOPFILE
cd $TOPFILE
cp ../PAIR_Charge_$training_cnt.txt .

gennm_new=0
if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
then
    echo "$TOPPAR" > GAML_settingfile-gentop-liquid.txt
    sed -i "s/VAR_title/GAML-Liquid/" GAML_settingfile-gentop-liquid.txt
    sed -i "s/VAR_toppath/$top_liq_path/" GAML_settingfile-gentop-liquid.txt
    sed -i "s/VAR_nm/$training_cnt/" GAML_settingfile-gentop-liquid.txt
    sed -i "s/VAR_stat/liq/" GAML_settingfile-gentop-liquid.txt

    cp ../$top_liq_path .
    echo y | gaml GAML_settingfile-gentop-liquid.txt

    tmp=$(ls | grep 'Topfile_liq' | wc -l)
    if (( $tmp <= 0 ))
    then
        echo "Fatal Error: GAML failed at top-liq generation at training_cnt=$training_cnt"
        exit 1
    fi
    ((gennm_new=$tmp-1))
fi

if [[ -n "$LV_HVAP" ]]
then
    echo "$TOPPAR" > GAML_settingfile-gentop-gas.txt
    sed -i "s/VAR_title/GAML-Gas/" GAML_settingfile-gentop-gas.txt
    sed -i "s/VAR_toppath/$top_gas_path/" GAML_settingfile-gentop-gas.txt
    sed -i "s/VAR_nm/$training_cnt/" GAML_settingfile-gentop-gas.txt
    sed -i "s/VAR_stat/gas/" GAML_settingfile-gentop-gas.txt

    cp ../$top_gas_path .
    echo y | gaml GAML_settingfile-gentop-gas.txt

    tmp=$(ls | grep 'Topfile_gas' | wc -l)
    if (( $tmp <= 0 ))
    then
        echo "Fatal Error: GAML failed at top-gas generation at training_cnt=$training_cnt"
        exit 1
    fi
    if (( $tmp - 1 > $gennm_new )); then (( gennm_new = $tmp - 1)); fi
fi

if [[ -n "$LV_FEP" ]]
then
    echo "$TOPPAR" > GAML_settingfile-gentop-fep.txt
    sed -i "s/VAR_title/GAML-FEP/" GAML_settingfile-gentop-fep.txt
    sed -i "s/VAR_toppath/$top_fep_path/" GAML_settingfile-gentop-fep.txt
    sed -i "s/VAR_nm/$training_cnt/" GAML_settingfile-gentop-fep.txt
    sed -i "s/VAR_stat/fep/" GAML_settingfile-gentop-fep.txt

    cp ../$top_fep_path .
    echo y | gaml GAML_settingfile-gentop-fep.txt

    tmp=$(ls | grep 'Topfile_fep' | wc -l)
    if (( $tmp <= 0 ))
    then
        echo "Fatal Error: GAML failed at top-fep generation at training_cnt=$training_cnt"
        exit 1
    fi
    if (( $tmp - 1 > $gennm_new )); then (( gennm_new = $tmp - 1)); fi
fi

# update
if [[ $gennm_new != $gennm ]]; then { echo "Note: Update gennm < $gennm > to gennm_new < $gennm_new >";
                                      gennm=$gennm_new; } fi
cd ../  # cd outof $TOPFILE


TRAINFOLDER=Training_$training_cnt
mkdir $TRAINFOLDER
# Result collection
rstFile=RST_EHD_$training_cnt.txt
if [[ -f RST_EHD_$training_cnt.txt ]]
then
    cnt=1
    while true
    do
        if [[ ! -f RST_EHD_${training_cnt}-bak-$cnt.txt ]]; then break; fi
        ((cnt++))
    done
    echo "Note: Renaming file < RST_EHD_${training_cnt}.txt > to < RST_EHD_${training_cnt}-bak-$cnt.txt >"
    mv RST_EHD_$training_cnt.txt RST_EHD_${training_cnt}-bak-$cnt.txt
fi
echo '' > $rstFile
cd $TRAINFOLDER

for ((i=1; $i <= $gennm; i++))
do
    # A global parameter to control whether to continue
    bool_continue=true
    
    # Note: COUNT_$i is the keyword used for referring
    echo "COUNT_$i" >> ../$rstFile

    # Liquid phase simulation
    if [[ -n "$LV_DES" || -n "$LV_HVAP" ]]
    then
        dirliq=Liquid_$i
        mkdir $dirliq
        cd $dirliq
        
        if [[ -n "$grompp_min_liq_path" ]]
        then
            $gmx grompp -f ../../$grompp_min_liq_path -c ../../$gro_liq_path \
                        -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_min.tpr
            if [[ -f liq_min.tpr ]]
            then
                $gmx mdrun -deffnm liq_min
                wait

                if ! [[ -f liq_min.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at liquid minimization simulations"
                    echo "Error Training number $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Error: Failed at liquid minimization preparation"
                echo "Error Training number $training_cnt $i"
            fi
        fi
        
        if $bool_continue && [[ -n "$grompp_nvt_liq_path" ]]
        then
            if [[ -n "$grompp_min_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_nvt_liq_path -c liq_min.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_nvt.tpr
            else
                $gmx grompp -f ../../$grompp_nvt_liq_path -c ../../$gro_liq_path \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_nvt.tpr
            fi
            
            if [[ -f liq_nvt.tpr ]]
            then
                $gmx mdrun -deffnm liq_nvt
                wait
                
                if ! [[ -f liq_nvt.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at liquid NVT simulations"
                    echo "Error Training number $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Error: Failed at liquid NVT preparation"
                echo "Error Training number $training_cnt $i"
            fi
        fi
        
        if $bool_continue && [[ -n "$grompp_npt_liq_path" ]] 
        then
            if [[ -n "$grompp_nvt_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_npt_liq_path -c liq_nvt.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            elif [[ -n "$grompp_min_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_npt_liq_path -c liq_min.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            else
                $gmx grompp -f ../../$grompp_npt_liq_path -c ../../$gro_liq_path \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            fi
            
            if [[ -f liq_npt.tpr ]]
            then
                $gmx mdrun -deffnm liq_npt
                wait
                
                if ! [[ -f liq_npt.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at liquid NPT simulations"
                    echo "Error Training number $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Error: Failed at liquid NPT preparation"
                echo "Error Training number $training_cnt $i"
            fi
        fi
        
        if $bool_continue
        then
            if [[ -n "$grompp_npt_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_npt.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            elif [[ -n "$grompp_nvt_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_nvt.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            elif [[ -n "$grompp_min_liq_path" ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_min.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            else
                $gmx grompp -f ../../$grompp_prod_liq_path -c ../../$gro_liq_path \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            fi
        
            if [[ -f liq_prod.tpr ]]
            then
                $gmx mdrun -deffnm liq_prod
                wait
                
                if ! [[ -f liq_prod.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at liquid production simulations"
                    echo "Error Training number $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Error: Failed at liquid production preparation"
                echo "Error Training number $training_cnt $i"
            fi
            
            if $bool_continue && [[ -f liq_prod.edr ]]
            then
                echo {1..22} | $gmx energy -f liq_prod.edr -b $analysis_begintime >> ../../$rstFile
            else
                bool_continue=false
                echo 'Error on liquid-edr-file' >> ../../$rstFile
                echo "Error: bool_continue is set to false due to liq_prod.edr does not exist -- $training_cnt $i Liquid"
            fi
        fi
        
        # Now do the analyzation
        if [[ -n "$LV_DES" ]]
        then
            calc_des=($(grep "Density" ../../$rstFile | head -n $i | tail -n 1))
            calc_des=${calc_des[1]}
            # Only check Decimals
            if [[ "$calc_des" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
            then
                err=$(echo "($calc_des - $LV_DES) / $LV_DES" | bc -l)
                err=$(echo $err | sed 's/-//')
                err=$(echo "$error_tolerance - $err + 0.01" | bc -l | grep '-')
                if [[ -n "$err" ]]
                then
                    bool_continue=false
                    echo "Warning: bool_continue is set to false due to error_tolerance on LV_DES -- $training_cnt $i Liquid"
                fi
            else
                bool_continue=false
                echo "Warning: bool_continue is set to false due to calc_des is not a number -- $training_cnt $i Liquid"
            fi
        fi
        cd ../  #cd outof $dirliq
    fi  # "LV_DES || LV_HVAP"
    
    
    # Gas phase simulation
    if $bool_continue && [[ -n "$LV_HVAP" ]]
    then
        dirgas=Gas_$i
        mkdir $dirgas
        cd $dirgas
        
        if [[ -n "$grompp_min_gas_path" ]]
        then
            $gmx grompp -f ../../$grompp_min_gas_path -c ../../$gro_gas_path \
                        -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_min.tpr
        
            if [[ -f gas_min.tpr ]]
            then
                $gmx mdrun -deffnm gas_min
                wait

                if ! [[ -f gas_min.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at gas minimization simulation"
                    echo "Error Training number $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Error: Failed at gas minimization preparation"
                echo "Error Training number $training_cnt $i"
            fi
        fi
        
        if $bool_continue && [[ -n "$grompp_min_gas_path" ]]
        then
            $gmx grompp -f ../../$grompp_prod_gas_path -c gas_min.gro \
                        -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_prod.tpr
        else
            $gmx grompp -f ../../$grompp_prod_gas_path -c ../../$gro_gas_path \
                        -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_prod.tpr
        fi
        
        if [[ -f gas_prod.tpr ]]
        then
            $gmx mdrun -deffnm gas_prod
            wait
            
            if ! [[ -f gas_prod.gro ]]
            then
                bool_continue=false
                echo "Error: Failed at gas production simulation"
                echo "Error Training number $training_cnt $i"
            fi
        else
            bool_continue=false
            echo "Error: Failed at gas production preparation"
            echo "Error Training number $training_cnt $i"
        fi
        
        if $bool_continue && [[ -f gas_prod.edr ]]
        then
            echo {1..14} | $gmx energy -f gas_prod.edr -b $analysis_begintime >> ../../$rstFile
            
            pv=($(sed -n "/COUNT_$i/,\$p" ../../$rstFile | grep 'Potential'))
            lenpv=${#pv[*]}
            if (( $lenpv == 12 ))
            then
                pvliq=${pv[1]}
                pvgas=${pv[7]}
                
                if [[ "$pvliq" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ && "$pvgas" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
                then
                    err=$(echo "$pvgas - $pvliq / $molecules_number" | bc -l | sed 's/-//')
                    err=$(echo "($err - $LV_HVAP) / $LV_HVAP" | bc -l | sed 's/-//')
                    err=$(echo "$error_tolerance - $err + 0.01" | bc -l | grep '-')
                    if [[ -n "$err" ]]
                    then
                        bool_continue=false
                        echo "Warning: bool_continue is set to false due to error_tolerance on LV_HVAP -- $training_cnt $i Gas"
                    fi
                else
                    bool_continue=false
                    echo "Warning: bool_continue is set to false due to pvliq or pvgas is not a number -- $training_cnt $i Gas"
                fi
            else
                bool_continue=false
                echo "Error: bool_continue is set to false due to lenpv is not equal to 12 -- $training_cnt $i Gas"
            fi
        else
            bool_continue=false
            echo 'Error on gas-edr-file' >> ../../$rstFile
            echo "Error: bool_continue is set to false due to gas_prod.edr does not exist -- $training_cnt $i Gas"
        fi
        cd ../  #cd outof $dirgas
    fi # LV_HVAP
    
    
    # FEP simulations
    if $bool_continue && [[ -n "$LV_FEP" ]]
    then
        dirfep=FEP_$i
        mkdir $dirfep
        cd $dirfep

        # An array to analysis gmx_bar
        bararray=''
        
        # For new folder, use the same name format;
        #     init_00  if it is less than 100 perturbations
        #     init_000 if it is more than 100 perturbations
        cnt=0
        while (( $cnt < $LENLAMBDAS ))
        do
            if ! $bool_continue; then break; fi
            
            if (( $LENLAMBDAS >= 100 ))
            then
                if (( $cnt < 10 ))
                then
                    dirname=init_00$cnt
                elif (( $cnt <= 99 ))
                then
                    dirname=init_0$cnt
                else
                    dirname=init_$cnt
                fi
            else
                if (( $cnt < 10 )); then dirname=init_0$cnt; else dirname=init_$cnt; fi
            fi
            
            mkdir $dirname
            cd $dirname
            
            if [[ -n "$grompp_fep_min_steep_path" ]]
            then
                cp ../../../$grompp_fep_min_steep_path grompp_fep_min_steep.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_min_steep.mdp)
                if [[ -n "$moltype" ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_min_steep.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_min_steep.mdp)
                if [[ -n "$initlambda" ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_min_steep.mdp
                fi

                $gmx grompp -f grompp_fep_min_steep.mdp -c ../../../$gro_fep_path \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_steep.tpr
                if [[ -f fep_min_steep.tpr ]]
                then
                    $gmx mdrun -deffnm fep_min_steep
                    wait

                    if ! [[ -f fep_min_steep.gro ]]
                    then
                        bool_continue=false
                        echo "Error: Failed at FEP Steep simulation: Lambda $cnt"
                        echo "Error Training number $training_cnt $i"
                    fi
                else
                    bool_continue=false
                    echo "Error: Failed at FEP Steep minimization preparation: Lambda $cnt"
                    echo "Error Training number $training_cnt $i"
                fi
            fi
            
            if $bool_continue && [[ -n "$grompp_fep_min_lbfgs_path" ]]
            then
                cp ../../../$grompp_fep_min_lbfgs_path grompp_fep_min_lbfgs.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_min_lbfgs.mdp)
                if [[ -n "$moltype" ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_min_lbfgs.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_min_lbfgs.mdp)
                if [[ -n "$initlambda" ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_min_lbfgs.mdp
                fi
                
                if [[ -n "$grompp_fep_min_steep" ]]
                then
                    $gmx grompp -f grompp_fep_min_lbfgs.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_lbfgs.tpr
                else
                    $gmx grompp -f grompp_fep_min_lbfgs.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_lbfgs.tpr
                fi
                
                if [[ -f fep_min_lbfgs.tpr ]]
                then
                    $gmx mdrun -deffnm fep_min_lbfgs
                    wait

                    if ! [[ -f fep_min_lbfgs.gro ]]
                    then
                        bool_continue=false
                        echo "Error: Failed at FEP lbfgs simulation: Lambda $cnt"
                        echo "Error Training number $training_cnt $i"
                    fi
                else
                    bool_continue=false
                    echo "Error: Failed at FEP l-bfgs minimization preparation: Lambda $cnt"
                    echo "Error Training number $training_cnt $i"
                fi
            fi
            
            if $bool_continue && [[ -n "$grompp_fep_nvt_path" ]]
            then
                cp ../../../$grompp_fep_nvt_path grompp_fep_nvt.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_nvt.mdp)
                if [[ -n "$moltype" ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_nvt.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_nvt.mdp)
                if [[ -n "$initlambda" ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_nvt.mdp
                fi
                
                if [[ -n "$grompp_fep_min_lbfgs" ]]
                then
                    $gmx grompp -f grompp_fep_nvt.mdp -c fep_min_lbfgs.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                elif [[ -n "$grompp_fep_min_steep" ]]
                then
                    $gmx grompp -f grompp_fep_nvt.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                else
                    $gmx grompp -f grompp_fep_nvt.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                fi
                
                if [[ -f fep_nvt.tpr ]]
                then
                    $gmx mdrun -deffnm fep_nvt
                    wait

                    if ! [[ -f fep_nvt.gro ]]
                    then
                        bool_continue=false
                        echo "Error: Failed at FEP NVT simulation: Lambda $cnt"
                        echo "Error Training number $training_cnt $i"
                    fi
                else
                    bool_continue=false
                    echo "Error: Failed at FEP NVT preparation: Lambda $cnt"
                    echo "Error Training number $training_cnt $i"
                fi
            fi
            
            if $bool_continue && [[ -n "$grompp_fep_npt_path" ]]
            then
                cp ../../../$grompp_fep_npt_path grompp_fep_npt.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_npt.mdp)
                if [[ -n "$moltype" ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_npt.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_npt.mdp)
                if [[ -n "$initlambda" ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_npt.mdp
                fi
                
                if [[ -n "$grompp_fep_nvt" ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_nvt.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                elif [[ -n "$grompp_fep_min_lbfgs" ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_min_lbfgs.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                elif [[ -n "$grompp_fep_min_steep" ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                else
                    $gmx grompp -f grompp_fep_npt.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                fi
                
                if [[ -f fep_npt.tpr ]]
                then
                    $gmx mdrun -deffnm fep_npt
                    wait

                    if ! [[ -f fep_npt.gro ]]
                    then
                        bool_continue=false
                        echo "Error: Failed at FEP NPT simulation: Lambda $cnt"
                        echo "Error Training number $training_cnt $i"
                    fi
                else
                    bool_continue=false
                    echo "Error: Failed at FEP NPT preparation: Lambda $cnt"
                    echo "Error Training number $training_cnt $i"
                fi
            fi
            
            
            if $bool_continue
            then
                cp ../../../$grompp_fep_prod_path grompp_fep_prod.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_prod.mdp)
                if [[ -n "$moltype" ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_prod.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_prod.mdp)
                if [[ -n "$initlambda" ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_prod.mdp
                fi
                
                if [[ -n "$grompp_fep_npt" ]]
                then
                    $gmx grompp -f grompp_fep_prod.mdp -c fep_npt.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
                elif [[ -n "$grompp_fep_nvt" ]]
                then
                    $gmx grompp -f grompp_fep_prod.mdp -c fep_nvt.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
                elif [[ -n "$grompp_fep_min_lbfgs" ]]
                then
                    $gmx grompp -f grompp_fep_prod.mdp -c fep_min_lbfgs.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
                elif [[ -n "$grompp_fep_min_steep" ]]
                then
                    $gmx grompp -f grompp_fep_prod.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
                else
                    $gmx grompp -f grompp_fep_prod.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
                fi
                
                if [[ -f fep_prod.tpr ]]
                then
                    $gmx mdrun -deffnm fep_prod
                    wait

                    if [[ -f fep_prod.gro && -f fep_prod.xvg ]]
                    then
                        bararray="$bararray $dirname/fep_prod.xvg"
                    else
                        bool_continue=false
                        echo "Error: Failed at FEP production simulation: Lambda $cnt"
                        echo "Error Training number $training_cnt $i"
                    fi
                else
                    bool_continue=false
                    echo "Error: Failed at FEP production preparation: Lambda $cnt"
                    echo "Error Training number $training_cnt $i"
                fi
            fi

            cd ../  # cd outof $dirname
            (( cnt++ ))
        done
        
        
        if $bool_continue
        then
            $gmx bar -f $bararray -b $analysis_begintime -e $analysis_endtime > bar_result.txt
            
            rstvalue=( $(grep 'total' bar_result.txt) )
            rstvalue=${rstvalue[5]}
            
            rstvalue_t=$(echo $rstvalue | sed 's/-//')
            echo "FEP                       $rstvalue" >> ../../$rstFile
            
            if [[ -n "$rstvalue" ]]
            then
                lv_fep_t=$(echo $LV_FEP | sed 's/-//')
                
                err=$(echo "($rstvalue_t - $lv_fep_t) / $lv_fep_t" | bc -l)
                err=$(echo $err | sed 's/-//')
                err=$(echo "$error_tolerance - $err + 0.01" | bc -l | grep '-')
                if [[ -n "$err" ]]
                then
                    bool_continue=false
                    echo "Warning: bool_continue is set to false due to error_tolerance on LV_FEP -- $training_cnt $i"
                fi
            else
                bool_continue=false
                echo "Warning: bool_continue is set to false due to rstvalue is not a number -- $training_cnt $i"
            fi
        fi
        cd ../  # cd outof $dirfep
    fi  # LV_FEP
    
    
    echo '' >> ../$rstFile
    echo '' >> ../$rstFile
done

cd ../  # cd outof $TRAINFOLDER


###TO-PROCESS-MDFILE: resultFile
#
# Generate file MAE_PAIR_$training_cnt
#
if [[ -f MAE_PAIR_$training_cnt.txt ]]
then
    cnt=1
    while true
    do
        if [[ ! -f MAE_PAIR_${training_cnt}-bak-$cnt.txt ]]; then break; fi
        ((cnt++))
    done
    echo "Note: Renaming file < MAE_PAIR_${training_cnt}.txt > to < MAE_PAIR_${training_cnt}-bak-$cnt.txt >"
    mv MAE_PAIR_${training_cnt}.txt MAE_PAIR_${training_cnt}-bak-$cnt.txt
fi

gaml file_gen_mdpotential -s PAIR_Charge_$training_cnt.txt -i $molecules_number \
                          -f $rstFile -kw $gromacs_energy_kw -lv $literature_value \
                          --MAE $MAE -o MAE_PAIR 

if ! [[ -f MAE_PAIR_$training_cnt.txt ]]
then
    echo "Fatal Error: cannot generate MAE_PAIR_$training_cnt.txt"
    exit 1
fi

cat MAE_PAIR_$training_cnt.txt >> MAE_PAIR_total.txt
echo '' >> MAE_PAIR_total.txt
echo '' >> MAE_PAIR_total.txt

if [[ $(grep 'HEAD' MAE_PAIR_$training_cnt.txt) ]]
then
    echo ''
    echo 'Note: The GAML training has been done'
    cat MAE_PAIR_$training_cnt.txt | grep 'HEAD'
    exit 0
fi


# update training_cnt
(( training_cnt++ ))

done # training_done

