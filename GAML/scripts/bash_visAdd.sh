#!/bin/bash
# -*- coding: utf-8 -*-

#BSUB -n 1
#BSUB -q gpu_arg
#BSUB -W 168:00
#BSUB -J IL
#BSUB -P prmt
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -m usr23

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#  For DES
#  version 0.10   :  start
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

# directory
FOLDER=''

# global parameter -- highest priority
bool_check=false

# processing
bool_process=false

# mdpfile
GROMPP=grompp_prod_viscosity_new.mdp


# unit in ps
analysis_beginning_time=20

# cos-acceleration, string
VISCOSNM="0.20  0.25  0.30"

# GROMACS
gmx=gmx



#
# End of user inputs
#
if [[ ! -d $FOLDER ]]; then { echo "Error: FOLDER < $FOLDER > not exist"; exit 1; } fi
if [[ -z "$VISCOSNM" ]]; then { echo "Error: no VISCOSNM is defined"; exit 1; } fi


gmx=${gmx:=gmx}
analysis_beginning_time=${analysis_beginning_time:=0}
type $gmx > /dev/null 2>&1 || { echo "Error: gmx < $gmx > is not found"; exit 1; }

if $bool_check; then bool_process=false; fi
if $bool_process; then bool_check=false; fi
if [[ ! $bool_process && ! -f $GROMPP ]]; then { echo "Error: < vis-mdpfile > does not exist"; exit 1; } fi


# Note: change path
cd $FOLDER

# a string hold all training folder numbers
dirstr=''
chkstr=''
for i in $(ls)
do
    if [[ ! -d $i ]]; then continue; fi

    # get dir_<nm>
    ndx=${i#dir_}
    if ! [[ $ndx =~ ^[0-9]+$ ]]; then continue; fi

    if [[ ! -f $i/prod.gro ]]
    then
        echo "Note: excluding FOLDER < $FOLDER/$i > due to < prod.gro > not exist"
        continue
    elif [[ ! -f $i/top_${ndx}.top ]]
    then
        echo "Note: excluding FOLDER < $FOLDER/$i > due to < top_${ndx}.top > not exist"
        continue
    fi

    dirstr="$dirstr $ndx"

    cd $i
    for j in $VISCOSNM
    do
        if [[ -d vis_$j ]]; then { echo "Note: excluding $FOLDER/$i/vis_$j due to already exist"; continue; } fi
        chkstr="$chkstr  $i/vis_$j"
    done
    cd ../

done
# sort it starting at smallest
dirstr=$(echo $dirstr | tr ' ' '\n' | sort -n)


# check & exit
if $bool_check
then
    echo "Note: checking..."
    echo ''
    echo "Note: FOLDER   < $FOLDER >"
    echo "Note: Will add < $chkstr >"
    echo ''
    echo "Note: Done checking"
    exit 0
fi



# process & exit
if $bool_process
then
    echo "Note: processing..."
    echo '' > rstfile-VIS
    for ndx in $dirstr
    do
        if [[ ! -d dir_$ndx ]]; then continue; fi
        cd dir_$ndx
        echo "@dir_$ndx" >> ../rstfile-VIS
        for vf in $VISCOSNM
        do
            if [[ ! -d vis_$vf ]]; then continue; fi

            cd vis_$vf
            if [[ -f vis.gro && -f vis.edr ]]
            then
                echo "@@VIS dir_${ndx} vis_${vf}" >> ../../rstfile-VIS
                echo {30..42} | $gmx energy -f vis.edr -b $analysis_beginning_time >> ../../rstfile-VIS

                # cleaning
                rm -f energy* \#energy* mdout* \#mdout* step* \#step*
                rm -f vis.log vis.trr vis_prev.cpt vis.cpt
            else
                echo "Note: dir_${ndx} vis_${vf} is broken" >> ../../rstfile-VIS
                rm -f *
            fi
            echo '' >> ../../rstfile-VIS
            cd ../

        done
        cd ../
    done

    echo ''
    echo ''

    # format: "dirnm   visnm   1/visValue": "57   0.15   10.3452"
    dvislist=()

    ## nmlist: hold line numbers for all "@@VIS"
    nmlist=()
    for i in $(grep -n '@@VIS' rstfile-VIS)
    do
        if [[ -n "$(echo $i | grep ':')" ]]; then nmlist+=(${i%%:*}); fi
    done
    nmlist+=($(cat rstfile-VIS | wc -l))

    for ((i=1; $i<${#nmlist[*]}; i++))
    do
        ((j=$i-1))
        beg=${nmlist[j]}
        end=${nmlist[i]}
        visrep=($(sed -n "$beg,${end}p" rstfile-VIS | grep 1/Visco))
        visrep=${visrep[1]}
        if [[ -z "$visrep" ]]; then visrep=NaN; fi

        nm=($(sed -n "${beg}p" rstfile-VIS))
        dirnm=${nm[1]}
        visnm=${nm[2]}

        dvislist+=("$dirnm  $visnm  $visrep")
    done

    # since each array in dvislist format is  "dir_nm    vis_nm   value"
    # collect them for all same dir_nm in a format "dir_nm  vis_nm  value   vis_nm  value ... "
    i=0
    while ((i<${#dvislist[*]}))
    do
        ndx=(${dvislist[$i]})
        idir=${ndx[0]}

        vcol="${ndx[1]}  ${ndx[2]}"

        for ((j=$i+1; $j<${#dvislist[*]}; j++))
        do
            jndx=(${dvislist[$j]})
            jdir=${jndx[0]}
            
            if [[ $jdir == $idir ]]
            then
                vcol="$vcol    ${jndx[1]}  ${jndx[2]}"
            else
                break
            fi
        done

        i=$j

        echo "$idir   $vcol"
    done

    echo ''
    echo ''
    echo "Note: Done processing < $FOLDER >"
    exit 0
fi




# training
for i in $dirstr
do
    cd dir_$i

    for vnm in $VISCOSNM
    do
        if [[ -d vis_$vnm ]]; then continue; fi

        mkdir vis_$vnm
        cd vis_$vnm

        mdpfile=grompp_prod_vis_${vnm}.mdp
        cp ../../../$GROMPP $mdpfile
        sed -i "s/VAR_COS/$vnm/" $mdpfile
        grompp -f $mdpfile -c ../prod.gro -p ../top_${i}.top -o vis.tpr

        if [[ -f vis.tpr ]]
        then
            $gmx mdrun -deffnm vis
            wait
        else
            echo "Warning: on < $FOLDER/dir_$i/vis_$vnm > no < vis_$vnm.tpr >"
        fi

        cd ../
    done

    cd ../
done



