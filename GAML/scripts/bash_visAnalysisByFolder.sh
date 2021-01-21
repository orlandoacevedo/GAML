#!/bin/bash
# -*- coding: utf-8 -*-


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#  For DES
#  version 0.10   :  start
#  version 0.20   :  sort in sequence
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

# directory
FOLDER=''


# unit in ps
analysis_beginning_time=20

# GROMACS
gmx=gmx



#
# End of user inputs
#
if [[ ! -d $FOLDER ]]; then { echo "Error: FOLDER < $FOLDER > not exist"; exit 1; } fi

gmx=${gmx:=gmx}
analysis_beginning_time=${analysis_beginning_time:=0}
type $gmx > /dev/null 2>&1 || { echo "Error: gmx < $gmx > is not found"; exit 1; }


# Note: change path
cd $FOLDER


echo ''
dirstr=''
vislist=()
for i in dir_*
do
    if [[ ! -d $i ]]; then continue; fi
    n=${i#*_}
    if [[ $n =~ ^[0-9]+$ ]]; then dirstr="$dirstr $n"; fi
done

if [[ -z "$dirstr" ]]; then { echo "Warning: no folder will be processed"; exit 1; } fi

dirstr=$(echo "$dirstr" | tr ' ' '\n' | sort -n)
for i in $dirstr
do
    visstr=$(ls dir_$i | grep 'vis_' | tr '\n' ' ')
    echo "Note: will process < vis_$i > : < $visstr >"
done
echo ''

echo "For < $FOLDER >:"
echo "Note: Do you want to continue? y/yes, else not"
read tmp
if [[ -z "$tmp" || ! ( "$tmp" == 'yes' || "$tmp" == 'y' ) ]]
then
    echo "You decided to quit..."
    exit 0
fi



bool_process=true
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


        visstr=''
        for j in vis_*
        do
            if [[ ! -d $j ]]; then continue; fi
            m=${j#*_}
            if [[ $m =~ ^([0-9]*[.])?([0-9]+)?$ ]]; then visstr="$visstr $m"; fi
        done


        for vf in $visstr
        do
            if [[ ! -d vis_$vf ]]; then continue; fi

            cd vis_$vf
            echo "@@VIS dir_${ndx} vis_${vf}" >> ../../rstfile-VIS
            if [[ -f vis.gro && -f vis.edr ]]
            then
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



