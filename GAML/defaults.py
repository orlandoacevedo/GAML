"""Collection of module defaults

If possible, parameters should be in lower case
"""


defaults_charge_gen_range = {
    'command'       :   'charge_gen_range',
    'charge_path'   :   None,
    'atomnm'        :   None,
    'percent'       :    0.8,
    'stepsize'      :    0.01,
    'nmround'       :    3,
    'fname'         :    'ChargeRange',
}


defaults_charge_gen_scheme = {
    'command'       :   'charge_gen_scheme',
    'charge_path'   :   None,
    'symmetry_list' :   None,
    'offset_list'   :   None,
    'offset_nm'     :   5,
    'counter_list'  :   None,
    'gennm'         :   5,
    'nmround'       :   2,
    'total_charge'  :   0.0,
    'in_keyword'    :   'ATOM',
    'bool_neutral'  :   True,
    'bool_nozero'   :   True,
    'neutral'       :   True,
    'nozero'        :   True,
    'pn_limit'      :   None,
    'threshold'     :   1.0,
    'fname'         :   'ChargePair',
}


defaults_GAML = {
    'command'           :   'gaml',
    'file_path'         :   None,
    'charge_path'       :   None,
    'symmetry_list'     :   None,
    'offset_list'       :   None,
    'offset_nm'         :   5,
    'counter_list'      :   None,
    'error_tolerance'   :   0.12,
    'bool_abscomp'      :   True,
    'abscomp'           :   True,
    'cut_keyword'       :   'MAE',
    'charge_extend_by'  :   0.3,
    'gennm'             :   20,
    'nmround'           :   2,
    'total_charge'      :   1.0,
    'bool_neutral'      :   True,
    'bool_nozero'       :   True,
    'neutral'           :   True,
    'nozero'            :   True,
    'pn_limit'          :   None,
    'threshold'         :   1.0,
    'ratio'             :   '0.7:0.2:0.1',  #ML:AV:MU
    'fname'             :   'ChargeGen',
}


defaults_file_gen_gaussian = {
    'command'       :   'file_gen_gaussian',
    'toppath'       :   None,
    'file_path'     :   None,
    'select_range'  :   10,
    'gennm'         :   5,
    'basis_set'     :   '# HF/6-31G(d) Pop=CHelpG',
    'charge_spin'   :   '0 1',
    'fname'         :   'GaussInput',
}


defaults_file_gen_gromacstop = {
    'command'        :   'file_gen_gromacstop',
    'toppath'        :   None,
    'charge_path'    :   None,
    'symmetry_list'  :   None,
    'reschoose'      :   'ALL',
    'in_keyword'     :   'PAIR',
    'cut_keyword'    :   'MAE',
    'gennm'          :   None,
    'fname'          :   'GromacsTopfile',
}


defaults_fss_analysis = {
    'command'           :   'fss_analysis',
    'file_path'         :   None,
    'atomtype_list'     :   None,
    'stepsize'          :   0.01,
    'error_tolerance'   :   0.28,
    'bool_abscomp'      :   True,
    'abscomp'           :   True,
    'percent'           :   0.95,
    'cut_keyword'       :   'MAE',
    'pallette_nm'       :   50,
    'color_map'         :   'rainbow',
    'fname'             :   'FSSPlot',
}


defaults_file_gen_mdpotential = {
    'command'           :   'file_gen_mdpotential',
    'file_path'         :   None,
    'chargefile'        :   None,
    'literature_value'  :   None,
    'atomnm'            :   500,
    'MAE'               :   0.05,
    'temperature'       :   298.15,
    'block'             :   'COUNT',
    'bool_gas'          :   False,
    'hvap'              :   False,
    'kwlist'            :   None,
    'fname'             :   'MDProcess',
}


defaults_GAML_autotrain = {
    'command'           :   'gaml_autotrain',
    'file_path'         :   None,
    'bashinterfile'     :   None,
}


defaults_file_gen_scripts = {
    'command'       :   'file_gen_scripts',
    'number'        :   None,
    'available'     :   None,
}


# note: register all defaults
parlist = [
    defaults_charge_gen_range,
    defaults_charge_gen_scheme,
    defaults_file_gen_gaussian,
    defaults_file_gen_gromacstop,
    defaults_file_gen_mdpotential,
    defaults_GAML,
    defaults_GAML_autotrain,
    defaults_fss_analysis,
    defaults_file_gen_scripts,
]


