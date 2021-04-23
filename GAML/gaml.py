from GAML.functions import file_size_check, file_gen_new, func_file_input, \
                           func_roundoff_error, func_pro_pn_limit
from GAML.charge_gen_scheme import Charge_gen_scheme
import random


class GAML(Charge_gen_scheme):
    def __init__(self,*args,**kwargs):
        super().__init__(self,*args,**kwargs)

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
            print('error_tolerance has to be a positive number')
            raise ValueError('wrong defined')

        if self.error_tolerance != 'nan' and self.error_tolerance > 1:
            print('Warning: the error_tolerance is greater than 1..')

        if 'bool_abscomp' in kwargs and kwargs['bool_abscomp'] is not None:
            self.bool_abscomp = False if (kwargs['bool_abscomp'] is False) else True
        else:
            self.bool_abscomp = True

        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            self.cut_keyword = kwargs['cut_keyword']
            if isinstance(self.cut_keyword,str):
                if len(self.cut_keyword.split()) == 0:
                    self.cut_keyword = 'MAE'
                else:
                    self.cut_keyword = self.cut_keyword.strip()
            else:
                print('cut_keyword is not correctly defined')
                raise ValueError('wrong defined')
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
            print('charge_extend_by has to be a positive number')
            raise ValueError('wrong defined')

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
                    p = self.ratio[:self.ratio.find(':')]
                    ml = 0 if len(p.split()) == 0 else float(p)

                    p = self.ratio[self.ratio.find(':')+1:self.ratio.rfind(':')]
                    av = 0 if len(p.split()) == 0 else float(p)

                    p = self.ratio[self.ratio.rfind(':')+1:]
                    mu = 0 if len(p.split()) == 0 else float(p)

                elif cnt == 1:
                    p = self.ratio[:self.ratio.find(':')]
                    ml = 0 if len(p.split()) == 0 else float(p)

                    p = self.ratio[self.ratio.find(':')+1:]
                    av = 0 if len(p.split()) == 0 else float(p)

                    mu = 0.0

                elif cnt == 0:
                    ml = float(self.ratio)
                    av = 0.0
                    mu = 0.0
                else:
                    raise ValueError
                tmp = mu + av + ml
                if tmp == 0: raise ValueError
                if mu < 0 or av < 0 or ml < 0: raise ValueError
                if mu > 1.0 or av > 1.0 or ml > 1.0: raise ValueError
                if tmp > 1.0:
                    # normalization
                    ml = ml / tmp
                    av = av / tmp
                    mu = 1.0 - ml - av

            except ValueError:
                print('ratio is not correctly defined')
                raise ValueError('wrong defined')
        else:
            self.ratio = '0.7:0.2:0.1'
            ml = 0.7
            av = 0.2
            mu = 0.1
        self.ratio_ = [ml, av, mu]

        # for repeats filtration
        self.totlist = []

        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.file_path = kwargs['file_path']
            self.profilepath()
        else:
            self.file_path = None

        # three main possibles
        # 1: has symmetry_list
        # 2: has charge_path
        # 3: has file_path
        if self.charge_path is None and len(self.symmetry_list) == 0:
            if self.file_path is None:
                print('Error: no generation type is defined')
                raise ValueError('no inputs')
            self.symmetry_list = [i for i in range(len(self.mlinlist[0]))]
        # parent method
        self.get_file_lines()

        if self.charge_path is None and self.file_path is None:
            rmax = 0
            for i in self.symmetry_list:
                if isinstance(i,int):
                    rmax += 1
                else:
                    rmax += len(i)
            self.charge_list = [[-self.charge_extend_by,self.charge_extend_by] for i in range(rmax)]



    def run(self):
        """rewrite parent run method

        However, we can still call its parent by using super()
        """
        # potential bug: SHALLOW and DEEP copy
        # to make the following codes work properly
        # its parent method, super().run() will initialize self.chargepair
        # at every time when it is called
        ml = self.ratio_[0]
        av = self.ratio_[1]
        mu = self.ratio_[2]
        del self.ratio_

        self.chargepair_av = []
        self.chargepair_ml = []
        self.chargepair_new = []
        self.chargepair_nor = []
        if self.charge_path is None:
            if self.file_path is None:
                # only symmetry_list
                # for future debug
                self.mlinlist = []
                # inherited method: no ratio related; no need filtration; DONE
                super().run()
                self.ratio_new = '0.0:0.0:0.0'
                self.chargepair_nor = self.chargepair
                self.charge_list_nor = self.charge_list
            else:
                # only file_path OR both file_path and symmetry_list
                # relation between symmetry_list and file_path --> self.lglist
                self.func_syml()

                # recalculate ratio
                if ml == 0 and av == 0:
                    ml = 0.5
                    av = 0.5
                else:
                    if ml == 0:
                        ml = 1 - av
                    elif av == 0:
                        av = 1 - ml
                    else:
                        ml = ml / (ml+av)
                        av = 1.0 - ml
                self.ratio_new = '{:}:{:}:0.0'.format(ml,av)

                # backup self.gennm
                totnm = self.gennm
                if len(self.symmetry_list) != len(self.reflist)*2:
                    # redefine self.gennm
                    self.gennm = int(totnm*ml + 0.5)
                    # generate ML: self.chargepair_ml
                    self.func_ml()
                    # use average method
                    self.gennm = totnm - self.gennm
                if self.gennm > 0: self.func_av()

                # reset self.gennm
                self.gennm = totnm
        else:
            # backup self.gennm
            totnm = self.gennm

            if self.file_path is None:
                # only charge_path OR both charge_pair and symmetry_list
                # consider mutation
                # recalculate ratio
                self.ratio_new = '0.0:0.0:1.0'

                nm_av = 0
                nm_ml = 0
                # for future debug
                self.mlinlist = []
            else:
                # relation between symmetry_list and file_path --> self.lglist
                self.func_syml()
                # recalculate ratio
                if ml == 0 and av == 0:
                    ml = av = (1.0-mu) / 2
                elif ml == 0 and mu == 0:
                    ml = mu = (1.0-av) / 2
                elif mu == 0 and av == 0:
                    mu = av = (1.0-ml) / 2
                else:
                    if ml == 0:
                        ml = 1.0 - (mu+av)
                    elif mu == 0:
                        mu = 1.0 - (ml+av)
                    elif av == 0:
                        av = 1.0 - (ml+mu)

                if len(self.symmetry_list) != len(self.reflist)*2:
                    # generate ML: self.chargepair_ml
                    self.gennm = int(totnm*ml + 0.5)
                    nm_ml = self.gennm
                    if nm_ml > 0: self.func_ml()
                else:
                    ml = 0.0
                    nm_ml = 0

                # redefine self.gennm for average
                self.gennm = int(totnm*av + 0.5)
                nm_av = self.gennm
                if self.gennm > 0: self.func_av()

                mu = 1 - ml - av
                self.ratio_new = '{:}:{:}:{:}'.format(ml,av,mu)


            # generate nor_charge_list: self.chargepair_nor
            # redefine self.gennm
            self.gennm = int( (totnm - nm_av - nm_ml) / 2 )
            nm_nor = self.gennm
            if self.gennm > 0:
                super().run(filterlist=self.totlist)
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
                    super().run(filterlist=self.totlist)
                    self.chargepair_new = self.chargepair

            # reset self.gennm
            self.gennm = totnm



    def profilepath(self):
        """process file_path based on self.error_tolerance

        Attributes:
            self.mlinlist
            self.totlist
        """
        file_size_check(self.file_path,fsize=500)
        profile = func_file_input(self.file_path,
                                  dtype=float,
                                  bool_tail=True,
                                  cut_keyword=self.cut_keyword,
                                  bool_force_cut_kw=True)

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

        if len(self.mlinlist) < 5:
            print('the number of entry to be trained has to be no less than 5')
            raise ValueError('too less parameters')

        print('For error_tolerance: {:}'.format(self.error_tolerance))
        print('Number of ML_charge_list is: {:}'.format(len(self.mlinlist)))
        if self.bool_abscomp:
            print('Note: the absolute comparison is implemented')
        else:
            print('Note: the average comparison is implemented')
            print('      which may cause positive and negative cancellation')
        print('\nDo you want to continue? y/yes, else quit?',end='    ')

        get = input()
        if get.lower() not in ['y', 'yes']:
            print('Warning: you have decided to quit the ML charge generation')
            raise RuntimeError('user decided quit')



    def func_adjust(self,inlist):
        """
        For a 1D number list, randomly choose a point which is not specified
        in refcntlist to fit its balanced-length summation to be equal to total,
        during the process, this value is rounded by nmround and set to be
        smaller than threshold, this adjustment is always less than 0.1

        Parameter:
            inlist
            self.lglist
            self.reflist
            self.totol_charge
            self.nmround
            self.threshold

        Returns:
            bool    :   True when done
            inlist  :   List
        """

        def get_sum(inlist,lglist,cntlist):
            i = 0
            tsum = 0.0
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
        dp = (self.total_charge - tsum) / self.lglist[fitp]
        if abs(dp) < 1 / 10**self.nmround:
            dp = -1.0 / 10**self.nmround if dp < 0 else 1.0 / 10**self.nmround
        elif abs(dp) > 0.1:
            dp = -0.1 if dp < 0 else 0.1

        vp = inlist[fitp] + dp
        if abs(vp) < self.threshold:
            inlist[fitp] = round(vp,self.nmround)
            tsum = get_sum(inlist,self.lglist,cntlist)
            if round(tsum-self.total_charge,self.nmround+2) == 0:
                return True,inlist

        return False,inlist


    def func_av(self):
        """Average method

        Randomly choose no bigger than 5 pair from self.mlinlist,
        average them as a new inputs

        Update:
            self.totlist

        Attributes:
            self.chargepair_av
        """
        cnt = 0
        self.chargepair_av = []
        lth = len(self.mlinlist[0])
        while len(self.chargepair_av) < self.gennm:
            nm = random.randrange(2,6)
            reflist = random.sample(range(len(self.mlinlist)),k=nm)

            averlist = []
            for i in range(lth):
                v = 0.0
                for j in reflist: v += self.mlinlist[j][i]
                averlist.append(round((v/nm),self.nmround))

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
                        if not self.func_bool_repeats(self.chargepair_av,averlist):
                            if not self.func_bool_repeats(self.totlist,averlist):
                                self.chargepair_av.append(averlist)

        # finally update self.totlist
        for i in self.chargepair_av: self.totlist.append(i)



    def func_syml(self):
        """
        get corresponded length list between self.symmetry_list and
        self.mlinlist, at least one of them exists
        """
        if len(self.symmetry_list) != 0:
            if len(self.mlinlist) != 0 and len(self.symmetry_list) != len(self.mlinlist[0]):
                print('symmetry_list and input training file')
                raise ValueError('not correspond')
            self.lglist = [1 if isinstance(i,int) else len(i) for i in self.symmetry_list]
        else:
            self.lglist = [1 for i in range(len(self.mlinlist[0]))]



    def func_ml(self):
        """generte number based on input lists

        Attributes:
            self.totlist
            self.chargepair_ml
        """
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
                    bo,v,vnm,s,snm = func_roundoff_error(lrs[cnt[0]],cnt[1],
                                                         lrs[cnt[2]],cnt[3],
                                                         nmround=self.nmround)
                    lrs[cnt[0]] = v
                    lrs[cnt[2]] = s
                    if bo:
                        break

            for cnt in self.reflist:
                while True:
                    bo,v,vnm,s,snm = func_roundoff_error(lrt[cnt[0]],cnt[1],
                                                         lrt[cnt[2]],cnt[3],
                                                         nmround=self.nmround)
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
                        if not self.func_bool_repeats(self.chargepair_ml,lrs):
                            if not self.func_bool_repeats(self.totlist,lrs):
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
                        if not self.func_bool_repeats(self.chargepair_ml,lrt):
                            if not self.func_bool_repeats(self.totlist,lrt):
                                self.chargepair_ml.append(lrt)


        # since for each loop self.chargepair_ml may append two lists,
        # it is important to double check to make sure
        # its length is always no bigger than self.gennm
        if len(self.chargepair_ml) > self.gennm:
            tmp = self.chargepair_ml.pop()

        # finally update self.totlist
        for i in self.chargepair_ml: self.totlist.append(i)



    def file_print(self):
        """overwrite parent method"""
        self.fname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        print('Note: new file < {:} >'.format(self.fname))

        with open(self.fname,mode='wt') as f:
            f.write('# Genetic Algorithm Machine Learning\n')
            f.write('# Total number of charge_pairs are: < {:} >\n\n'.format(self.gennm))

            if len(self.symmetry_list) != 0:
                f.write('# symmetry_list: < {:} >\n'.format(self.file_line_symmetry))
                if len(self.offset_list) != 0:
                    f.write('# offset_list: < {:} >\n'.format(self.file_line_offset))
                    f.write('# offset_nm: < {:} >\n'.format(self.offset_nm))

            if len(self.counter_list) != 0:
                f.write('# counter_list: < {:} >\n'.format(self.file_line_counter))

            if len(self.pn_limit) != 0:
                tmp = [str(i[0]+1) + i[1] for i in self.pn_limit]
                line = ','.join(tmp).strip(',')
                f.write('# pn_limit: < {:} >\n\n'.format(line))

            f.write('# ratio: (ML:Average:Mutation) < {:} >\n'.format(self.ratio))
            f.write('# using ratio: (ML:Average:Mutation) < {:} >\n'.format(self.ratio_new))
            f.write('# threshold: < {:} >\n'.format(self.threshold))
            f.write('# total_charge: < {:} >\n\n'.format(self.total_charge))
            f.write('# bool_neutral: < {:} >\n'.format(self.bool_neutral))
            f.write('# bool_nozero: < {:} >\n\n'.format(self.bool_nozero))

            if self.file_path is not None:
                f.write('# file_path: < {:} >\n'.format(self.file_path))

            if self.charge_path is not None:
                f.write('# charge_path: < {:} >\n\n'.format(self.charge_path))

            nm_nor = len(self.chargepair_nor)
            if nm_nor > 0:
                f.write('# normal charge_range:\n')
                j = 1
                for i in self.charge_list_nor:
                    f.write('#ATOM  {:>4} {:>7}  {:>7}\n'.format(j,i[0],i[1]))
                    j += 1
                f.write('\n\n')

                print('Number of charge pairs generated by the normal charge range are: ',nm_nor)
                f.write('# The charge_pair generated by normal charge_range: ({:})\n\n'.format(nm_nor))
                for i in self.chargepair_nor:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')

            nm_new = len(self.chargepair_new)
            if nm_new > 0:
                f.write('\n\n# charge_extend_by: < {:} >\n'.format(self.charge_extend_by))
                f.write('# With the addition or subtraction, or keeping constant, in both low and high bound\n')
                f.write('# New charge_range:\n\n')
                j = 1
                for i in self.charge_list_new:
                    f.write('#ATOM  {:>4} {:>7}  {:>7}\n'.format(j,round(i[0],3),round(i[1],3)))
                    j += 1
                f.write('\n\n')

                print('Number of charge pairs generated by the new charge range are: ',nm_new)
                f.write('# The charge_pair generated by modified charge_range: ({:})\n\n'.format(nm_new))
                for i in self.chargepair_new:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')

            if self.file_path is not None: f.write('\n\n')

            nm_ml = len(self.chargepair_ml)
            if nm_ml > 0:
                print('Number of charge pairs generated by the Genetic Algorithm are: ',nm_ml)
                f.write('# The charge_pair generated by Genetic Algorithm: ({:})\n\n'.format(nm_ml))
                for i in self.chargepair_ml:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')

            nm_av = len(self.chargepair_av)
            if nm_av > 0:
                print('Number of charge_pairs generated by the Average are: ',nm_av)
                f.write('\n\n# The charge_pair generated by Average: ({:})\n\n'.format(nm_av))
                for i in self.chargepair_av:
                    f.write('PAIR  ')
                    for j in i:
                        f.write('{:>7}'.format(j))
                    f.write('\n')



