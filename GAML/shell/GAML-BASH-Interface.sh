# Check if the commands exist or not, if not, set `G_EXESTAT=false'
# arguments: cmd-1 cmd-2 cmd-3 ...
#
# Note: it first will initialize global variable `G_EXESTAT' to true,
# then check the input commands, if any one of them is not found, 
# it will set this global variable `G_EXESTAT' to false
cmdchk(){
G_EXESTAT=true
if (( $# > 0 ))
then
    for cmd in $@
    do
        type $cmd > /dev/null 2>&1 || \
            { 
                echo "Warning: command < $cmd > is not found"
                  G_EXESTAT=false
                  break
            }
    done
fi
}

cmd_array=( pwd $gmx cd mkdir kill sleep ps grep cat )
cmdchk ${cmd_array[*]}

if ! $G_EXESTAT; then exit 1; fi

# Kill a process by using its pid after given amount time
# two arguments: 1_pid 2_sleep_time(integer, in seconds)
#
# Note, this function will check the existence of global
# variable `G_EXETIME', if not, set it to `5' 
pktime(){
if [[ -z $G_EXETIME ]]
then
    G_EXETIME=5
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


# Get the starting work path
CWD=$(pwd)


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

for i in {1..5}
do
    echo y | gaml GAML_settingfile-init.txt &
    pid_gaml=$!
    pktime $pid_gaml 8
    
    if [[ -f PAIR_Charge_$training_cnt.txt ]] 
    then
        break
    fi
done

# Check for Initialization
if ! [[ -f PAIR_Charge_$training_cnt.txt ]]
then
    echo 'Error: GAML initialization is failed'
    echo 'Exiting ...'
    exit 1
fi



while (( $training_cnt <= $training_total_nm ))
do

# Gromacs topology files generation
TOPFILE=TopFile_training_$training_cnt
mkdir $TOPFILE
cd $TOPFILE
    cp ../PAIR_Charge_$training_cnt.txt .

    echo "# GAML_AutoTrain-Liquid-part
command       = file_gen_gromacstop 
symmetry_list = $symmetry_list
toppath       = $top_liq_path
charge_path   = PAIR_Charge_$training_cnt.txt
reschoose     = $reschoose
fname         = Topfile_liq
gennm         =                  # default is None
in_keyword    = PAIR
cut_keyword   =                  # default is MAE
" > GAML_settingfile-gentop-liquid.txt

    cp ../$top_liq_path .
    echo y | gaml GAML_settingfile-gentop-liquid.txt

    echo "# GAML_AutoTrain-Gas-part
command       = file_gen_gromacstop 
symmetry_list = $symmetry_list
toppath       = $top_gas_path
charge_path   = PAIR_Charge_$training_cnt.txt
reschoose     = $reschoose
fname         = Topfile_gas
gennm         =                  # default is None
in_keyword    = PAIR   
cut_keyword   =                  # default is MA
" > GAML_settingfile-gentop-gas.txt

    cp ../$top_gas_path .
    echo y | gaml GAML_settingfile-gentop-gas.txt

cd ../  #cd outof $TOPFILE


TRAINFOLDER=Training_$training_cnt
mkdir $TRAINFOLDER
cd $TRAINFOLDER

i=1
while (( i <= $gennm ))
do
    # Liquid simulation
    dirliq=Liquid_$i
    mkdir $dirliq
    cd $dirliq
    $gmx grompp -f ../../$grompp_min_liq_path -c ../../$gro_liq_path \
         -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_min.tpr
    if ! [[ -f liq_min.tpr ]]
    then
        echo "Error: Failed at liquid minimization preparation"
        echo "Error Training number $training_cnt"
    else
        $gmx mdrun -deffnm liq_min        
        wait

        if ! [[ -f liq_min.gro ]]
        then
            echo "Error: Failed at liquid minimization training"
            echo "Error Training number $training_cnt"
        else
            $gmx grompp -f ../../$grompp_npt_liq_path -c liq_min.gro \
                -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            if ! [[ -f liq_npt.tpr ]]
            then
                echo "Error: Failed at liquid equilibration preparation"
                echo "Error Training number $training_cnt"
            else
                $gmx mdrun -deffnm liq_npt
                wait
                
                if ! [[ -f liq_npt.gro ]]
                then
                    echo "Error: Failed at liquid equilibration training"
                    echo "Error Training number $training_cnt"
                else
                    $gmx grompp -f ../../$grompp_prod_liq_path -c liq_npt.gro \
                        -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
                    if ! [[ -f liq_prod.tpr ]]
                    then
                        echo "Error: Failed at liquid production preparation"
                        echo "Error Training number $training_cnt"
                    else
                        $gmx mdrun -deffnm liq_prod
                        wait
                        
                        if ! [[ -f liq_prod.gro ]]
                        then
                            echo "Error: Failed at liquid production training"
                            echo "Error Training number $training_cnt"
                        fi
                    fi
                fi
            fi
        fi
    fi
    cd ../  #cd outof $dirliq

    # Gas simulation
    dirgas=Gas_$i
    mkdir $dirgas
    cd $dirgas
    $gmx grompp -f ../../$grompp_min_gas_path -c ../../$gro_gas_path \
         -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_min.tpr
    if ! [[ -f gas_min.tpr ]]
    then
        echo "Error: Failed at gas minimization preparation"
        echo "Error Training number $training_cnt"
    else
        $gmx mdrun -deffnm gas_min
        wait

        if ! [[ -f gas_min.gro ]]
        then
            echo "Error: Failed at gas minimization training"
            echo "Error Training number $training_cnt"
        else
            $gmx grompp -f ../../$grompp_prod_gas_path -c gas_min.gro \
                -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_prod.tpr
            if ! [[ -f gas_prod.tpr ]]
            then
                echo "Error: Failed at gas production preparation"
                echo "Error Training number $training_cnt"
            else
                $gmx mdrun -deffnm gas_prod
                wait
                
                if ! [[ -f gas_prod.gro ]]
                then
                    echo "Error: Failed at gas production training"
                    echo "Error Training number $training_cnt"
                fi
            fi
        fi
    fi
    cd ../  #cd outof $dirgas

    (( i++ ))
done


# Result collection
resultFile=$CWD/RESULT_HD_$training_cnt.txt

i=1
while (( $i <= $gennm ))
do
    cd Liquid_$i
    echo COUNT_LIQUID_$i >> $resultFile
    if [[ -f liq_prod.edr ]] 
    then
        echo {1..22} | $gmx energy -f liq_prod.edr >> $resultFile
    else
        echo NONE >> $resultFile
    fi
    cd ../  #cd outof Liquid_$training_cnt
    
    cd Gas_$i
    echo '' >> $resultFile
    echo COUNT_GAS_$i >> $resultFile
    if [[ -f gas_prod.edr ]]
    then
        echo {1..14} | $gmx energy -f gas_prod.edr >> $resultFile
    else
        echo NONE >> $resultFile
    fi
    cd ../  #cd outof Gas_$training_cnt

    (( i++ ))
done

cd ../  #cd outof $TRAINFOLDER



###TO-PROCESS-MDFILE: resultFile
#
# Generate file MAE_PAIR_$training_cnt
#
gaml file_gen_mdpotential -s PAIR_Charge_$training_cnt.txt -i 500 --MAE $MAE -f RESULT_HD_$training_cnt.txt \
        -kw $gromacs_energy_kw -lv $literature_value -o MAE_PAIR



if ! [[ -f MAE_PAIR_$training_cnt.txt ]]
then
    echo "Error: cannot generate MAE_PAIR_$training_cnt.txt"
    echo 'Exiting...'
    exit 1
fi

cat MAE_PAIR_$training_cnt.txt >> MAE_PAIR_total.txt
echo '' >> MAE_PAIR_total.txt
echo '' >> MAE_PAIR_total.txt

if [[ $(grep '^HEAD' MAE_PAIR_$training_cnt.txt) ]]
then
    echo ''
    echo 'The GAML training has been done'
    cat MAE_PAIR_$training_cnt.txt | grep '^HEAD'
    exit 0
fi


# update training_cnt
(( training_cnt++ ))

if ! [[ -f GAML_settingfile_training.txt ]]
then
    echo "# GAML_Training
command          = gaml
charge_path      = $charge_range_path
offset_list      = $offset_list
counter_list     = $counter_list
symmetry_list    = $symmetry_list
pn_limit       = $pn_limit
file_path        = MAE_PAIR_total.txt
gennm            = $gennm
nmround          = $nmround
total_charge     = $total_charge
error_tolerance  = $error_tolerance
fname            = PAIR_Charge     
charge_extend_by = $charge_extend_by
threshold        = $threshold
bool_neutral     = $bool_neutral
bool_nozero      = $bool_nozero
bool_abscomp     = $bool_abscomp
cut_keyword      =                  # default is MAE
" > GAML_settingfile-training.txt
fi

for i in {1..3}
do
    echo y | gaml GAML_settingfile-training.txt &
    pid_gaml=$!
    pktime $pid_gaml 5
    
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
    echo "Fitting the error_tolerance parameters"

    for tmp in 0.5 0.7 0.9 1.0 1.2 1.4 1.6 1.8 2.0 3.0 5.0
    do
        echo "# GAML_Training-fitting
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
error_tolerance  = $tmp
fname            = PAIR_Charge     
charge_extend_by = $charge_extend_by
threshold        = $threshold
bool_neutral     = $bool_neutral
bool_nozero      = $bool_nozero
bool_abscomp     = $bool_abscomp
cut_keyword      =                  # default is MAE
" > GAML_settingfile-training-fit.txt
        
        echo y | gaml GAML_settingfile-training-fit.txt &
        pid_gaml=$!
        pktime $pid_gaml 5

        if [[ -f PAIR_Charge_$training_cnt.txt ]] 
        then
            break
        fi
    done
fi


if ! [[ -f PAIR_Charge_$training_cnt.txt ]]
then
    echo 'Error: GAML training is failed at training number'
    echo "      $training_cnt"
    echo "Exiting..."
    exit 1
fi
done #training_done
