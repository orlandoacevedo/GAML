from GAML.functions import file_size_check, file_gen_new, func_file_input, func_roundoff_error, func_pro_pn_limit
from GAML.charge_gen_scheme import Charge_gen_scheme
import random


class GAML(Charge_gen_scheme):

    def __init__(self,*args,**kwargs):

        super().__init__(self,*args,**kwargs)
        if not self.log['nice']: return

        bo = False
        if 'error_tolerance' in kwargs and kwargs['error_tolerance'] is not None:
            self.error_tolerance = kwargs['error_tolerance']
            if isinstance(self.error_tolerance,str):
                ltmp = self.error_tolerance.split()
                if len(ltmp) == 0:
                    self.error_tolerance = 0.12
                elif len(ltmp) == 1:
                    if str(ltmp[0]).lower() == 'nan':
                        self.error_tolerance = 'nan'
                    else:
                        try:
                            self.error_tolerance = float(ltmp[0])
                            if self.error_tolerance < 0:
                                raise ValueError
                        except ValueError:
                            bo = True
                else:
                    bo = True
            elif isinstance(self.error_tolerance,(float,int)):
                if self.error_tolerance < 0: bo = True
            else:
                bo = True
        else:
            self.error_tolerance = 0.12
        if bo:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter error_tolerance has to be a positive number'
            return

        if self.error_tolerance != 'nan' and self.error_tolerance > 1:
            print('Warning: the error_tolerance is greater than 1..')


        if 'bool_abscomp' in kwargs and kwargs['bool_abscomp'] is not None:
            self.bool_abscomp = False if (kwargs['bool_abscomp'] is False) else True
        else:
            self.bool_abscomp = True


        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            self.cut_keyword = kwargs['cut_keyword']
            if isinstance(self.cut_keyword,str):
                if len(self.cut_keyword.split()) == 0: self.cut_keyword = 'MAE'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter cut_keyword is not correctly defined'
                return
        else:
            self.cut_keyword = 'MAE'


        bo = False
        # NOTE: this number no less than 0.1
        if 'charge_extend_by' in kwargs and kwargs['charge_extend_by'] is not None:
            self.charge_extend_by = kwargs['charge_extend_by']
            if isinstance(self.charge_extend_by,str):
                ltmp = self.charge_extend_by.split()
                if len(ltmp) == 0:
                    self.charge_extend_by = 0.3
                elif len(ltmp) == 1:
                    if str(ltmp[0]).lower() == 'nan':
                        self.charge_extend_by = 'nan'
                    else:
                        try:
                            self.charge_extend_by = float(ltmp[0])
                            if self.charge_extend_by < 0.1:
                                raise ValueError
                        except ValueError:
                            bo = True
                else:
                    bo = True
            elif isinstance(self.charge_extend_by,(float,int)):
                if self.charge_extend_by < 0.1: bo = True
            else:
                bo = True
        else:
            self.charge_extend_by = 0.3
        if bo:
            self.log['nice'] = False
            self.log['info'] = 'Error: the parameter charge_extend_by has to be a positive number'
            return


        if 'ratio' in kwargs and kwargs['ratio'] is not None:
            self.ratio = kwargs['ratio']
            bo = False
            if isinstance(self.ratio,str):
                if len(self.ratio.split()) == 0: self.ratio = '0.7:0.2:0.1'
            else:
                bo = True
            try:
                if bo: raise ValueError
                cnt = self.ratio.count(':')
                if cnt == 2:
                    stmp = self.ratio[:self.ratio.find(':')]
                    ratio_ml = 0 if len(stmp.split()) == 0 else float(stmp)

                    stmp = self.ratio[self.ratio.find(':')+1:self.ratio.rfind(':')]
                    ratio_av = 0 if len(stmp.split()) == 0 else float(stmp)

                    stmp = self.ratio[self.ratio.rfind(':')+1:]
                    ratio_mu = 0 if len(stmp.split()) == 0 else float(stmp)

                elif cnt == 1:
                    stmp = self.ratio[:self.ratio.find(':')]
                    ratio_ml = 0 if len(stmp.split()) == 0 else float(stmp)

                    stmp = self.ratio[self.ratio.find(':')+1:]
                    ratio_av = 0 if len(stmp.split()) == 0 else float(stmp)

                    ratio_mu = 0.0

                elif cnt == 0:
                    ratio_ml = float(self.ratio)
                    ratio_av = 0.0
                    ratio_mu = 0.0
                else:
                    raise ValueError
                tmp = ratio_mu + ratio_av + ratio_ml
                if tmp == 0: raise ValueError
                if ratio_mu < 0 or ratio_av < 0 or ratio_ml < 0: raise ValueError
                if ratio_mu > 1.0 or ratio_av > 1.0 or ratio_ml > 1.0: raise ValueError
                if tmp > 1.0:
                    # normalization
                    ratio_ml = ratio_ml / tmp
                    ratio_av = ratio_av / tmp
                    ratio_mu = 1.0 - ratio_ml - ratio_av

            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter ratio is not correctly defined\n' + \
                                   'Error: {:}'.format(kwargs['ratio'])
                return
        else:
            self.ratio = '0.7:0.2:0.1'
            ratio_ml = 0.7
            ratio_av = 0.2
            ratio_mu = 0.1

        # for repeats filtration
        self.totlist = []

        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file_path = kwargs['file_path']
            self.profilepath()
            if not self.log['nice']: return
        else:
            self.file_path = None

        # three main possibles
        # 1: only symmetry_list
        # 2: only charge_path
        # 3: only file_path
        if self.charge_path is None and self.file_path is None and len(self.symmetry_list) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: no generation type is defined'
            return

        # one potential bug for the future updates because of SHALLOW and DEEP copy
        # to make the following codes work properly
        # the parent method, super().run() has to initialize list-attribute self.chargepair
        # at every time when it is called
        if self.charge_path is None:
            if self.file_path is None:
                # only symmetry_list
                # for future debug
                self.mlinlist = []
                # use inherited method; no ratio related; no need filtration; DONE
                self.run()
                if not self.log['nice']: return
                self.ratio_new = '0.0:0.0:0.0'
            else:
                # only file_path OR both file_path and symmetry_list
                # relation between symmetry_list and file_path --> self.lglist
                self.func_syml()

                # recalculate ratio
                if ratio_ml == 0 and ratio_av == 0:
                    ratio_ml = 0.5
                    ratio_av = 0.5
                else:
                    if ratio_ml == 0:
                        ratio_ml = 1 - ratio_av
                    elif ratio_av == 0:
                        ratio_av = 1 - ratio_ml
                    else:
                        ratio_ml = ratio_ml / (ratio_ml+ratio_av)
                        ratio_av = 1.0 - ratio_ml
                self.ratio_new = '{:}:{:}:0.0'.format(ratio_ml,ratio_av)

                # backup self.gennm
                totnm = self.gennm
                # redefine self.gennm
                self.gennm = int(totnm*ratio_ml + 0.5)
                # generate ML: self.chargepair_ml
                self.func_ml()
                # use average method
                self.gennm = totnm - self.gennm
                if self.gennm > 0:
                    self.func_av()
                else:
                    self.chargepair_av = []

                # reset self.gennm
                self.gennm = totnm
        else:
            # backup self.gennm
            totnm = self.gennm

            if self.file_path is None:
                # only charge_path OR both charge_pair and symmetry_list
                # consider mutation
                # recalculate ratio
                if ratio_ml == 0 and ratio_mu == 0:
                    ratio_ml = 0.5
                    ratio_mu = 0.5
                else:
                    if ratio_ml == 0:
                        ratio_ml = 1 - ratio_mu
                    elif ratio_mu == 0:
                        ratio_mu = 1 - ratio_ml
                    else:
                        ratio_ml = ratio_ml / (ratio_ml+ratio_mu)
                        ratio_mu = 1.0 - ratio_ml
                self.ratio_new = '{:}:0.0:{:}'.format(ratio_ml,ratio_mu)

                nm_av = 0
                # for future debug
                self.mlinlist = []
                self.chargepair_av = []
            else:
                # relation between symmetry_list and file_path --> self.lglist
                self.func_syml()
                # recalculate ratio
                if ratio_ml == 0 and ratio_av == 0:
                    ratio_ml = ratio_av = (1.0-ratio_mu) / 2
                elif ratio_ml == 0 and ratio_mu == 0:
                    ratio_ml = ratio_mu = (1.0-ratio_av) / 2
                elif ratio_mu == 0 and ratio_av == 0:
                    ratio_mu = ratio_av = (1.0-ratio_ml) / 2
                else:
                    if ratio_ml == 0:
                        ratio_ml = 1.0 - (ratio_mu+ratio_av)
                    elif ratio_mu == 0:
                        ratio_mu = 1.0 - (ratio_ml+ratio_av)
                    elif ratio_av == 0:
                        ratio_av = 1.0 - (ratio_ml+ratio_mu)
                self.ratio_new = '{:}:{:}:{:}'.format(ratio_ml,ratio_av,ratio_mu)

                # redefine self.gennm for average
                self.gennm = int(totnm*ratio_av + 0.5)
                nm_av = self.gennm
                self.func_av()


            # generate ML: self.chargepair_ml
            self.gennm = int(totnm*ratio_ml + 0.5)
            nm_ml = self.gennm
            if nm_ml > 0:
                self.func_ml()
            else:
                # for future debug
                self.chargepair_ml = []

            # generate nor_charge_list: self.chargepair_nor
            # redefine self.gennm
            self.gennm = int( (totnm - nm_av - nm_ml) / 2 )
            nm_nor = self.gennm
            if self.gennm > 0:
                self.run(filterlist=self.totlist)
                if not self.log['nice']: return
                # rename ATTENTION
                self.chargepair_nor = self.chargepair

                # manually update self.totlist
                for i in self.chargepair_nor: self.totlist.append(i)

                # generate new_charge_list: self.charge_pair_new
                # redefine self.gennm
                self.gennm = int( totnm - nm_av - nm_ml - nm_nor )
                if self.gennm > 0:
                    # backup normal charge_list
                    # ATTENTION: DEEP copy
                    # based on we already know its data type, easiest way
                    self.charge_list_nor = []
                    for i in self.charge_list: self.charge_list_nor.append([j for j in i])

                    # mutation
                    # 0: no change; 1: add; 2: minus
                    for i in range(len(self.charge_list)):
                        # low bound
                        tmp = random.randrange(3)
                        if tmp == 1 or tmp == 2:
                            s = self.charge_list[i][0]
                            t = s + self.charge_extend_by if tmp == 1 else s - self.charge_extend_by
                            if ( self.charge_list[i][0] < 0 and t < 0 ) or \
                               ( self.charge_list[i][0] > 0 and t > 0 ):
                                self.charge_list[i][0] = t
                            else:
                                # get random extend number
                                m = random.randrange(3,int(self.charge_extend_by*100))
                                m = m / 100.0
                                n = s + m if tmp == 1 else s - m
                                if ( self.charge_list[i][0] < 0 and n < 0 ) or \
                                   ( self.charge_list[i][0] > 0 and n > 0 ):
                                    self.charge_list[i][0] = n

                        # high bound
                        tmp = random.randrange(3)
                        if tmp == 1 or tmp == 2:
                            s = self.charge_list[i][1]
                            t = s + self.charge_extend_by if tmp == 1 else s - self.charge_extend_by
                            if ( self.charge_list[i][1] < 0 and t < 0 ) or \
                               ( self.charge_list[i][1] > 0 and t > 0 ):
                                self.charge_list[i][1] = t
                            else:
                                # get random extend number
                                m = random.randrange(3,int(self.charge_extend_by*100))
                                m = m / 100.0
                                n = s + m if tmp == 1 else s - m
                                if ( self.charge_list[i][1] < 0 and n < 0 ) or \
                                   ( self.charge_list[i][1] > 0 and n > 0 ):
                                    self.charge_list[i][1] = n

                    # parent method
                    self.prochargelist()
                    # rename ATTENTION
                    self.charge_list_new = self.charge_list

                    # generation
                    self.run(filterlist=self.totlist)
                    if not self.log['nice']: return
                    self.chargepair_new = self.chargepair
                else:
                    self.chargepair_new = []
            # reset self.gennm
            self.gennm = totnm


    def profilepath(self):
        """process file_path based on self.error_tolerance
           Result:
                self.mlinlist; self.totlist"""

        log = file_size_check(self.file_path,fsize=500)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return 0
        log, profile = func_file_input(self.file_path,dtype=float,bool_tail=True,cut_keyword=self.cut_keyword,
                                       bool_force_cut_kw=True)
        if not log['nice']:
            self.log['nice'] = False
            self.log['info'] = log['info']
            return 0


        self.mlinlist = []
        for i in profile:
            self.totlist.append(i[:-1])

            if self.error_tolerance == 'nan':
                self.mlinlist.append(i[:-1])
            elif isinstance(i[-1],(float,int)):
                if self.bool_abscomp and abs(i[-1]) <= self.error_tolerance:
                    self.mlinlist.append(i[:-1])
                elif i[-1] <= self.error_tolerance:
                    self.mlinlist.append(i[:-1])

        print('For the error_tolerance: {:}'.format(self.error_tolerance))
        print('The selected number of ML_charge_list is: {:d}'.format(len(self.mlinlist)))
        if self.bool_abscomp:
            print('Note: the absolute comparison is implemented')
        else:
            print('Note: the average comparison is implemented, which may cause positive and negative cancellation')
        print('\nDo you want to continue? y/yes for continue, else quit?',end='    ')

        getinput = input()
        if getinput.lower() not in ['y', 'yes']:
            self.log['nice'] = False
            self.log['info'] = ''
            print('Warning: you have decided to quit the ML charge generation')
            return 0

        if len(self.mlinlist) < 5:
            self.log['nice'] = False
            self.log['info'] = 'Error: for machine learning, the number of entry to be trained has to be no less than 5'
            return 0

        return 1



    def func_adjust(self,inlist):
        """For a 1D number list, randomly choose a point which is not specified in refcntlist
           to fit its balanced-length summation to be equal to total, during the process, this
           value is rounded by nmround and set to be smaller than threshold, this adjustment
           is always less than 0.1

           Parameter:
                inlist, self.lglist, self.reflist, self.totol_charge, self.nmround, self.threshold
           Return:
                boolean, inlist"""

        def get_sum(inlist,lglist,cntlist):
            i = 0
            tsum = 0
            while i < len(inlist):
                if i not in cntlist:
                    tsum += inlist[i] * lglist[i]
                i += 1
            return tsum

        cntlist = []
        for i in self.reflist:
            cntlist.append(i[0])
            cntlist.append(i[2])

        # check input list
        tsum = get_sum(inlist,self.lglist,cntlist)
        if round(tsum-self.total_charge,self.nmround+2) == 0:
            return True,inlist
        elif len(inlist) == 2 and len(self.reflist) != 0:
            return False,inlist

        while True:
            fitp = random.randrange(len(inlist))
            if (fitp not in cntlist):
                break

        # adjust fitp position value
        delta_p = (self.total_charge - tsum) / self.lglist[fitp]
        if abs(delta_p) < 1 / 10**self.nmround:
            delta_p = -1 / 10**self.nmround if delta_p < 0 else 1 / 10**self.nmround
        elif abs(delta_p) > 0.1:
            delta_p = -0.1 if delta_p < 0 else 0.1

        value_p = inlist[fitp] + delta_p


        if abs(value_p) < self.threshold:
            inlist[fitp] = round(value_p,self.nmround)
            tsum = get_sum(inlist,self.lglist,cntlist)
            if round(tsum-self.total_charge,self.nmround+2) == 0:
                return True,inlist

        return False,inlist


    def func_av(self):
        """Randomly choose no bigger than 5 pair from self.mlinlist, average them as a new inputs

           Update:
                self.totlist
           Result:
                self.chargepair_av"""

        self.chargepair_av = []
        lth = len(self.mlinlist[0])
        while len(self.chargepair_av) < self.gennm:
            nm = random.randrange(2,6)
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

            bo,averlist = self.func_adjust(averlist)
            if bo:
                # take care of the counter_list
                for i in self.reflist:
                    s = averlist[i[0]]
                    snm = i[1]
                    t = averlist[i[2]]
                    tnm = i[3]
                    while True:
                        bo,s,snm,t,tnm = func_roundoff_error(s,snm,t,tnm,self.nmround)
                        if bo:
                            averlist[i[0]] = s
                            averlist[i[2]] = t
                            break

                # apply the pn_limit
                bool_limit = False
                for i in self.pn_limit:
                    v = averlist[i[0]]
                    if i[1] == 'p' and v < 0:
                        bool_limit = True
                        break
                    elif i[1] == 'n' and v > 0:
                        bool_limit = True
                        break

                if not bool_limit:
                    if (not self.bool_nozero) or (not 0 in averlist):
                        # inherited method
                        # self-check and overall check
                        if (not self.func_bool_repeats(self.chargepair_av,averlist)) and \
                            (not self.func_bool_repeats(self.totlist,averlist)):
                            self.chargepair_av.append(averlist)

        # finally update self.totlist
        for i in self.chargepair_av: self.totlist.append(i)



    def func_syml(self):
        """This method is to used to get corresponded length list between self.symmetry_list and self.mlinlist,
           at least one of them exists"""

        if len(self.symmetry_list) != 0:
            if len(self.mlinlist) != 0 and len(self.symmetry_list) != len(self.mlinlist[0]):
                self.log['nice'] = False
                self.log['info'] = 'Error: the symmetry_list and the input trainning file are not corresponded'
                return
            self.lglist = [1 if isinstance(i,int) else len(i) for i in self.symmetry_list]
        else:
            self.lglist = [1 for i in range(len(self.mlinlist[0]))]


    def func_ml(self):
        """This method is used to generte number of self.gennm charge_pairs based on the chosen charge_list,
           symmetry_list and counter_list

           Update:
                self.totlist
           Result:
                self.chargepair_ml"""

        self.chargepair_ml = []
        lth = len(self.mlinlist)
        lgth = len(self.mlinlist[0])
        while len(self.chargepair_ml) < self.gennm:
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
                    bo,v,vnm,s,snm = func_roundoff_error(lrs[cnt[0]],cnt[1],lrs[cnt[2]],
                                                         cnt[3],nmround=self.nmround)
                    lrs[cnt[0]] = v
                    lrs[cnt[2]] = s
                    if bo:
                        break

            for cnt in self.reflist:
                while True:
                    bo,v,vnm,s,snm = func_roundoff_error(lrt[cnt[0]],cnt[1],lrt[cnt[2]],
                                                         cnt[3],nmround=self.nmround)
                    lrt[cnt[0]] = v
                    lrt[cnt[2]] = s
                    if bo:
                        break

            bo,lrs = self.func_adjust(lrs)
            if bo:
                # apply the pn_limit
                bool_limit = False
                for i in self.pn_limit:
                    v = lrs[i[0]]
                    if i[1] == 'p' and v < 0:
                        bool_limit = True
                        break
                    elif i[1] == 'n' and v > 0:
                        bool_limit = True
                        break
                if not bool_limit:
                    # check self.bool_nozero and repeats
                    if (not self.bool_nozero) or (not 0 in lrs):
                        if (not self.func_bool_repeats(self.chargepair_ml,lrs)) and \
                            (not self.func_bool_repeats(self.totlist,lrs)):
                            self.chargepair_ml.append(lrs)

            bo,lrt = self.func_adjust(lrt)
            if bo:
                # apply the pn_limit
                bool_limit = False
                for i in self.pn_limit:
                    v = lrt[i[0]]
                    if i[1] == 'p' and v < 0:
                        bool_limit = True
                        break
                    elif i[1] == 'n' and v > 0:
                        bool_limit = True
                        break
                if not bool_limit:
                    # check self.bool_nozero and repeats
                    if (not self.bool_nozero) or (not 0 in lrt):
                        if (not self.func_bool_repeats(self.chargepair_ml,lrt)) and \
                            (not self.func_bool_repeats(self.totlist,lrt)):
                            self.chargepair_ml.append(lrt)


        # since for each loop self.chargepair_ml may append two lists, it is important to check
        # its length to make sure it is always no bigger than self.gennm
        if len(self.chargepair_ml) > self.gennm:
            dump_value = self.chargepair_ml.pop()

        # finally update self.totlist
        for i in self.chargepair_ml: self.totlist.append(i)


    def file_print(self):
        """overwrite parent method"""

        self.fname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        print('The combined generated charge file name is:',end='    ')
        print(self.fname)

        with open(self.fname,mode='wt') as f:
            f.write('# This is the genetic algorithm machine learning generated charge file\n')
            f.write('# The total number of generated charge_pairs are: < {:} >\n\n'.format(self.gennm))

            if len(self.prolist.symmetry_list) != 0:
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:}\n\n'.format(self.prolist.file_line_symmetry))
                if len(self.prolist.offset_list) != 0:
                    f.write('# The offset_list used is: < {:} >\n'.format(self.prolist.file_line_offset))
                    f.write('# The offset_nm used is: < {:} >\n\n'.format(self.offset_nm))

            if len(self.reflist) != 0:
                f.write('# The counter_list used is: < {:} >\n\n'.format(self.prolist.file_line_counter))

            if len(self.pn_limit) != 0:
                tmp = [str(i[0]+1) + i[1] for i in self.pn_limit]
                f.write('# The pn_limit used is:\n#    {:}\n\n'.format(tmp))

            f.write('# The input ratio is: (ML:Average:Mutation) < {:} >\n'.format(self.ratio))
            f.write('# The recalc ratio is: (ML:Average:Mutation) < {:} >\n'.format(self.ratio_new))
            f.write('# For each entry, the threshold used is: < {:} >\n'.format(self.threshold))
            f.write('# The total_charge is: < {:} >\n\n'.format(self.total_charge))
            f.write('# The bool_neutral is: < {:} >\n'.format('ON' if self.bool_neutral else 'OFF'))
            f.write('# The bool_nozero is: < {:s} >\n\n'.format('ON' if self.bool_nozero else 'OFF'))

            if self.file_path is not None:
                f.write('# The file_path used is: < {:} >\n'.format(self.file_path))

            if self.charge_path is not None:
                f.write('# The charge_path used is: < {:} >\n\n'.format(self.charge_path))

                nm_nor = len(self.chargepair_nor)
                if nm_nor > 0:
                    f.write('# The normal charge_range used is:\n')
                    j = 1
                    for i in self.charge_list_nor:
                        f.write('#  ATOM  {:>4} {:>7}  {:>7}\n'.format(j,i[0],i[1]))
                        j += 1
                    f.write('\n\n')

                    print('The number of charge_pairs generated by the normal charge range are: ',nm_nor)
                    f.write('# The charge_pair generated by normal charge_range: ({:})\n\n'.format(nm_nor))
                    for i in self.chargepair_nor:
                        f.write('PAIR  ')
                        for j in i:
                            f.write('{:>7}'.format(j))
                        f.write('\n')

                    nm_new = len(self.chargepair_new)
                    if nm_new > 0:
                        f.write('\n\n# The value of charge_extention is: < {:} >\n'.format(self.charge_extend_by))
                        f.write('# With the addition or subtraction, or keeping constant, in both low and high bound\n')
                        f.write('# The new charge_range used is:\n\n')
                        j = 1
                        for i in self.charge_list_new:
                            f.write('#  ATOM  {:>4} {:>7}  {:>7}\n'.format(j,round(i[0],3),round(i[1],3)))
                            j += 1
                        f.write('\n\n')

                        print('The number of charge_pairs generated by the new charge range are: ',nm_new)
                        f.write('# The charge_pair generated by modified charge_range: ({:})\n\n'.format(nm_new))
                        for i in self.chargepair_new:
                            f.write('PAIR  ')
                            for j in i:
                                f.write('{:>7}'.format(j))
                            f.write('\n')

            if self.file_path is not None:
                f.write('\n\n')
                nm_ml = len(self.chargepair_ml)
                if nm_ml != 0:
                    print('The number of charge_pairs generated by the Genetic Algorithm are: ',nm_ml)
                    f.write('# The charge_pair generated by Genetic Algorithm: ({:})\n\n'.format(nm_ml))
                    for i in self.chargepair_ml:
                        f.write('PAIR  ')
                        for j in i:
                            f.write('{:>7}'.format(j))
                        f.write('\n')
                nm_av = len(self.chargepair_av)
                if nm_av != 0:
                    print('The number of charge_pairs generated by the Average are: ',nm_av)
                    f.write('\n\n# The charge_pair generated by Average: ({:})\n\n'.format(nm_av))
                    for i in self.chargepair_av:
                        f.write('PAIR  ')
                        for j in i:
                            f.write('{:>7}'.format(j))
                        f.write('\n')


