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
                echo "Error: command < $cmd > is not found"
                  G_EXESTAT=false
                  break
            }
    done
fi
}

cmd_array=( pwd $gmx cd mkdir kill sleep ps grep cat sed date )
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
date +'%T %B %d %Y'
CWD=$(pwd)


# Check simulation types

if [[ -z $grompp_prod_liq_path || -z $top_liq_path || -z $gro_liq_path ]]
then
    BOOL_LIQ=false
else
    BOOL_LIQ=true
fi

if $BOOL_LIQ
then
    if ! [[ -d Test ]]; then mkdir Test; fi
    cd Test
    if ! [[ -f test_prod_liq.tpr ]]
    then
        $gmx grompp -f ../$grompp_prod_liq_path -c ../$gro_liq_path \
                    -p ../$top_liq_path -o test_prod_liq.tpr
        if ! [[ -f test_prod_liq.tpr ]]; then BOOL_LIQ=false; fi
    fi
    cd ../
fi

if [[ -z $grompp_prod_gas_path || -z $top_gas_path || -z $gro_gas_path ]]
then
    BOOL_GAS=false
else
    BOOL_GAS=true
fi

if $BOOL_GAS
then
    if ! [[ -d Test ]]; then mkdir Test; fi
    cd Test
    if ! [[ -f test_prod_gas.tpr ]]
    then
        $gmx grompp -f ../$grompp_prod_gas_path -c ../$gro_gas_path \
                    -p ../$top_gas_path -o test_prod_gas.tpr
        if ! [[ -f test_prod_gas.tpr ]]; then BOOL_GAS=false; fi
    fi
    cd ../
fi

if [[ -z $grompp_fep_prod_path || -z $top_fep_path || -z $gro_fep_path ]]
then
    BOOL_FEP=false
else
    BOOL_FEP=true
fi

if $BOOL_FEP && [[ -z $reschoose ]]
then
    echo "Error: the parameter reschoose is not set for the FEP simulations"
    echo "Exiting..."
    exit 1
fi


# Get the total number of molecules from $top_liq_path
if $BOOL_LIQ && [[ -n $reschoose ]]
then
    MOLNM=( $(grep -i "^[[:blank:]]*$reschoose" $top_liq_path) )
    MOLNM=${MOLNM[-1]}
    
    if ! [[ $MOLNM =~ ^[0-9]+$ ]]
    then
        echo "Warning: getting the total number of molecules is failed"
        echo "         Please input this number"
        MOLNM=read &
        sleep 30
    fi
fi

if [[ $MOLNM =~ ^[0-9]+$ ]]
then
    echo "GAML: Setting the total number of molecules to $MOLNM"
else
    echo "GAML: Setting the total number of molecules to 500"
    MOLNM=500
fi


if $BOOL_FEP
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
    
    if [[ -z $LENLAMBDAS ]]; then BOOL_FEP=false; fi
    
    if $BOOL_FEP
    then
        if ! [[ -d Test ]]; then mkdir Test; fi
        cd Test
        if ! [[ -f test_prod_fep.tpr ]]
        then
            cp ../$grompp_fep_prod_path test_grompp_fep_prod.mdp
            moltype=$(grep '^[[:blank:]]*couple[-_]moltype' test_grompp_fep_prod.mdp)
            if [[ -n $moltype ]]
            then
                sed -i "s@$moltype@couple-moltype    = $reschoose@" test_grompp_fep_prod.mdp
            fi
            initlambda=$(grep '^[[:blank:]]*init_lambda_state' test_grompp_fep_prod.mdp)
            if [[ -n $initlambda ]]
            then
                sed -i "s@$initlambda@init_lambda_state    = 0@" test_grompp_fep_prod.mdp
            fi
            
            $gmx grompp -f test_grompp_fep_prod.mdp -c ../$gro_fep_path \
                        -p ../$top_fep_path -o test_prod_fep.tpr
            if ! [[ -f test_prod_fep.tpr ]]; then BOOL_FEP=false; fi
        fi
        cd ../
    fi
fi


if ! $BOOL_LIQ && ! $BOOL_GAS && ! $BOOL_FEP
then
    echo 'Error: No training job is set, exiting...'
    exit 1
fi


if ! [[ -f PAIR_Charge_$training_cnt.txt ]]
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
        echo 'Exiting...'
        exit 1
    fi
fi


while (( $training_cnt <= $training_total_nm ))
do

# Gromacs topology files generation
TOPFILE=Topfile_train_$training_cnt
mkdir $TOPFILE
cd $TOPFILE
    cp ../PAIR_Charge_$training_cnt.txt .

    if $BOOL_LIQ
    then
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
    fi

    if $BOOL_GAS
    then
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
    fi

    if $BOOL_FEP
    then
        echo "# GAML_AutoTrain-FEP-part
command       = file_gen_gromacstop 
symmetry_list = $symmetry_list
toppath       = $top_fep_path
charge_path   = PAIR_Charge_$training_cnt.txt
reschoose     = $reschoose
fname         = Topfile_fep
gennm         =                  # default is None
in_keyword    = PAIR   
cut_keyword   =                  # default is MA
" > GAML_settingfile-gentop-fep.txt

        cp ../$top_fep_path .
        echo y | gaml GAML_settingfile-gentop-fep.txt
    fi
cd ../  # cd outof $TOPFILE



TRAINFOLDER=Training_$training_cnt
mkdir $TRAINFOLDER
cd $TRAINFOLDER

i=1
while (( $i <= $gennm ))
do
    # Liquid phase simulation
    if $BOOL_LIQ
    then
        dirliq=Liquid_$i
        mkdir $dirliq
        cd $dirliq
        
        if [[ -n $grompp_min_liq_path ]]
        then
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
                    echo "Error: Failed at liquid minimization simulations"
                    echo "Error Training number $training_cnt"
                fi
            fi
        fi
        
        bool_nvt=true
        if [[ -n $grompp_nvt_liq_path ]]
        then
            if [[ -n $grompp_min_liq_path ]]
            then
                if [[ -f liq_min.gro ]]
                then
                    $gmx grompp -f ../../$grompp_nvt_liq_path -c liq_min.gro \
                                -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_nvt.tpr
                else
                    bool_nvt=false
                fi
            else
                $gmx grompp -f ../../$grompp_nvt_liq_path -c ../../$gro_liq_path \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_nvt.tpr
            fi
            
            if ! [[ -f liq_nvt.tpr ]]
            then
                if $bool_nvt
                then
                    echo "Error: Failed at liquid NVT preparation"
                    echo "Error Training number $training_cnt"
                else
                    bool_nvt=false
                fi
            else
                $gmx mdrun -deffnm liq_nvt
                wait
                
                if ! [[ -f liq_nvt.gro ]]
                then
                    bool_nvt=false
                    echo "Error: Failed at liquid NVT simulations"
                    echo "Error Training number $training_cnt"
                fi
            fi
        fi
        
        bool_npt=true
        if [[ -n $grompp_npt_liq_path ]] 
        then
            if [[ -n $grompp_nvt_liq_path ]]
            then
                if [[ -f liq_nvt.gro ]]
                then
                    $gmx grompp -f ../../$grompp_npt_liq_path -c liq_nvt.gro \
                                -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
                else
                    bool_npt=false
                fi
            elif [[ -n $grompp_min_liq_path ]]
            then
                if [[ -f liq_min.gro ]]
                then
                    $gmx grompp -f ../../$grompp_npt_liq_path -c liq_min.gro \
                                -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
                else
                    bool_npt=false
                fi
            else
                $gmx grompp -f ../../$grompp_npt_liq_path -c ../../$gro_liq_path \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            fi
            
            if ! [[ -f liq_npt.tpr ]]
            then
                if $bool_npt
                then
                    echo "Error: Failed at liquid NPT preparation"
                    echo "Error Training number $training_cnt"
                else
                    bool_npt=false
                fi
            else
                $gmx mdrun -deffnm liq_npt
                wait
                
                if ! [[ -f liq_npt.gro ]]
                then
                    bool_npt=false
                    echo "Error: Failed at liquid NPT simulations"
                    echo "Error Training number $training_cnt"
                fi
            fi
        fi
        
        bool_prod=true
        if [[ -n $grompp_npt_liq_path ]]
        then
            if [[ -f liq_npt.gro ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_npt.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            else
                bool_prod=false
            fi
        elif [[ -n $grompp_nvt_liq_path ]]
        then
            if [[ -f liq_nvt.gro ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_nvt.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
            else
                bool_prod=false
            fi
        elif [[ -n $grompp_min_liq_path ]]
        then
            if [[ -f liq_min.gro ]]
            then
                $gmx grompp -f ../../$grompp_prod_liq_path -c liq_min.gro \
                            -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_npt.tpr
            else
                bool_prod=false
            fi
        else
            $gmx grompp -f ../../$grompp_prod_liq_path -c ../../$gro_liq_path \
                        -p ../../$TOPFILE/Topfile_liq_$i.top -o liq_prod.tpr
        fi
        
        if ! [[ -f liq_npt.tpr ]]
        then
            if $bool_prod
            then
                echo "Error: Failed at liquid production preparation"
                echo "Error Training number $training_cnt"
            fi
        else
            $gmx mdrun -deffnm liq_prod
            wait
            
            if ! [[ -f liq_prod.gro ]]
            then
                echo "Error: Failed at liquid production simulations"
                echo "Error Training number $training_cnt"
            fi
        fi
        cd ../  #cd outof $dirliq
    fi  # BOOL_LIQ
    
    
    # Gas phase simulation
    if $BOOL_GAS
    then
        dirgas=Gas_$i
        mkdir $dirgas
        cd $dirgas
        
        bool_min=true
        if [[ -n $grompp_min_gas_path ]]
        then
            $gmx grompp -f ../../$grompp_min_gas_path -c ../../$gro_gas_path \
                        -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_min.tpr
        
            if ! [[ -f gas_min.tpr ]]
            then
                bool_min=false
                echo "Error: Failed at gas minimization preparation"
                echo "Error Training number $training_cnt"
            else
                $gmx mdrun -deffnm gas_min
                wait

                if ! [[ -f gas_min.gro ]]
                then
                    bool_gas=false
                    echo "Error: Failed at gas minimization simulation"
                    echo "Error Training number $training_cnt"
                fi
            fi
        fi
        
        bool_prod=true
        if [[ -n $grompp_min_gas_path ]]
        then
            if [[ -f gas_min.gro ]]
            then
                $gmx grompp -f ../../$grompp_prod_gas_path -c gas_min.gro \
                            -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_prod.tpr
            else
                bool_prod=false
            fi
        else
            $gmx grompp -f ../../$grompp_prod_gas_path -c ../../$gro_gas_path \
                        -p ../../$TOPFILE/Topfile_gas_$i.top -o gas_prod.tpr
        fi
        
        if ! [[ -f gas_prod.tpr ]]
        then
            if $bool_prod
            then
                echo "Error: Failed at gas production preparation"
                echo "Error Training number $training_cnt"
            fi
        else
            $gmx mdrun -deffnm gas_prod
            wait
            
            if ! [[ -f gas_prod.gro ]]
            then
                echo "Error: Failed at gas production simulation"
                echo "Error Training number $training_cnt"
            fi
        fi
        cd ../  #cd outof $dirgas
    fi # BOOL_GAS
    
    
    # FEP simulations
    if $BOOL_FEP
    then
        dirfep=FEP_$i
        mkdir $dirfep
        cd $dirfep
        
        # Local boolean parameter
        # if any one of those FEP simulations is failed/broken
        # break the loop
        bool_fep_local=true

        # For new folder, use the same name format;
        #     init_00  if it is less than 100 perturbations
        #     init_000 if it is more than 100 perturbations
        cnt=0
        while (( $cnt < $LENLAMBDAS ))
        do
            if ! $bool_fep_local; then break; fi
            
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
                if (( $cnt < 10 ))
                then
                    dirname=init_0$cnt
                else
                    dirname=init_$cnt
                fi
            fi
            
            mkdir $dirname
            cd $dirname
            
            bool_min_steep=true
            if [[ -n $grompp_fep_min_steep_path ]]
            then
                cp ../../../$grompp_fep_min_steep_path grompp_fep_min_steep.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_min_steep.mdp)
                if [[ -n $moltype ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_min_steep.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_min_steep.mdp)
                if [[ -n $initlambda ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_min_steep.mdp
                fi

                $gmx grompp -f grompp_fep_min_steep.mdp -c ../../../$gro_fep_path \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_steep.tpr
                if ! [[ -f fep_min_steep.tpr ]]
                then
                    bool_min_steep=false
                    echo "Error: Failed at FEP Steep minimization preparation"
                    echo "Error Training number $training_cnt"
                else
                    $gmx mdrun -deffnm fep_min_steep
                    wait

                    if ! [[ -f fep_min_steep.gro ]]
                    then
                        bool_min_steep=false
                        echo "Error: Failed at FEP Steep simulation"
                        echo "Error Training number $training_cnt"
                    fi
                fi
            fi
            
            bool_min_lbfgs=true
            if [[ -n $grompp_fep_min_lbfgs_path ]]
            then
                cp ../../../$grompp_fep_min_lbfgs_path grompp_fep_min_lbfgs.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_min_lbfgs.mdp)
                if [[ -n $moltype ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_min_lbfgs.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_min_lbfgs.mdp)
                if [[ -n $initlambda ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_min_lbfgs.mdp
                fi
                
                if [[ -f fep_min_steep.gro ]]
                then
                    $gmx grompp -f grompp_fep_min_lbfgs.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_lbfgs.tpr
                else
                    $gmx grompp -f grompp_fep_min_lbfgs.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_min_lbfgs.tpr
                fi
                
                if ! [[ -f fep_min_lbfgs.tpr ]]
                then
                    bool_min_lbfgs=false
                    if $bool_min_steep
                    then
                        echo "Error: Failed at FEP l-bfgs minimization preparation"
                        echo "Error Training number $training_cnt"
                    fi
                else
                    $gmx mdrun -deffnm fep_min_lbfgs
                    wait

                    if ! [[ -f fep_min_lbfgs.gro ]]
                    then
                        bool_min_lbfgs=false
                        echo "Error: Failed at FEP lbfgs simulation"
                        echo "Error Training number $training_cnt"
                    fi
                fi
            fi
            
            bool_nvt=true
            if [[ -n $grompp_fep_nvt_path ]]
            then
                cp ../../../$grompp_fep_nvt_path grompp_fep_nvt.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_nvt.mdp)
                if [[ -n $moltype ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_nvt.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_nvt.mdp)
                if [[ -n $initlambda ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_nvt.mdp
                fi
                
                if [[ -f fep_min_lbfgs.gro ]]
                then
                    $gmx grompp -f grompp_fep_nvt.mdp -c fep_min_lbfgs.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                elif [[ -f fep_min_steep.gro ]]
                then
                    $gmx grompp -f grompp_fep_nvt.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                else
                    $gmx grompp -f grompp_fep_nvt.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_nvt.tpr
                fi
                
                if ! [[ -f fep_nvt.tpr ]]
                then
                    bool_nvt=false
                    if $bool_min_lbfgs
                    then
                        echo "Error: Failed at FEP NVT preparation"
                        echo "Error Training number $training_cnt"
                    fi
                else
                    $gmx mdrun -deffnm fep_nvt
                    wait

                    if ! [[ -f fep_nvt.gro ]]
                    then
                        bool_nvt=false
                        echo "Error: Failed at FEP NVT simulation"
                        echo "Error Training number $training_cnt"
                    fi
                fi
            fi
            
            bool_npt=true
            if [[ -n $grompp_fep_npt_path ]]
            then
                cp ../../../$grompp_fep_npt_path grompp_fep_npt.mdp
                moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_npt.mdp)
                if [[ -n $moltype ]]
                then
                    sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_npt.mdp
                fi
                initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_npt.mdp)
                if [[ -n $initlambda ]]
                then
                    sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_npt.mdp
                fi
                
                if [[ -f fep_nvt.gro ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_nvt.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                elif [[ -f fep_min_lbfgs.gro ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_min_lbfgs.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                elif [[ -f fep_min_steep.gro ]]
                then
                    $gmx grompp -f grompp_fep_npt.mdp -c fep_min_steep.gro \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                else
                    $gmx grompp -f grompp_fep_npt.mdp -c ../../../$gro_fep_path \
                                -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_npt.tpr
                fi
                
                if ! [[ -f fep_npt.tpr ]]
                then
                    bool_npt=false
                    if $bool_nvt
                    then
                        echo "Error: Failed at FEP NPT preparation"
                        echo "Error Training number $training_cnt"
                    fi
                else
                    $gmx mdrun -deffnm fep_npt
                    wait

                    if ! [[ -f fep_npt.gro ]]
                    then
                        bool_npt=false
                        echo "Error: Failed at FEP NPT simulation"
                        echo "Error Training number $training_cnt"
                    fi
                fi
            fi
            
            cp ../../../$grompp_fep_prod_path grompp_fep_prod.mdp
            moltype=$(grep '^[[:blank:]]*couple[-_]moltype' grompp_fep_prod.mdp)
            if [[ -n $moltype ]]
            then
                sed -i "s@$moltype@couple-moltype    = $reschoose@" grompp_fep_prod.mdp
            fi
            initlambda=$(grep '^[[:blank:]]*init_lambda_state' grompp_fep_prod.mdp)
            if [[ -n $initlambda ]]
            then
                sed -i "s@$initlambda@init_lambda_state    = $cnt@" grompp_fep_prod.mdp
            fi
            
            if [[ -f fep_npt.gro ]]
            then
                $gmx grompp -f grompp_fep_prod.mdp -c fep_npt.gro \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
            elif [[ -f fep_nvt.gro ]]
            then
                $gmx grompp -f grompp_fep_prod.mdp -c fep_nvt.gro \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
            elif [[ -f fep_min_lbfgs.gro ]]
            then
                $gmx grompp -f grompp_fep_prod.mdp -c fep_min_lbfgs.gro \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
            elif [[ -f fep_min_steep.gro ]]
            then
                $gmx grompp -f grompp_fep_prod.mdp -c fep_min_steep.gro \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
            else
                $gmx grompp -f grompp_fep_prod.mdp -c ../../../$gro_fep_path \
                            -p ../../../$TOPFILE/Topfile_fep_$i.top -o fep_prod.tpr
            fi
            
            if ! [[ -f fep_prod.tpr ]]
            then
                bool_fep_local=false
                if $bool_npt
                then
                    echo "Error: Failed at FEP production preparation"
                    echo "Error Training number $training_cnt"
                fi
            else
                $gmx mdrun -deffnm fep_prod
                wait

                if ! [[ -f fep_prod.gro ]]
                then
                    bool_fep_local=false
                    echo "Error: Failed at FEP production simulation"
                    echo "Error Training number $training_cnt"
                fi
            fi

            cd ../  # cd outof $dirname
            (( cnt++ ))
        done
    cd ../  # cd outof $dirfep
    fi  # BOOL_FEP

    (( i++ ))
done


# Result collection
resultFile=$CWD/RESULT_EHD_$training_cnt.txt

i=1
while (( $i <= $gennm ))
do
    if $BOOL_LIQ
    then
        echo "COUNT_LIQUID_$i" >> $resultFile
        cd Liquid_$i
        if [[ -f liq_prod.edr ]] 
        then
            echo {1..22} | $gmx energy -f liq_prod.edr -b $analysis_begintime >> $resultFile
        else
            echo NONE >> $resultFile
        fi
        cd ../  # cd outof Liquid_$training_cnt
    fi
    
    if $BOOL_FEP
    then
        # Make sure the block keywords 'COUNT' always exist
        if ! $BOOL_LIQ
        then
            echo "COUNT_FEP_$i" >> $resultFile
        fi
        
        cd FEP_$i
        xvgfiles=( init_*/fep_prod.xvg )
        lenxvgfiles=${xvgfile[*]}
        if (( $lenxvgfiles != $LENLAMBDAS ))
        then
            echo NONE >> $resultFile
        else
            $gmx bar -f ${xvgfiles[*]} -b $analysis_begintime \
                     -e $analysis_endtime > result.txt
            
            rstvalue=( $(grep '^total' result.txt) )
            rstvalue=${rstvalue[5]}
            
            if [[ -z $rstvalue ]]
            then
                echo NONE >> $resultFile
            else
                echo "FEP                       $rstvalue" >> $resultFile
            fi
        fi
        cd ../  # cd outof FEP_$training_cnt
    fi
    
    if $BOOL_GAS
    then
        echo '' >> $resultFile
        echo "COUNT_GAS_$i" >> $resultFile
        cd Gas_$i
        if [[ -f gas_prod.edr ]]
        then
            echo {1..14} | $gmx energy -f gas_prod.edr -b $analysis_begintime >> $resultFile
        else
            echo NONE >> $resultFile
        fi
        cd ../  # cd outof Gas_$training_cnt
    fi

    (( i++ ))
done

cd ../  # cd outof $TRAINFOLDER


###TO-PROCESS-MDFILE: resultFile
#
# Generate file MAE_PAIR_$training_cnt
#
gaml file_gen_mdpotential -s PAIR_Charge_$training_cnt.txt -i $MOLNM \
                          -f RESULT_EHD_$training_cnt.txt \
                          -kw $gromacs_energy_kw -lv $literature_value \
                          --MAE $MAE -o MAE_PAIR 


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
    echo 'Note: The GAML training has been done'
    cat MAE_PAIR_$training_cnt.txt | grep '^HEAD'
    date +'%T %B %d %Y'
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
pn_limit         = $pn_limit
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
    pktime $pid_gaml 8
    
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
    echo "Error Training number $training_cnt"
    echo "Exiting..."
    exit 1
fi
done # training_done
date +'%T %B %d %Y'


