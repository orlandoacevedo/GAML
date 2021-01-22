#!/bin/bash
# -*- coding: utf-8 -*-

#BSUB -n 1
#BSUB -q gpu_arg
#BSUB -W 168:00
#BSUB -J IL
#BSUB -P ionic
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -m usr14


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# version 0.1   LV_DES,  LV_ST, LV_VIS
# version 0.2   Add processing modules, bool_process
# version 0.3   Add bool_minchk to avoid wrong minimization
# version 0.4   Add bool_seltraining for selected training
# version 0.41  Fix bool_process minior error <caused by dir_1>
# version 0.42  Add overflow for bool_check
# version 0.50  Add rstfile & remove bool_process
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

# Density(g/mL)  SurfaceTension(mN/m)  Viscosity(cP)
#      Den      ST     VIS
gromacs_energy_kw="Density  ST"     # ST @ NM celsius
literature_value='            '     # corresponding values

topdir_path=''                      # GROMACS topology folder

gmx=gmx                             # default: gmx

# debug mode -- highest priority
bool_check=false

# pre-minimization
bool_minchk=true

# for selection
bool_seltraining=true

gro_path=box.gro

error_tolerance=0.3
analysis_beginning_time=20         # unit in ps

grompp_min_path=grompp_min.mdp
grompp_npt_path=grompp_npt.mdp
grompp_prod_path=grompp_prod.mdp
grompp_prod_surf_path=grompp_prod_surface.mdp
grompp_prod_vis_path=grompp_prod_viscosity.mdp




#
# END of user inputs
#


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
cmd_array=( gaml $gmx $packmol cd mkdir kill sleep ps grep cat sed wc bc tr sort )
cmdchk ${cmd_array[*]}

if ! $G_EXESTAT; then exit 1; fi


# Check simulation types based on provided files and parameters
kw=($gromacs_energy_kw)
lenkw=${#kw[*]}
lv=($literature_value)
lenlv=${#lv[*]}
if (( $lenkw < $lenlv )); then lenmin=$lenkw; else lenmin=$lenlv; fi

#NOTE: DEBUG: add other properties
LV_DES=''
LV_ST=''
LV_VIS=''
for ((i=0; $i < $lenmin; i++))
do
    if [[ -n $(echo ${kw[$i]} | grep -i 'st') ]]; then LV_ST=${lv[$i]}; fi
    if [[ -n $(echo ${kw[$i]} | grep -i 'den') ]]; then LV_DES=${lv[$i]}; fi
    if [[ -n $(echo ${kw[$i]} | grep -i 'vis') ]]; then LV_VIS=${lv[$i]}; fi
done

if [[ ! -f "$grompp_min_path" ]]; then { echo "Error: parameter grompp_min_path is not defined"; exit 1; } fi
if [[ ! -f "$grompp_npt_path" ]]; then { echo "Error: parameter grompp_npt_path is not defined"; exit 1; } fi

if [[ ! -f "$grompp_prod_path" ]]
then
    if [[ -n "$LV_ST" || -n "$LV_DES" ]]
    then
        echo "Warning: Liquid Prod mdp file does not exist"
        echo "Note: Setting LV_ST and LV_DES to false"
        LV_ST=''
        LV_DES=''
    fi
fi

if [[ ! -f "$grompp_prod_vis_path" && -n "$LV_VIS" ]]
then
    echo "Warning: Viscosity Prod mdp file does not exist"
    echo "Note: Setting LV_VIS to false"
    LV_VIS=''
fi


bool_check=${bool_check:=true}
bool_minchk=${bool_minchk:=true}
echo ""


# global parameter
training_toplist=""
if [[ ! -d $topdir_path ]]; then { echo "Error: TOP folder does not exist"; exit 1; } fi
for name in $(ls $topdir_path)
do
    f=${name##*_}
    f=${f%%\.top}
    if [[ "$f" =~ ^[0-9]+$ ]]; then training_toplist="$training_toplist $f"; fi
done
if [[ -z "$training_toplist" ]]; then { echo "Error: no training topfile is defined"; exit 1; } fi
# sort training_toplist in ascending
training_toplist=$(echo "$training_toplist" | tr ' ' '\n' | sort -n | tr '\n' ' ')

gro_path=${gro_path:=npt.gro}
if [[ ! -f $gro_path ]]; then { echo "Error: gro_path does not exist"; exit 1; } fi

if ! [[ -d Test ]]; then mkdir Test; fi

cd Test
sel=(${training_toplist[*]})
sel=${sel[0]}
if [[ ! -f test_prod.tpr ]]
then
    $gmx grompp -f ../$grompp_prod_path -c ../$gro_path -p ../$topdir_path/top_${sel}.top -o test_prod.tpr
    if [[ ! -f test_prod.tpr ]]
    then
        echo "Error: in preparation of prod"
        exit 1
    fi
fi

bool_prod_st=false
if [[ -n "$LV_ST" ]]
then
    if [[ ! -f test_prod_surf.tpr ]]
    then
        $gmx grompp -f ../$grompp_prod_surf_path -c ../$gro_path -p ../$topdir_path/top_${sel}.top -o test_prod_surf.tpr
        if [[ ! -f test_prod_surf.tpr ]]; then bool_prod_st=true; fi
    fi
fi

bool_prod_vis=false
if [[ -n "$LV_VIS" ]]
then
    cp ../$grompp_prod_vis_path test_prod_vis.mdp
    sed -i "s/VAR_COS/0.1/" test_prod_vis.mdp
    if [[ ! -f test_prod_vis.tpr ]]
    then
        $gmx grompp -f test_prod_vis.mdp -c ../$gro_path -p ../$topdir_path/top_${sel}.top -o test_prod_vis.tpr
        if [[ ! -f test_prod_vis.tpr ]]; then bool_prod_vis=true; fi
    fi
fi
cd ../




if $bool_seltraining
then
    trainnm=${topdir_path}
else
    trainnm=${topdir_path##*_}
    if [[ ! "$trainnm" =~ ^[0-9]+$ ]]; then { echo "Error: wrong < topdir_path > for Training mode"; exit 1; } fi
fi

if [[ -d Training_$trainnm ]]; then { echo "Error: Training folder already exists"; exit 1; } fi

if $bool_check
then

    if $bool_minchk
    then
        if [[ ! -d MINI_$trainnm ]]; then mkdir MINI_$trainnm; fi
        cd MINI_$trainnm
        for i in $training_toplist
        do
            # avoid many training by checking whether log file exists
            if [[ ! -f min_${i}.log ]]
            then
                $gmx grompp -f ../$grompp_min_path -c ../$gro_path -p ../$topdir_path/top_${i}.top -o min_${i}
                $gmx mdrun -deffnm min_${i}
                rm -f step* mdout* min_${i}.edr min_${i}.trr min_${i}.tpr
            fi
        done
        cd ../
    fi

    CWD=$(pwd)
    CWD=${CWD##*/}
    echo "Note: Current Working Directory: < $CWD >"
    echo "Note: The used Top folder  is < $topdir_path >"
    echo "Note: Training folder will be < Training_$trainnm >"
    echo "Note: The files are < $training_toplist >"
    if $bool_prod_st
    then
        echo "Error: on Testing SurfaceTension prod tpr Generating. Setting LV_ST to false"
        LV_ST=''
    fi
    if $bool_prod_vis
    then
        echo "Error: on Testing Viscosity prod tpr Generating. Setting LV_VIS to false"
        LV_VIS=''
    fi
    echo ""
    if [[ -z "$LV_DES" ]]; then echo "Warning: LV_DES is not defined"; else echo "Note: LV_DES = $LV_DES"; fi
    if [[ -z "$LV_ST" ]]; then echo "Warning: LV_ST is not defined"; else echo "Note: LV_ST  = $LV_ST"; fi
    if [[ -z "$LV_VIS" ]]; then echo "Warning: LV_VIS is not defined"; else echo "Note: LV_VIS = $LV_VIS"; fi

    if $bool_minchk
    then
        cd MINI_$trainnm
        echo ""
        cnt=0
        flow=""
        for i in $training_toplist
        do
            info=$(grep 'Norm of force' min_${i}.log)
            force=($info)
            force=$(printf '%f' ${force[4]})

            # make compare
            ntmp=$(echo "1000 - $force" | bc -l)
            if [[ -n "$(echo $ntmp | grep '-')" ]]
            then
                flow="${flow}${i},"
                index="<Overflow>"
            else
                index=""
            fi

            if [[ -f min_${i}.gro ]]
            then
                echo "Top-${i}    $info  $index"
                ((cnt++))
            else
                echo "Top-${i}    $info  <Dropped>"
            fi
        done
        cd ../
        echo ''
        echo "Note: The overflow Top-nms are: <$flow>"
        if $bool_seltraining; then echo "Note: selected training mode is < ON >"; fi
        echo "Note: the total training number will be < $cnt >"
    fi
    exit 0
fi



analysis_beginning_time=${analysis_beginning_time:=0}



#
# Start training under folder Training_$trainnm
#

mkdir Training_$trainnm
cd Training_$trainnm

echo "Result Processing File" > rstfile
echo "" >> rstfile
echo "@Training $trainnm" >> rstfile
echo "@LV_DES $LV_DES" >> rstfile
echo "@LV_ST  $LV_ST" >> rstfile
echo "@LV_VIS $LV_VIS" >> rstfile
echo "" >> rstfile


for training_cnt in $training_toplist
do

    # A global parameter to control whether to continue
    bool_continue=true

    dirname=dir_$training_cnt
    mkdir $dirname
    cd $dirname

    if $bool_minchk
    then
        # only training pair whose gro file exists
        if [[ -f ../../MINI_$trainnm/min_${training_cnt}.gro ]]
        then
            cp ../../MINI_$trainnm/min_${training_cnt}.gro min.gro
        else
            bool_continue=false
        fi
    else
        $gmx grompp -f ../../$grompp_min_path -c ../../$gro_path -p ../../$topdir_path/top_${training_cnt}.top -o min.tpr
        if [[ -f min.tpr ]]
        then
            $gmx mdrun -deffnm min
            wait

            if [[ ! -f min.gro ]]
            then
                bool_continue=false
                echo "Error: Failed at Density minimization simulations -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Error: Failed at Density minimization preparation -- $training_cnt"
        fi
    fi

    if $bool_continue
    then
        $gmx grompp -f ../../$grompp_npt_path -c min.gro -p ../../$topdir_path/top_${training_cnt}.top -o npt.tpr
        
        if [[ -f npt.tpr ]]
        then
            $gmx mdrun -deffnm npt
            wait
            
            if [[ ! -f npt.gro ]]
            then
                bool_continue=false
                echo "Error: Failed at Density NPT simulations -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Error: Failed at Density NPT preparation -- $training_cnt"
        fi
    fi
    
    if $bool_continue
    then
        $gmx grompp -f ../../$grompp_prod_path -c npt.gro -p ../../$topdir_path/top_${training_cnt}.top -o prod.tpr

        if [[ -f prod.tpr ]]
        then
            $gmx mdrun -deffnm prod
            wait
            
            if [[ ! -f prod.gro ]]
            then
                bool_continue=false
                echo "Error: Failed at Density Prod simulation -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Error: Failed at Density Prod preparation -- $training_cnt"
        fi
    fi


    if $bool_continue
    then
        echo "@dir_${training_cnt}" > tmprstfile
        echo "@@PROD dir_${training_cnt}" >> tmprstfile
        echo {1..40} | $gmx energy -f prod.edr -b $analysis_beginning_time >> tmprstfile
        calc_des=($(grep "Density" tmprstfile))
        calc_des=${calc_des[1]}
        # Only check Decimals
        if [[ "$calc_des" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
        then
            err=$(echo "($calc_des / 1000 - $LV_DES) / $LV_DES" | bc -l)
            err=$(echo $err | sed 's/-//')
            err=$(echo "$error_tolerance - $err + 0.01" | bc -l | grep '-')
            if [[ -n "$err" ]]
            then
                bool_continue=false
                echo "Warning: bool_continue is set to false on LV_DES -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Warning: bool_continue is set to false due to calc_des is not a number -- $training_cnt"
        fi
    else
        bool_continue=false
        echo "Error: bool_continue is set to false due to prod.edr does not exist -- $training_cnt"
    fi


    if $bool_continue && [[ -n "$LV_ST" ]]
    then
        cp prod.gro prod_surftmp.gro
        atnm=$(sed -n '2p' prod_surftmp.gro)
        ((atnm=$atnm+3))
        boxlen=($(sed -n "${atnm}p" prod_surftmp.gro))
        boxlen=${boxlen[0]}
        boxnew=$(echo "${boxlen}*3" | bc -l)
        sed -i "${atnm}s/$boxlen/$boxnew/3" prod_surftmp.gro

        $gmx grompp -f ../../$grompp_prod_surf_path -c prod_surftmp.gro -p ../../$topdir_path/top_${training_cnt}.top -o surf.tpr

        if [[ -f surf.tpr ]]
        then
            $gmx mdrun -deffnm surf
            wait
            
            if [[ ! -f surf.gro ]]
            then
                bool_continue=false
                echo "Error: Failed at SurfaceTension Prod simulation -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Error: Failed at SurfaceTension Prod preparation -- $training_cnt"
        fi
    fi

    if $bool_continue
    then
        echo '' >> tmprstfile
        echo '' >> tmprstfile
        echo "@@SURF dir_${training_cnt}" >> tmprstfile
        echo {1..35} | $gmx energy -f surf.edr -b $analysis_beginning_time >> tmprstfile
        
        calc_xx=($(grep "Pres-XX" tmprstfile | tail -n 1))
        calc_xx=${calc_xx[1]}
        if [[ "$calc_xx" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
        then
            calc_yy=($(grep "Pres-YY" tmprstfile | tail -n 1))
            calc_yy=${calc_yy[1]}
            if [[ "$calc_yy" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
            then
                calc_zz=($(grep "Pres-ZZ" tmprstfile | tail -n 1))
                calc_zz=${calc_zz[1]}
                if ! [[ "$calc_xx" =~ ^[+-]?([0-9]*[.])?([0-9]+)?$ ]]
                then
                    bool_continue=false
                    echo "Error: Pres-ZZ is not a number -- $training_cnt"
                fi
            else
                bool_continue=false
                echo "Error: Pres-YY is not a number -- $training_cnt"
            fi
        else
            bool_continue=false
            echo "Error: Pres-XX is not a number -- $training_cnt"
        fi

        if $bool_continue
        then
            calc_surf=$(echo "$boxnew / 20 * ($calc_zz - ( $calc_xx + $calc_yy ) / 2)" | bc -l)
            err=$(echo "($calc_surf - $LV_ST) / $LV_ST" | bc -l)
            err=$(echo $err | sed 's/-//')
            err=$(echo "$error_tolerance - $err + 0.01" | bc -l | grep '-')
            if [[ -n "$err" ]]
            then
                bool_continue=false
                echo "Warning: bool_continue is set to false on LV_ST -- $training_cnt"
            fi
        fi
    fi


    if $bool_continue && [[ -n "$LV_VIS" ]]
    then

        for i in 0.2
        do
            mkdir vis_${i}
            cd vis_${i}

            cp ../../../$grompp_prod_vis_path grompp_prod_vis_${i}.mdp
            sed -i "s/VAR_COS/$i/" grompp_prod_vis_${i}.mdp

            $gmx grompp -f grompp_prod_vis_${i}.mdp -c ../prod.gro -p ../../../$topdir_path/top_${training_cnt}.top -o vis.tpr
            
            if [[ -f vis.tpr ]]
            then
                $gmx mdrun -deffnm vis
                wait
                
                if [[ ! -f vis.gro ]]
                then
                    bool_continue=false
                    echo "Error: Failed at SurfaceTension Prod simulation"
                    echo "Error Training number $training_cnt"
                fi
            else
                bool_continue=false
                echo "Error: Failed at SurfaceTension Prod preparation"
                echo "Error Training number $training_cnt"
            fi

            echo '' >> ../tmprstfile
            echo '' >> ../tmprstfile
            echo "@@VIS dir_${training_cnt} vis_${i}" >> ../tmprstfile
            echo {30..42} | $gmx energy -f vis.edr -b $analysis_beginning_time >> ../tmprstfile
            echo "" >> ../tmprstfile

            cd ../
        done
    fi

    cat tmprstfile >> ../rstfile
    echo '' >> ../rstfile
    echo '' >> ../rstfile
    echo '' >> ../rstfile
    cd ../ # outof dirname


done # training_done

