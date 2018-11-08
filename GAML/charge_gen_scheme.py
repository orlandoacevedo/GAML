from GAML.functions import file_size_check, file_gen_new,function_roundoff_error, \
                     function_pro_bool_limit
from GAML.function_prolist import Pro_list
import random

class Charge_gen_scheme(object):
    """Randomly generate the charge pairs based on the given charge ranges"""

    def __init__(self,charge_path,symmetry_list=None,counter_list=None,
                 offset_list=None,**kwargs):
        if 'gennm' in kwargs:
            if kwargs['gennm'] is None:
                self.gennm = 5
            else:
                try:
                    self.gennm = int(kwargs['gennm'])
                    if self.gennm <= 0:
                        raise ValueError
                except:
                    print('Error: the parameter gennm has to be a positive integer')
                    exit()
        else:
            self.gennm = 5


        if 'nmround' in kwargs:
            if kwargs['nmround'] is None:
                self.nmround = 2
            else:
                try:
                    self.nmround = int(kwargs['nmround'])
                    if self.nmround <= 0:
                        raise ValueError
                except:
                    print('Error: the parameter nmround has to be a positive integer')
                    exit()
        else:
            self.nmround = 2
            

        if 'total_charge' in kwargs:
            if kwargs['total_charge'] is None:
                self.total_charge = 1.0
            else:
                try:
                    self.total_charge = float(kwargs['total_charge'])
                except:
                    print('Error: the parameter total_charge has to be a number')
                    exit()
        else:
            self.total_charge = 1.0
            

        if 'fname' in kwargs:
            if kwargs['fname'] is None:
                self.fname = 'ChargeRandomGen'
            else:
                self.fname = kwargs['fname']
        else:
            self.fname = 'ChargeRandomGen'
            

        if 'in_keyword' in kwargs:
            if kwargs['in_keyword'] is None:
                self.in_keyword = 'ATOM'
            else:
                self.in_keyword = kwargs['in_keyword']
        else:
            self.in_keyword = 'ATOM'


        if 'bool_neutral' in kwargs:
            if kwargs['bool_neutral'] is None:
                self.bool_neutral = True
            else:
                self.bool_neutral = False if (kwargs['bool_neutral']is False) else True
        else:
            self.bool_neutral = True


        if 'bool_nozero' in kwargs:
            if kwargs['bool_nozero'] is None:
                self.bool_nozero = True
            else:
                self.bool_nozero = False if (kwargs['bool_nozero'] is False) else True
        else:
            self.bool_nozero = True


        if 'bool_limit' in kwargs:
            if kwargs['bool_limit'] is None:
                self.bool_limit = []
            elif isinstance(kwargs['bool_limit'],list):
                self.bool_limit = kwargs['bool_limit']
            elif isinstance(kwargs['bool_limit'],str):
                if len(kwargs['bool_limit']) == 0 or len(kwargs['bool_limit'].split()) == 0:
                    self.bool_limit = []
                else:
                    self.file_line_limit = kwargs['bool_limit']
                    self.bool_limit = function_pro_bool_limit(kwargs['bool_limit'],False)
            else:
                print('Error: the parameter bool_limit is not correctly defined')
                print('     : ',kwargs['bool_limit'])
                exit()
        else:
            self.bool_limit = []


        if 'threshold' in kwargs:
            if kwargs['threshold'] is None:
                self.threshold = 1.0
            else:
                try:
                    self.threshold = float(kwargs['threshold'])
                    if self.threshold < 0.3:
                        raise ValueError
                except:
                    print('Error: the parameter threshold has to be greater than 0.3')
                    exit()
        else:
            self.threshold = 1.0


        if 'offset_nm' in kwargs:
            if kwargs['offset_nm'] is None:
                self.offset_nm = 5
            else:
                try:
                    self.offset_nm = int(kwargs['offset_nm'])
                    if self.offset_nm <= 0:
                        raise ValueError
                except:
                    print('Error: the parameter offset_nm has to be a positive integer')
                    exit()
        else:
            self.offset_nm = 5

        if self.total_charge == 0:
            self.bool_neutral = False

        if self.bool_neutral and self.nmround < 3:
            print('Error: When bool_neutral is set to True, the nmround should be not less than 2')
            exit()


        if symmetry_list is None:
            self.symmetry_list = None
        elif isinstance(symmetry_list,list):
            self.symmetry_list = None if len(symmetry_list) == 0 else symmetry_list
        else:
            print('Error: the parameter symmetry_list has to be a list')
            exit()
            
        if counter_list is None:
            self.counter_list = None
        elif isinstance(counter_list,list):
            self.counter_list = None if len(counter_list) == 0 else counter_list
        else:
            print('Error: the parameter counter_list has to be a list')
            exit()
            

        self.charge_path = charge_path
        self.charge_list = self._f_pro_charge_path(charge_path)

        rmax = 0
        if len(self.bool_limit) != 0:
            ls = [i[0] for i in self.bool_limit]
            rmax = max(rmax,max(ls))
        if rmax > len(self.charge_list):
            print('Error: some entries in parameter bool_limit are out of the index')
            print('     : the biggest number can be defined is ',len(charge_list))
            print('     : however, the number in bool_limit is ', rmax)
            exit()
        
        if (self.symmetry_list is None) and (self.counter_list is None):
            self.chargepair = self.gen_chargepair_file()
        else:          
            self.prolist = Pro_list(symmetry_list=self.symmetry_list,counter_list=self.counter_list,
                                    offset_list=offset_list)

            if len(self.prolist.symmetry_list) == 2 and len(self.prolist.reflist) != 0 and self.total_charge != 0:
                print('Error: if only two parameters are in perturbation and they are set to counter')
                print('Error: then the total_charge has to be equal to zero')
                exit()

            self.reflist = self.prolist.reflist

            if len(self.prolist.symmetry_list) == 0:
                rmax = [max(i[0],i[2]) for i in self.prolist.reflist]
                if len(self.charge_list) < 2*len(rmax) or len(self.charge_list) < max(rmax):
                    print('Error: the charge_path and counter_list are not corresponded')
                    exit()
                self.chargepair = self.gen_chargepair_counter()
                
            else:
                self.symmetry_list = self.prolist.symmetry_list
                self.offset_list = self.prolist.offset_list
                
                if len(self.charge_list) < self.prolist.symmetry_length:
                    print('Error: the charge_path and symmetry_list are not corresponded')
                    exit()

                if len(self.symmetry_list) <= 4 and len(self.prolist.reflist) != 0:    
                    self.chargepair = self.gen_chargepair_counter()
                else:
                    self.chargepair = self.gen_chargepair_symmetry()


    def _f_pro_charge_path(self,charge_path):
        
        if isinstance(charge_path,list):
            # change the list name
            charge_list = charge_path
            if len(charge_path) == 0:
                print('Error: it seems the charge_path is a list, however, its length cannot be zero')
                exit()

            for i in charge_list:
                if isinstance(i,list) and len(i) == 2 and (isinstance(i[0],int) or isinstance(i[0],float)) \
                   and (isinstance(i[1],int) or isinstance(i[1],float)):
                    pass
                else:
                    print('Error: the charge_path has to be a 2D nested number list')
                    print('       and its each sublist only contains two indices')
                    exit()                   
                
        elif isinstance(charge_path,str):
            
            dump_value = file_size_check(charge_path,fsize=100)
            
            charge_list = []
            with open(charge_path,mode='rt') as f:
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    else:
                        ltmp = line[:line.find('#')].split()
                        if len(ltmp) != 0 and ltmp[0] == self.in_keyword:
                            ls = []
                            ls.append(float(ltmp[2]))
                            ls.append(float(ltmp[3]))
                            charge_list.append(ls)               
        return charge_list



    def gen_chargepair_file(self):
        """Randomly generate charge_pairs based on the given input charge_file"""

        self.counter_list = []
        self.reflist = []

        return self.gen_chargepair_counter()



    def gen_chargepair_counter(self):
        """Randomly generate charge_pairs based on the given charge range
           and counter_list"""

        # avoid wrong calling
        if self.counter_list is None:
            print('Error: the symmetry_list is not defined')
            exit()
            
        # make a copy of counter_list -> reflist
        refcntlist = self.reflist[:]

        refcntlist_lth = 2*len(refcntlist)
        refcntlist_ndx = []
        for i in refcntlist:
            refcntlist_ndx.append(i[0])
            refcntlist_ndx.append(i[2])
        
        if self.bool_neutral:
            calc_total_charge = 1.0
            calc_nmround = self.nmround - 1
        else:    
            calc_total_charge = self.total_charge
            calc_nmround = self.nmround

        multibase = 10 ** calc_nmround
        chargepair = []
        while len(chargepair) < self.gennm:
            totcharge = 0.0
            subcharp = []
            reflist = list(range( len(self.charge_list)  ) )
            while len(reflist) > refcntlist_lth:

                while True:
                    ix = random.randrange( len(reflist) )
                    ndx = reflist[ix]
                    if ndx not in refcntlist_ndx:
                        reflist.remove(ndx)
                        break

                chmin = self.charge_list[ndx][0] + 0.0
                chmax = self.charge_list[ndx][1] + 0.0

                if chmax < chmin:
                    t = chmax
                    chmax = chmin
                    chmin = t
                elif chmax == chmin:
                    chmax += 5.0/multibase

                rch = random.randrange(int(chmin*multibase),int(chmax*multibase))
                
                lp = []
                lp.append(ndx)
                charget = round(float(rch)/multibase,calc_nmround)
                totcharge =  totcharge + charget
                lp.append(charget)
                subcharp.append(lp)

                   
            for cnt in refcntlist:
               
                chmin = self.charge_list[cnt[0]][0] + 0.0
                chmax = self.charge_list[cnt[0]][1] + 0.0
                rch = random.randrange(int(chmin*multibase),int(chmax*multibase))

                charget = float(rch) / multibase
                charcnt = 0 - charget * cnt[1] / cnt[3]

                lp = [cnt[0],]
                lt = [cnt[2],]

                # take care of the round-off-error
                while True:
                    bo,charget,getndx,charcnt,cntndx = function_roundoff_error(
                                                        charget,cnt[1],charcnt,cnt[3],
                                                        nmround=calc_nmround
                                                        )
                    # since it is a counter charge, get its opposite number
                    if bo:
                        lp.append(charget)
                        subcharp.append(lp)
                        lt.append(charcnt)
                        subcharp.append(lt)
                        break

            # Now, apply the charge constrain
            if round(totcharge - calc_total_charge, calc_nmround + 2) != 0:
                # randomly choose a chargepair but not the counter-pair-charge
                while True:
                    j = random.randrange(len(self.charge_list))
                    if j in refcntlist_ndx:
                        continue

                    cnt = 0
                    while cnt < len(subcharp):
                        if subcharp[cnt][0] == j:
                            break
                        cnt += 1

                    chartmp = ( calc_total_charge - totcharge ) + subcharp[cnt][1]
                    chartmp = round(chartmp,calc_nmround)

                    err = chartmp + totcharge - calc_total_charge - subcharp[cnt][1]
                    if round(err,calc_nmround+2) == 0:
                        subcharp[cnt][1] = chartmp
                        break

            # adjust subcharp list to correspond to self.charge_list
            ltmp = []
            i = 0
            while i < len(self.charge_list):
                for j in subcharp:
                    if j[0] == i:
                        ltmp.append(j[1])
                        break
                i += 1


            # apply the bool_limit, take care the python index starts at zero
            bool_tmp_limit = False
            for i in self.bool_limit:
                v = ltmp[i[0]-1]
                if i[1] == 'p' and v < 0:
                    bool_tmp_limit = True
                    break
                elif i[1] == 'n' and v > 0:
                    bool_tmp_limit = True
                    break
                
            if bool_tmp_limit:
                continue
            

            # apply charge threshold
            if max(abs(min(ltmp)),abs(max(ltmp))) <= self.threshold:
                
                if self.bool_neutral:
                    ltmp = [round(i*self.total_charge,self.nmround) for i in ltmp]

                if len(ltmp) == len(self.charge_list) and (self.bool_nozero or (not 0 in ltmp)):
                    if not self._f_remove_repeats(chargepair,ltmp):
                        chargepair.append(ltmp)
                
        return chargepair


    
    def gen_chargepair_symmetry(self):
        """Randomly generate charge_piars based on the given charege range,
           symmetry_list and counter_list"""

        # avoid wrong calling
        if self.symmetry_list is None:
            print('Error: the symmetry_list is not defined')
            exit()
       
        # make a copy of counter_list -> reflist
        refcntlist = self.prolist.reflist[:]

        # this list is used only when len(refcntlist) is not zero
        cmpreflist = []
        for i in refcntlist:
            cmpreflist.append(i[0])
            cmpreflist.append(i[2])

        if self.bool_neutral:
            calc_total_charge = 1.0
            calc_nmround = self.nmround - 1
        else:    
            calc_total_charge = self.total_charge
            calc_nmround = self.nmround

        multibase = 10 ** calc_nmround
        chargepair = []   
        while len(chargepair) < self.gennm:
            totcharge = 0.0
            subcharp = []
            reflist = list(range( len(self.symmetry_list)  ) )
            while len(reflist) > len(self.offset_list):

                while True:
                    ix = random.randrange( len(reflist) )
                    refndx = reflist[ix]
                    if refndx not in self.prolist.offset_ndx_list:
                        ndx = self.symmetry_list[ refndx ]
                        reflist.remove(refndx)
                        break

                bool_counter = False   
                for cmpndx in refcntlist:
                    if refndx in (cmpndx[0],cmpndx[2]):
                        if refndx == cmpndx[0]:
                            bool_calcndx = True
                        else:
                            bool_calcndx = False
                        bool_counter = True
                        break
                                       
                if isinstance(ndx,int):
                    ndxlth = 1
                    j = ndx
                else:
                    ndxlth = len(ndx)
                    ix = random.randrange(ndxlth)
                    j = ndx[ix]

                chmin = self.charge_list[j][0] + 0.0
                chmax = self.charge_list[j][1] + 0.0

                if chmax < chmin:
                    t = chmax
                    chmax = chmin
                    chmin = t
                elif chmax == chmin:
                    chmax += 5.0/multibase

                rch = random.randrange(int(chmin*multibase),int(chmax*multibase))
                
                lp = []
                lp.append(ndx)
                charget = round(float(rch)/multibase,calc_nmround)
              
                # calculate counterpart charge
                if bool_counter:

                    lt = []
                    if bool_calcndx:
                        # update the reflist
                        reflist.remove(cmpndx[2])
                        lt.append(self.symmetry_list[cmpndx[2]])
                        charcnt = 0 - charget * cmpndx[1] / cmpndx[3]
                        getndx = cmpndx[1]
                        cntndx = cmpndx[3]
                    else:
                        reflist.remove(cmpndx[0])
                        lt.append(self.symmetry_list[cmpndx[0]])
                        charcnt = 0 - charget * cmpndx[3] / cmpndx[1]
                        getndx = cmpndx[3]
                        cntndx = cmpndx[1]
                        
                    # take care of the round-off-error
                    while True:
                        bo,charget,getndx,charcnt,cntndx = function_roundoff_error(
                                                            charget,getndx,charcnt,cntndx,
                                                            nmround=calc_nmround
                                                            )
                        # since it is a counter charge, get its opposite number
                        if bo:
                            lt.append(charcnt)
                            subcharp.append(lt)
                            lp.append(charget)
                            subcharp.append(lp)
                            break
                else:
                    totcharge =  totcharge + charget * ndxlth
                    lp.append(charget)
                    subcharp.append(lp)  


            # Now, take care of the offset_nm to apply the charge constrain
            # it is divided into three different situations, where when the length of self.offset_list
            #   is equal to 0, 1 and 2

            if len(self.offset_list) == 0 or len(self.offset_list) == 1:

                if len(self.offset_list) == 1:
                    ndx = self.symmetry_list[self.prolist.offset_0_ndx]
                    if isinstance(ndx,int):
                        ndxlth = 1
                        j = ndx
                    else:
                        ndxlth = len(ndx)
                        ix = random.randrange(ndxlth)
                        j = ndx[ix]
                    
                    chmin = self.charge_list[j][0] + 0.0
                    chmax = self.charge_list[j][1] + 0.0

                    if chmax < chmin:
                        t = chmax
                        chmax = chmin
                        chmin = t
                    elif chmax == chmin:
                        chmax += 5.0/multibase

                    rch = random.randrange(int(chmin*multibase),int(chmax*multibase))
                    rch = round(float(rch)/multibase,calc_nmround) 
                    totcharge += rch * ndxlth
                    
                    lp = []
                    lp.append(ndx)
                    lp.append(rch)
                    subcharp.append(lp)

                if round(totcharge - calc_total_charge, calc_nmround + 2) != 0:
                    # randomly choose a chargepair but not the counter-pair-charge
                    while True:
                        j = random.randrange(len(self.symmetry_list))
                        if j in cmpreflist:
                            continue

                        offsetndx = self.symmetry_list[j]
                        if isinstance(offsetndx,int):
                            offset_lth = 1
                        else:
                            offset_lth = len(offsetndx)

                        cnt = 0
                        while cnt < len(subcharp):
                            if subcharp[cnt][0] == offsetndx:
                                break
                            cnt += 1

                        chartmp = ( calc_total_charge - totcharge ) / offset_lth + subcharp[cnt][1]
                        chartmp = round(chartmp,calc_nmround)

                        err = chartmp*offset_lth + totcharge - calc_total_charge - subcharp[cnt][1]*offset_lth
                        if round(err,calc_nmround+2) == 0:
                            subcharp[cnt][1] = chartmp
                            break
            else:
                bool_charge_index = True
                subcharsum = 0.0
                for dump in range(self.offset_nm):
                    offset_totcharge = totcharge
                    
                    if self.prolist.bool_offset_1:
                        ndx = self.symmetry_list[ self.prolist.offset_1_ndx ]
                        ndxlth_1 = len(ndx)
                        ix = random.randrange(ndxlth_1)
                        j = ndx[ix]
                    else:
                        ndxlth_1 = 1
                        j = self.symmetry_list[ self.prolist.offset_1_ndx ]

                    chmin = self.charge_list[j][0] + 0.0
                    chmax = self.charge_list[j][1] + 0.0

                    if chmax < chmin:
                        t = chmax
                        chmax = chmin
                        chmin = t
                    elif chmax == chmin:
                        chmax += 5.0/multibase

                    genrch = random.randrange(int(chmin*multibase),int(chmax*multibase))
                    genrch = round(float(genrch) / multibase,calc_nmround)
                    subcharsum += genrch
                    offset_totcharge += genrch * ndxlth_1

                    if self.prolist.bool_offset_0:
                        ndx = self.symmetry_list[ self.prolist.offset_0_ndx ]
                        ndxlth_0 = len(ndx)
                        ix = random.randrange(ndxlth_0)
                        j = ndx[ix]
                    else:
                        ndxlth_0 = 1
                        j = self.symmetry_list[ self.prolist.offset_0_ndx ]

                    chmin = self.charge_list[j][0] + 0.0
                    chmax = self.charge_list[j][1] + 0.0

                    if chmax < chmin:
                        t = chmax
                        chmax = chmin
                        chmin = t
                    elif chmax == chmin:
                        chmax += 5.0/multibase

                    rch = ( calc_total_charge - offset_totcharge ) / ndxlth_0
                    rch = round(rch,calc_nmround)
                    offset_totcharge += rch * ndxlth_0

                    if rch >= chmin and rch <= chmax and \
                       round(calc_total_charge - offset_totcharge,calc_nmround+2) == 0:
                        lp = []
                        lp.append( self.symmetry_list[ self.prolist.offset_1_ndx ] )
                        lp.append( genrch )
                        subcharp.append(lp)
                        
                        lp = []
                        lp.append( self.symmetry_list[ self.prolist.offset_0_ndx ] )
                        lp.append( rch )
                        subcharp.append(lp)
                        
                        bool_charge_index = False
                        break


                if bool_charge_index:
                    ndx_1 = self.symmetry_list[ self.prolist.offset_1_ndx ]
                    ndxlth_1 = len( ndx_1 ) if self.prolist.bool_offset_1 else 1

                    genrch = round(subcharsum/self.offset_nm,calc_nmround)
                    rtmp = calc_total_charge - totcharge - ( genrch * ndxlth_1 )

                    ndx_0 = self.symmetry_list[ self.prolist.offset_0_ndx ]
                    ndxlth_0 = len( ndx_0 ) if self.prolist.bool_offset_0 else 1

                    rch = round(rtmp / ndxlth_0,calc_nmround)

                    err = rtmp - ( rch * ndxlth_0 )
                    if round(err,calc_nmround+2) == 0:             
                        lp = []
                        lp.append( ndx_1 )
                        lp.append( genrch )
                        subcharp.append(lp)
                            
                        lp = [] 
                        lp.append( ndx_0 )
                        lp.append( rch )
                        subcharp.append(lp)
                    else:
                        # start from the beginning, the new generation
                        continue

                
            # adjust subcharp list to correspond to symmetry_list
            ltmp = []
            for i in self.symmetry_list:
                for j in subcharp:
                    if isinstance(i,int) and isinstance(j[0],int) and i == j[0]:
                        ltmp.append(j[1])
                        break
                    elif isinstance(i,list) and isinstance(j[0],list) and i == j[0]: 
                        ltmp.append(j[1])
                        break


            # apply the bool_limit, take care the python index starts at zero
            bool_tmp_limit = False
            for i in self.bool_limit:
                v = ltmp[i[0]-1]
                if i[1] == 'p' and v < 0:
                    bool_tmp_limit = True
                    break
                elif i[1] == 'n' and v > 0:
                    bool_tmp_limit = True
                    break
                
            if bool_tmp_limit:
                continue


            # apply charge threshold
            if max(abs(min(ltmp)),abs(max(ltmp))) <= self.threshold:
                
                if self.bool_neutral:
                    ltmp = [round(i*self.total_charge,self.nmround) for i in ltmp]

                if len(ltmp) == len(self.symmetry_list) and ((not self.bool_nozero) or (not 0 in ltmp)):
                    if not self._f_remove_repeats(chargepair,ltmp):
                        chargepair.append(ltmp)

        return chargepair


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
            


    def file_print(self):

        fname = file_gen_new(self.fname,fextend='txt')
        with open(fname,mode='wt') as f:
            f.write('# This is the randomly generated charge pairs based on charge_range_list \n\n')

            if self.symmetry_list is not None:
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:s}\n\n'.format(self.prolist.file_line_symmetry))
                if len(self.prolist.file_line_offset) != 0:
                    f.write('# The offset_list used is:\n')
                    f.write('#    {:s}\n\n'.format(self.prolist.file_line_offset))

            if (self.counter_list is not None) and len(self.counter_list) != 0:
                f.write('# The counter_list used is:\n')
                f.write('#   {:s}\n\n'.format(self.prolist.file_line_counter))

            if len(self.bool_limit) != 0:
                f.write('# The bool_limit used is:\n')
                f.write('#   {:s}\n\n'.format(self.file_line_limit))
                
            f.write('# The total_charge is: < {:} >\n\n'.format(self.total_charge))
            f.write('# The bool_neutral is: < {:s} >\n\n'.format('ON' if self.bool_neutral else 'OFF'))
            f.write('# The bool_nozero is: < {:s} >\n\n'.format('ON' if self.bool_nozero else 'OFF'))
            
            if isinstance(self.charge_path,str):
                f.write('# The used charge_range file is:\n#    {:s}\n\n'.format(self.charge_path))

            f.write('# For each entry, the charge_range is:\n\n')
            j = 1
            for i in self.charge_list:
                f.write('# ATOM  {:>3}    {:>8}    {:>8}\n'.format(j,i[0],i[1]))
                j += 1

            f.write('\n\n# The randomly generated charges are: \n\n')

            for i in self.chargepair:
                f.write('PAIR ')
                for j in i:
                    f.write('{:>7.3}'.format(j))
                f.write('\n')
            f.write('\n\n')
                
        return 1

