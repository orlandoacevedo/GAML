from GAML.functions import file_size_check, file_gen_new, function_file_input, function_roundoff_error, \
                      function_pro_pn_limit
from GAML.charge_gen_scheme import Charge_gen_scheme
from GAML.function_prolist import Pro_list
import random


class GAML_main(object):

    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,}
        
        charge_path = kwargs['charge_path'] if 'charge_path' in kwargs else None
        file_path = kwargs['file_path'] if 'file_path' in kwargs else None
        symmetry_list = kwargs['symmetry_list'] if 'symmetry_list' in kwargs else None
        counter_list = kwargs['counter_list'] if 'counter_list' in kwargs else None
        offset_list = kwargs['offset_list'] if 'offset_list' in kwargs else None
        
        if 'error_tolerance' in kwargs and kwargs['error_tolerance'] is not None:              
            try:
                self.error_tolerance = float(kwargs['error_tolerance'])
                if self.error_tolerance < 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter error_tolerance has to be a positive number'
                return
        else:
            self.error_tolerance = 0.12

        if self.error_tolerance > 1:
            print('Warning: the error_tolerance is greater than 1..')
            

        if 'bool_abscomp' in kwargs and kwargs['bool_abscomp'] is not None:
            self.bool_abscomp = False if (kwargs['bool_abscomp'] is False) else True
        else:
            self.bool_abscomp = True


        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            self.cut_keyword = kwargs['cut_keyword']
        else:
            self.cut_keyword = 'MAE'
            

        if 'charge_extend_by' in kwargs and kwargs['charge_extend_by'] is not None:
            try:
                self.charge_extend_by = float(kwargs['charge_extend_by'])
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter charge_extend_by has to be a number'
                return
        else:
            self.charge_extend_by = 0.3

       
        if 'gennm' in kwargs and kwargs['gennm'] is not None:
            try:
                self.gennm = int(kwargs['gennm'])
                if self.gennm <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter gennm has to be a positive integer'
                return
        else:
            self.gennm = 20


        if 'ratio' in kwargs and kwargs['ratio'] is not None:
            self.ratio = kwargs['ratio']
            try:
                if kwargs['ratio'].count(':') == 2:
                    stmp = kwargs['ratio'][:kwargs['ratio'].find(':')]
                    ml = 0 if len(stmp.split()) == 0 else int(stmp)
                    
                    stmp = kwargs['ratio'][kwargs['ratio'].find(':')+1:kwargs['ratio'].rfind(':')]
                    av = 0 if len(stmp.split()) == 0 else int(stmp)
                    
                    stmp = kwargs['ratio'][kwargs['ratio'].rfind(':')+1:]
                    mu = 0 if len(stmp.split()) == 0 else int(stmp)

                elif kwargs['ratio'].count(':') == 1:
                    stmp = kwargs['ratio'][:kwargs['ratio'].find(':')]
                    ml = 0 if len(stmp.split()) == 0 else int(stmp)

                    stmp = kwargs['ratio'][kwargs['ratio'].find(':')+1:]
                    av = 0 if len(stmp.split()) == 0 else int(stmp)

                    mu = min(av,ml)
                else:
                    raise ValueError
                    
                if mu < 0 or av < 0 or ml < 0 or mu+av+ml == 0:
                    raise ValueError
                ratio_mu = mu / (mu + av + ml)
                ratio_av = av / (mu + av + ml)
                ratio_ml = ml / (mu + av + ml)
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter ratio is not correctly defined\n' + \
                                   'Error:' + kwargs['ratio']
                return 
        else:
            self.ratio = None
            ratio_ml = 0.7
            ratio_av = 0.2
            ratio_mu = 0.1


        if 'offset_nm' in kwargs and kwargs['offset_nm'] is not None:
            try:
                self.offset_nm = int(kwargs['offset_nm'])
                if self.offset_nm <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter offset_nm has to be a positive integer'
                return
        else:
            self.offset_nm = 5


        if 'nmround' in kwargs and kwargs['nmround'] is not None:
            try:
                self.nmround = int(kwargs['nmround'])
                if self.nmround <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter nmround has to be a positive integer'
                return
        else:
            self.nmround = 2
            

        if 'pn_limit' in kwargs and kwargs['pn_limit'] is not None:
            if isinstance(kwargs['pn_limit'],list):
                self.pn_limit = kwargs['pn_limit']
            elif isinstance(kwargs['pn_limit'],str):
                if len(kwargs['pn_limit']) == 0 or len(kwargs['pn_limit'].split()) == 0:
                    self.pn_limit = []
                else:
                    self.file_line_limit = kwargs['pn_limit']
                    log, self.pn_limit = function_pro_pn_limit(kwargs['pn_limit'],False)
                    if not log['nice']:
                        self.log['nice'] = False
                        self.log['info'] = log['info']
                        return
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter pn_limit is not correctly defined\n' + \
                                   '     : ' + str(kwargs['pn_limit'])
                return
        else:
            self.pn_limit = []


        if 'total_charge' in kwargs and kwargs['total_charge'] is not None:
            try:
                self.total_charge = float(kwargs['total_charge'])
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter total_charge has to be a number'
                return
        else:
            self.total_charge = 1.0
            

        if 'bool_neutral' in kwargs and kwargs['bool_neutral'] is not None:
            self.bool_neutral = False if (kwargs['bool_neutral'] is False) else True
        else:
            self.bool_neutral = True


        if self.total_charge == 0:
            self.bool_neutral = False

        if self.bool_neutral and self.nmround < 2:
            self.log['nice'] = False
            self.log['info'] = 'Error: When bool_neutral is set to True, the nmround should be not less than 2'
            return


        if 'bool_nozero' in kwargs and kwargs['bool_nozero'] is not None:
            self.bool_nozero = False if (kwargs['bool_nozero'] is False) else True
        else:
            self.bool_nozero = True


        if 'threshold' in kwargs and kwargs['threshold'] is not None:
            try:
                self.threshold = float(kwargs['threshold'])
                if self.threshold < 0.3:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter threshold has to be greater than 0.3'
                return
        else:
            self.threshold = 1.0


        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname']
        else:
            self.fname = 'ML_ChargeRandomGen'


        if (file_path is None) and (charge_path is None):
            self.log['nice'] = False
            self.log['info'] = 'Error: at least one of file_path and charge_path has to be provided'
            return

        # control all the pair-inputs
        self.totlist = []
        
        if charge_path is None:
            self.charge_path = None
            self.file_path = file_path
            dump_value = self._f_pro_filepath()
            if not self.log['nice']: return
           
            _par = Pro_list(symmetry_list=symmetry_list,offset_list=offset_list,counter_list=counter_list)
            if not _par.log['nice']:
                self.log['nice'] = False
                self.log['info'] = _par.log['info']
                return
            
            self.symmetry_list = _par.symmetry_list
            self.file_line_symmetry = _par.file_line_symmetry
            self.file_line_offset = _par.file_line_offset
            self.reflist = _par.reflist
            t = ratio_ml + ratio_av + ratio_mu if ratio_ml + ratio_av == 0 else ratio_ml + ratio_av
            nmtmp = int(self.gennm * ratio_ml / t + 0.5)
            if len(self.reflist) != 0:
                self.file_line_counter = _par.file_line_counter
                if len(self.mlinlist[0]) == 2:
                    if self.total_charge != 0:
                        self.log['nice'] = False
                        self.log['info'] = 'Error: if only two parameters are in perturbation and they are set to counter\n' + \
                                           'Error: then the total_charge has to be equal to zero'
                        return
                    #turn off the machine learning
                    nmtmp = 0

            dump_value = self._f_pro_symmetry_list()
            if not self.log['nice']: return
            self.galist_ml = self._f_charge_gen_ml(nmtmp)
            
            natmp = 0 if self.gennm - nmtmp <= 0 else self.gennm - nmtmp
            self.galist_average = self._f_charge_gen_average(natmp)
            
        else:    
            self.charge_path = charge_path
            self.charge_nor_list,self.charge_new_list = self._f_pro_charge_path(charge_path,self.charge_extend_by)
            if not self.log['nice']: return
            
            if file_path is None:
                self.file_path = None
            else:
                self.file_path = file_path
                dump_value = self._f_pro_filepath()
                if not self.log['nice']: return
                if len(self.charge_nor_list) < len(self.mlinlist[0]):
                    self.log['nice'] = False
                    self.log['info'] = 'Error: the charge file and the input file are not corresponded'
                    return

            gennm_nor = self.gennm // 2 if (file_path is None) else int(self.gennm * ratio_mu + 0.5)
            gennm_nor = 0 if gennm_nor == 0 else gennm_nor
            _par = Charge_gen_scheme(charge_path=self.charge_nor_list,symmetry_list=symmetry_list,offset_list=offset_list,
                                     counter_list=counter_list,nmround=self.nmround,gennm=gennm_nor,
                                     threshold=self.threshold,total_charge=self.total_charge,
                                     bool_neutral=self.bool_neutral,offset_nm=self.offset_nm,
                                     bool_nozero=self.bool_nozero,pn_limit=self.pn_limit)
            if not _par.log['nice']:
                self.log['nice'] = False
                self.log['info'] = _par.log['info']
                return
            self.schemelist_nor = []
            for i in _par.chargepair:
                if not self._f_remove_repeats(self.totlist,i):
                    self.schemelist_nor.append(i)

            for i in self.schemelist_nor:
                self.totlist.append(i)
            
            gennm_new = self.gennm - len(self.schemelist_nor) if (file_path is None) else gennm_nor
            gennm_new = 0 if gennm_new == 0 else gennm_new
            _par = Charge_gen_scheme(charge_path=self.charge_new_list,symmetry_list=symmetry_list,offset_list=offset_list,
                                     counter_list=counter_list,nmround=self.nmround,gennm=gennm_new,
                                     threshold=self.threshold,total_charge=self.total_charge,
                                     bool_neutral=self.bool_neutral,offset_nm=self.offset_nm,
                                     bool_nozero=self.bool_nozero,pn_limit=self.pn_limit)
            if not _par.log['nice']:
                self.log['nice'] = False
                self.log['info'] = _par.log['info']
                return
            self.schemelist_new = []
            for i in _par.chargepair:
                if not self._f_remove_repeats(self.totlist,i):
                    self.schemelist_new.append(i)

            for i in self.schemelist_new:
                self.totlist.append(i)

            self.symmetry_list = _par.prolist.symmetry_list
            if len(self.symmetry_list) != 0:
                self.file_line_symmetry = _par.prolist.file_line_symmetry
                self.file_line_offset = _par.prolist.file_line_offset
                
            self.reflist = _par.prolist.reflist
            if len(self.reflist) != 0:
                self.file_line_counter = _par.prolist.file_line_counter
                
            if file_path is not None:
                
                dump_value = self._f_pro_symmetry_list()
                if not self.log['nice']: return

                if len(self.reflist) != 0 and len(self.mlinlist[0]) == 2 and self.total_charge != 0:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: if only two parameters are in perturbation and they are set to counter\n' + \
                                       'Error: then the total_charge has to be equal to zero'
                    return
                
                nmtmp = int(self.gennm * ratio_ml + 0.5)
                self.galist_ml = self._f_charge_gen_ml(nmtmp)
                
                natmp = self.gennm - gennm_nor - gennm_new - nmtmp
                natmp = 0 if natmp <= 0 else natmp
                self.galist_average = self._f_charge_gen_average(natmp)
                


    def _f_remove_repeats(self,reflist,complist):
        """For a 2D nested reflist, if 1D complist is in it, return True, else return False."""

        for i in reflist:
            k = 0
            bool_ndx = True
            for j in complist:
                if j != i[k]:
                    bool_ndx = False
                    break
                k += 1
                
            if bool_ndx:
                return True
            
        return False


        
    def _f_pro_charge_path(self,charge_path,charge_extend_by):
        """Randomly generate a new charge range based on the charge_extend_by parameters, the return values
           are normal charge_range and this new charge_range"""
        
        def bound_mutation(prolist,extend_by,des='string'):
            if len(prolist) == 0:
                self.log['nice'] = False
                self.log['info'] = 'Error: it seems the charge_path is a {:s}, however, nothing was input\n'.format(des) + \
                                   '     : Or it is not correctly defined'
                return 0
                
            newlist = []
            for i in prolist:
                
                vs =  i[0] + ( random.randrange(3) - 1 ) * extend_by
                vt =  i[1] + ( random.randrange(3) - 1 ) * extend_by

                ls = []
                if vt > vs:
                    ls.append(vs)
                    ls.append(vt)
                elif vt == vs:
                    ls.append(vs)
                    ls.append(vs + 0.1)
                else:
                    ls.append(vt)
                    ls.append(vs)
                    
                newlist.append(ls)

            return newlist
        
        
        if isinstance(charge_path,list):
            for i in charge_list:
                if isinstance(i,list) and len(i) == 2 and (isinstance(i[0],int) or isinstance(i[0],float)) \
                   and (isinstance(i[1],int) or isinstance(i[1],float)):
                    pass
                else:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: the charge_path has to be a 2D nested number list\n' + \
                                       '       and its each sublist only contains two indices'
                    return 0,0

            # change the list name
            charge_nor_list = charge_path
            charge_new_list = bound_mutation(charge_path,charge_extend_by,des='list')
            
                
        elif isinstance(charge_path,str):
            
            log = file_size_check(charge_path,fsize=50)
            if not log['nice']:
                self.log['nice'] = False
                self.log['info'] = log['info']
                return 0,0
            
            charge_nor_list = []
            with open(charge_path,mode='rt') as f:
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    else:
                        ltmp = line[:line.find('#')].split()
                        if len(ltmp) != 0 and ltmp[0] == 'ATOM':
                            ls = []
                            ls.append(float(ltmp[2]))
                            ls.append(float(ltmp[3]))
                            charge_nor_list.append(ls)
            charge_new_list = bound_mutation(charge_nor_list,charge_extend_by,des='file\'s path')
            
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: the charge file has to be correctly defined'
            return 0,0
                       
        return charge_nor_list,charge_new_list



    def _f_pro_filepath(self):
        
        log = file_size_check(self.file_path,fsize=500)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return 0
        log, profile = function_file_input(self.file_path,dtype=float,bool_tail=True,cut_keyword=self.cut_keyword,
                                           bool_force_cut_kw=True)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return 0

        
        self.mlinlist = []
        for i in profile:
            self.totlist.append(i[:-1])

            if self.bool_abscomp and abs(i[-1]) <= self.error_tolerance:
                self.mlinlist.append(i[:-1])
            elif i[-1] <= self.error_tolerance:
                self.mlinlist.append(i[:-1])
                    
        print('For the error_tolerance: {}'.format(self.error_tolerance))
        print('The selected number of ML_charge_list is: {:d}'.format(len(self.mlinlist)))
        if self.bool_abscomp:
            print('Note: the absolute comparison is implemented')
        else:
            print('Note: the average comparison is implemented, which may cause positive and negative cancellation')
        print('\nDo you want to continue? y/yes for continue, else quit?',end='    ')

        getinput = input()
        if getinput.upper() != 'Y' and getinput.upper() != 'YES':
            self.log['nice'] = False
            self.log['info'] = ''
            print('Warning: you have decided to quit the ML charge generateion')
            return 0

        if len(self.mlinlist) < 5:
            self.log['nice'] = False
            self.log['info'] = 'Error: for machine learning, the number of entry to be trained has to be no less than 5'
            return 0

        return 1

            

    def _f_adjustment(self,inlist,lglist,refcntlist,total,nmround,threshold):
        """For a 1D number list, randomly choose a point which is not specified in refcntlist
           to fit its balanced-length summation to be equal to total, during the process, this
           value is rounded by nmround and set to be smaller than threshold, this adjustment
           is always less than 0.1"""

        def get_sum(inlist,lglist,cntlist):
            i = 0
            tsum = 0
            while i < len(inlist):
                if i not in cntlist:
                    tsum += inlist[i] * lglist[i]
                i += 1
            return tsum

        cntlist = []
        for i in refcntlist:
            cntlist.append(i[0])
            cntlist.append(i[2])
            
        # check input list
        tsum = get_sum(inlist,lglist,cntlist)
        if round(tsum-total,nmround+2) == 0:
            return True,inlist
        elif len(inlist) == 2 and len(refcntlist) != 0:
            return False,inlist
            
        while True:
            fitp = random.randrange(len(inlist))
            if (fitp not in cntlist):
                break

        # adjust fitp position value
        delta_p = (total - tsum) / lglist[fitp]
        if abs(delta_p) < 1 / 10**nmround:
            delta_p = -1 / 10**nmround if delta_p < 0 else 1 / 10**nmround
        elif abs(delta_p) > 0.1:
            delta_p = -0.1 if delta_p < 0 else 0.1

        value_p = inlist[fitp] + delta_p


        if abs(value_p) < threshold:
            inlist[fitp] = round(value_p,nmround)
            tsum = get_sum(inlist,lglist,cntlist)
            if round(tsum-total,nmround+2) == 0:
                return True,inlist
            
        return False,inlist


    def _f_charge_gen_average(self,pro_gennm):
        """Randomly choose no bigger than 5 pair from self.mlinlist, average them as a new inputs"""

        galist = []
        lth = len(self.mlinlist[0])
        while len(galist) < pro_gennm:
            nm = random.randrange(1,6)
            reflist = []
            while True:
                i = random.randrange(len(self.mlinlist))
                if i not in reflist:
                    reflist.append(i)
                if len(reflist) >= nm:
                    break

            i = 0
            averlist = []
            while i < lth:
                v = 0
                for j in reflist:
                    v += self.mlinlist[j][i]
                averlist.append(round((v/nm),self.nmround))
                i += 1
            
            for tmp in range(5):
                bo,averlist = self._f_adjustment(averlist,self.lglist,self.reflist,self.total_charge,
                                                 self.nmround,self.threshold)
                if bo:

                    # take care of the counter_list
                    for i in self.reflist:
                        s = averlist[i[0]]
                        snm = i[1]
                        t = averlist[i[2]]
                        tnm = i[3]
                        while True:
                            bo,s,snm,t,tnm = function_roundoff_error(s,snm,t,tnm,self.nmround)
                            if bo:
                                averlist[i[0]] = s
                                averlist[i[2]] = t
                                break
                    
                    # apply the pn_limit, take care the python index starts at zero
                    bool_tmp_limit = False
                    for i in self.pn_limit:
                        v = averlist[i[0]-1]
                        if i[1] == 'p' and v < 0:
                            bool_tmp_limit = True
                            break
                        elif i[1] == 'n' and v > 0:
                            bool_tmp_limit = True
                            break
                        
                    if not bool_tmp_limit:
                        if (not self.bool_nozero) or (not 0 in averlist):
                            if (not self._f_remove_repeats(galist,averlist)) and \
                               (not self._f_remove_repeats(self.totlist,averlist)):
                                galist.append(averlist)
                    break
               
        return galist



    def _f_pro_symmetry_list(self):
        """This method is to used to get corresponded length list"""

        self.lglist = []
        if len(self.symmetry_list) != 0:
            if len(self.symmetry_list) != len(self.mlinlist[0]):
                self.log['nice'] = False
                self.log['info'] = 'Error: the symmetry_list and the input trainning file are not corresponded'
                return 0 
                
            for i in self.symmetry_list:
                if isinstance(i,int):
                    self.lglist.append(1)
                else:
                    self.lglist.append(len(i))
        else:
            self.lglist = [ 1 for i in range(len(self.mlinlist[0]))]

        return 1

   

    def _f_charge_gen_ml(self,pro_gennm):
        """This method is used to generte charge_pairs based on the chosen charge_list, symmetry_list and counter_list"""
              
        crosslist = []
        lth = len(self.mlinlist)
        lgth = len(self.mlinlist[0])
        while len(crosslist) < pro_gennm:
            while True:
                rs = random.randrange(lth)
                rt = random.randrange(lth)
                if rs != rt:
                    break

            lrs = self.mlinlist[rs]
            lrt = self.mlinlist[rt]

            cutposition = random.randrange(1,lgth)

            lrs_1 = lrs[:cutposition]
            lrs_2 = lrs[cutposition:]

            lrt_1 = lrt[:cutposition]
            lrt_2 = lrt[cutposition:]

            lrs = lrs_1 + lrt_2
            lrt = lrt_1 + lrs_2

            # process the counterpart charge
            for cnt in self.reflist:
                while True:
                    bo,v,vnm,s,snm = function_roundoff_error(lrs[cnt[0]],cnt[1],lrs[cnt[2]],
                                                             cnt[3],nmround=self.nmround)
                    lrs[cnt[0]] = v
                    lrs[cnt[2]] = s
                    if bo:
                        break

            for cnt in self.reflist:
                while True:
                    bo,v,vnm,s,snm = function_roundoff_error(lrt[cnt[0]],cnt[1],lrt[cnt[2]],
                                                             cnt[3],nmround=self.nmround)
                    lrt[cnt[0]] = v
                    lrt[cnt[2]] = s
                    if bo:
                        break


            for tmp in range(5):
                bo,lrs = self._f_adjustment(lrs,self.lglist,self.reflist,self.total_charge,
                                            self.nmround,self.threshold)

                if bo:
                    # apply the pn_limit, take care the python index starts at zero
                    bool_tmp_limit = False
                    for i in self.pn_limit:
                        v = lrs[i[0]-1]
                        if i[1] == 'p' and v < 0:
                            bool_tmp_limit = True
                            break
                        elif i[1] == 'n' and v > 0:
                            bool_tmp_limit = True
                            break

                    if not bool_tmp_limit:
                    
                        # check self.bool_nozero and repeats
                        if (not self.bool_nozero) or (not 0 in lrs):
                            if (not self._f_remove_repeats(crosslist,lrs)) and \
                               (not self._f_remove_repeats(self.totlist,lrs)):
                                crosslist.append(lrs)
                    break

            for tmp in range(5):
                bo,lrt = self._f_adjustment(lrt,self.lglist,self.reflist,self.total_charge,
                                            self.nmround,self.threshold)
                
                if bo:
                    # apply the pn_limit, take care the python index starts at zero
                    bool_tmp_limit = False
                    for i in self.pn_limit:
                        v = lrt[i[0]-1]
                        if i[1] == 'p' and v < 0:
                            bool_tmp_limit = True
                            break
                        elif i[1] == 'n' and v > 0:
                            bool_tmp_limit = True
                            break
                        
                    if not bool_tmp_limit:
                    
                        # check self.bool_nozero and repeats
                        if (not self.bool_nozero) or (not 0 in lrt):
                            if (not self._f_remove_repeats(crosslist,lrt)) and \
                               (not self._f_remove_repeats(self.totlist,lrt)):
                                crosslist.append(lrt)
                    break
                
                    
        # since for each loop crosslist appends two lists, it is important to check its length
        # to make sure it is always no bigger than pro_gennm
        if len(crosslist) > pro_gennm:
            dump_value = crosslist.pop()

        # update the self.totlist
        for i in crosslist:
            self.totlist.append(i)
            
        return crosslist



    def file_print(self):

        self.fname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        print('The combined generated charge file name is:',end='    ')
        print(self.fname)

        with open(self.fname,mode='wt') as f:
            f.write('# This is the genetic algorithm machine learning generated charge file\n')
            f.write('# The total number of generated charge_pairs are: < {:} >\n\n'.format(self.gennm))
            
            if len(self.symmetry_list) != 0:
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:}\n\n'.format(self.file_line_symmetry))
                if len(self.file_line_offset) != 0:
                    f.write('# The offset_list used is:\n')
                    f.write('#    {:}\n'.format(self.file_line_offset))
                    f.write('# The offset_nm used is: < {:} >\n\n'.format(self.offset_nm))

            if len(self.reflist) != 0:
                f.write('# The counter_list used is:\n')
                f.write('#    {:}\n\n'.format(self.file_line_counter))

            if len(self.pn_limit) != 0:
                f.write('# The pn_limit used is:\n')
                f.write('#    {:}\n\n'.format(self.file_line_limit))

            if self.ratio is not None:
                f.write('# The ratio used is:\n')
                f.write('#    {:}\n'.format(self.ratio))

            f.write('# For each entry, the threshold used is: < {:} >\n'.format(self.threshold))
            f.write('# The bool_neutral is: < {:} >\n'.format('ON' if self.bool_neutral else 'OFF'))
            f.write('# The total_charge is: < {:} >\n\n'.format(self.total_charge))

            if self.file_path is not None:
                f.write('# The file_path used is:\n')
                f.write('#    {:}\n'.format(self.file_path))

            if self.charge_path is not None:
                if isinstance(self.charge_path,str):
                    f.write('# The charge_path used is:\n')
                    f.write('#    {:}\n\n'.format(self.charge_path))
                    
                f.write('# The normal charge_range used is:\n\n')
                j = 1
                for i in self.charge_nor_list:
                    f.write('#  ATOM  {:>4} {:>7}  {:>7}\n'.format(j,i[0],i[1]))
                    j += 1
                f.write('\n\n')
                    
                print('The number of charge_pairs generated by the normal charge range are: ',len(self.schemelist_nor))

                f.write('# The charge_pair generated by normal charge_range;\n\n')
                for i in self.schemelist_nor:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')

                f.write('\n\n# The value of charge_extention is: < {:} >\n'.format(self.charge_extend_by))
                f.write('# With the addition or subtraction, or keeping constant, in both low and high bound\n')
                f.write('# The new charge_range used is:\n\n')
                j = 1
                for i in self.charge_new_list:
                    f.write('#  ATOM  {:>4} {:>7}  {:>7}\n'.format(j,round(i[0],3),round(i[1],3)))
                    j += 1
                f.write('\n\n')

                print('The number of charge_pairs generated by the new charge range are: ',len(self.schemelist_new))

                f.write('# The charge_pair generated by modified charge_range;\n\n')
                for i in self.schemelist_new:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')
                    
                
            if self.file_path is not None:
                f.write('\n\n')

                if len(self.galist_ml) != 0:
                    print('The number of charge_pairs generated by the Genetic Algorithm are: ',len(self.galist_ml))

                    f.write('# The charge_pair generated by Genetic Algorithm\n\n')
                    for i in self.galist_ml:
                        f.write('PAIR  ')
                        for j in i:
                            f.write('{:>7}'.format(j))
                        f.write('\n')

                if len(self.galist_average) != 0:
                    print('The number of charge_pairs generated by the Average are: ',len(self.galist_average))

                    f.write('\n\n# The charge_pair generated by Average\n\n')
                    for i in self.galist_average:
                        f.write('PAIR  ')
                        for j in i:
                            f.write('{:>7}'.format(j))
                        f.write('\n')


    
