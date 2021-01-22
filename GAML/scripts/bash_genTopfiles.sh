#!/bin/bash

#  version 0.10: start
#  version 0.20: more powerful

CHARGEPATH=''
TOPPATH=topol.top

if [[ -f settingfile-pair.txt ]]
then
    FILE=settingfile-pair.txt
elif [[ -f GAML_settingfile-training-sel.txt ]]
then
    FILE=GAML_settingfile-training-sel.txt
else
    echo "Error: no symmetry_list is defined"
    exit 1
fi



#
# END of user inputs
#

symmetry_list=$(grep 'symmetry_list' $FILE | head -n 1)
symmetry_list=${symmetry_list##*=}

nm=${CHARGEPATH#*_}
nm=${nm//\.*}
TOPFOLDER=Topfile_$nm

if [[ ! -f $CHARGEPATH ]]; then { echo "Error: no charge file"; exit 1; } fi
if [[ ! -f $TOPPATH ]]; then { echo "Error: no top file"; exit 1; } fi
if [[ -z $symmetry_list ]]; then { echo "Error: no symmetry_list"; exit 1; } fi
if [[ -d $TOPFOLDER ]]; then { echo "Error: top folder already exist"; exit 1; } fi


SETTINGFILE="#GAML-DES
command       = file_gen_gromacstop 
toppath       = $TOPPATH
charge_path   = $CHARGEPATH
symmetry_list = $symmetry_list
reschoose     = 
fname         = top
gennm         =                  # default is None
in_keyword    = PAIR
cut_keyword   =                  # default is MAE
"

mkdir $TOPFOLDER
cd $TOPFOLDER
cp ../$CHARGEPATH ../$TOPPATH .
echo "$SETTINGFILE" > settingfile.txt
echo y | gaml settingfile.txt

echo "DONE everything"
