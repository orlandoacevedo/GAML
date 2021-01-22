#!/bin/bash

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# version 0.10  :   processing Training result
# version 0.11  :   fix decimal comparison
# version 0.12  :   fix Viscosity extraction values
# version 0.121 :   fix nm larger than 10
# version 0.13  :   add box length
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

# folder, no '/' on last dir
# which folder to train
WORKFOLDER=''

# GROMACS `energy' output file
FILE=rstfile
bool_autoid=false


FILE=${WORKFOLDER}'/'${FILE}



#
# END of user inputs
#

if $bool_autoid
then
    nm=""
    for i in $(ls | grep 'Training_')
    do
        t=${i##*_}
        if [[ "$t" =~ ^[0-9]+$ ]]; then nm="$nm $t"; fi
    done
    nm=($(echo "$nm" | tr ' ' '\n' | sort -r -n))
    nm=${nm[0]}
    FD="Training_Topfile_${nm}/$FILE"
else
    FD=$FILE
fi
if [[ -f "$FD" ]]
then
    echo "Note: Setting FILE to < $FD >"
    echo ''
else
    echo "Error: File < Training_Topfile_${nm}/$FILE > does not exist"
    exit 1
fi


LV_DES=($(grep "@LV_DES" $FD))
if (( ${#LV_DES[*]} == 2 )); then LV_DES=${LV_DES[1]}; else LV_DES=''; fi
LV_ST=($(grep "@LV_ST" $FD))
if (( ${#LV_ST[*]} == 2 )); then LV_ST=${LV_ST[1]}; else LV_ST=''; fi
LV_VIS=($(grep "@LV_VIS" $FD))
if (( ${#LV_VIS[*]} == 2 )); then LV_VIS=${LV_VIS[1]}; else LV_VIS=''; fi

if [[ -z "$LV_DES" && -z "$LV_ST" && -z "$LV_VIS" ]]
then
    echo "Error: NO LV value is found OR wrong input rstfile"
    exit 1
fi

# format: line number for content @dir_
linenmlist=()
# format: corresponding extracted content "nm" of @dir_nm
dirnmlist=()
tmp=$(grep -n '@dir_' $FD)
if [[ -z "$tmp" ]]; then { echo "Error: no processing data OR wrong input rstfile"; exit 1; } fi
for i in $tmp
do
    linenmlist+=(${i%%:*})
    dirnmlist+=(${i##*_})
done

tmp=$(cat $FD | wc -l)
linenmlist+=($tmp)


rstlist=()
for ((ndx=1; $ndx<${#linenmlist[*]}; ndx++))
do
    end=${linenmlist[$ndx]}
    ((i=$ndx-1))
    beg=${linenmlist[$i]}
    dirnm=${dirnmlist[$i]}

    line=$(sed -n "${beg},${end}p" $FD | grep -n '@@')
    if [[ -z "$line" ]]; then { rstlist+=("@dir_${dirnm}   NoResults-OR-Broken"); continue; } fi

    # remove all "dir_" and "vis_"
    proline=${line//dir_/}
    proline=${proline//vis_/}

    sublinenmlist=()
    for i in $proline
    do
        if [[ "$i" =~ ^([0-9]*[.])?([0-9]+)?$ ]]
        then
            # double check
            if [[ "$i" =~ ^[0-9]+$ ]]
            then
                if (( $i != $dirnm ))
                then
                    echo "Error: dirnm checking failed"
                    echo "     : values are < $dirnm > and < $i >"
                    echo ""
                    echo "INFO :"
                    echo "$line"
                    exit 1
                fi
            fi
        else
            # double check
            if [[ -z $(echo $i | grep ':') ]]
            then
                echo "Error: wrong formats for input rstfile"
                echo "INFO :"
                echo "$line"
                exit 1
            fi
            t=${i%%:*}
            ((t=$t+$beg-1))
            sublinenmlist+=($t)
        fi
    done

    tot=$(sed -n "${beg},${end}p" $FD | wc -l)
    ((tot=$tot+$beg-1))
    sublinenmlist+=($tot)

    line="@dir_${dirnm}  "
    for ((k=1; k<${#sublinenmlist[*]}; k++))
    do
        ((tmp=$k-1))
        ((x=${sublinenmlist[$tmp]}))
        ((y=${sublinenmlist[$k]}))

        pstr=$(sed -n "${x}p" $FD)
        if [[ -n $(echo "$pstr" | grep PROD) ]]
        then
            v=($(sed -n "${x},${y}p" $FD | grep Density))
            if [[ -n "${v[1]}" ]]; then line="$line DES ${v[1]}"; else line="$line DES Nan"; fi
        elif [[ -n $(echo "$pstr" | grep SURF) ]]
        then
            xx=($(sed -n "${x},${y}p" $FD | grep 'Pres-XX'))
            yy=($(sed -n "${x},${y}p" $FD | grep 'Pres-YY'))
            zz=($(sed -n "${x},${y}p" $FD | grep 'Pres-ZZ'))
            
            if [[ -n "${xx[1]}" && -n "${yy[1]}" && -n "${zz[1]}" ]]
            then
                line="$line XX ${xx[1]} YY ${yy[1]} ZZ ${zz[1]}"
            else
                line="$line XX Nan YY NaN ZZ NaN"
            fi
        elif [[ -n $(echo "$pstr" | grep VIS) ]]
        then
            tmp=($pstr)
            t=${#tmp[*]}
            ((t--))
            tmp=${tmp[$t]}
            v=($(sed -n "${x},${y}p" $FD | grep Viscos))
            if [[ -n "${v[1]}" ]]; then line="$line $tmp ${v[1]}"; else line="$line $tmp Nan"; fi
        fi
    done

    GROFILE=$WORKFOLDER/dir_${dirnm}/surf.gro
    if [[ -f $GROFILE ]]
    then
        atnm=$(sed -n '2p' $GROFILE)
        ((atnm=$atnm+3))
        boxlen=$(sed -n "${atnm}p" $GROFILE)
        line="$line   BOX $boxlen"
    else
        line="$line   BOX NaN  NaN  NaN"
    fi
    rstlist+=("$line")
done

for ((i=0; $i<${#rstlist[*]}; i++)); do echo "${rstlist[$i]}"; done
echo ""
echo "Note: LV values are"
echo "LV_DES = $LV_DES"
echo "LV_ST  = $LV_ST"
echo "LV_VIS = $LV_VIS"

