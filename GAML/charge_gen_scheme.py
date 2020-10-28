from GAML.functions import file_size_check, file_gen_new, func_roundoff_error, func_pro_pn_limit
from GAML.function_prolist import Prolist
import random

class Charge_gen_scheme(object):
    """Randomly generate the charge pairs based on the given charge ranges"""

    def __init__(self,*args,**kwargs):
        self.log = {'nice':True,'info':''}

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
            self.gennm = 5


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


        if 'total_charge' in kwargs and kwargs['total_charge'] is not None:
            try:
                self.total_charge = float(kwargs['total_charge'])
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter total_charge has to be a number'
                return
        else:
            self.total_charge = 0.0


        if 'fname' in kwargs and kwargs['fname'] is not None:
            if isinstance(kwargs['fname'],str):
                if len(kwargs['fname'].split()) != 0:
                    self.fname = kwargs['fname']
                else:
                    self.fname = 'ChargeRandomGen'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter fname is not correctly defined'
        else:
            self.fname = 'ChargeRandomGen'


        if 'in_keyword' in kwargs and kwargs['in_keyword'] is not None:
            if isinstance(kwargs['in_keyword'],str):
                if len(kwargs['in_keyword'].split()) != 0:
                    self.in_keyword = kwargs['in_keyword']
                else:
                    self.in_keyword = 'ATOM'
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: parameter in_keyword is not correctly defined'
        else:
            self.in_keyword = 'ATOM'


        if 'bool_neutral' in kwargs and kwargs['bool_neutral'] is not None:
            self.bool_neutral = True if (kwargs['bool_neutral'] is True) else False
        else:
            self.bool_neutral = False


        if 'bool_nozero' in kwargs and kwargs['bool_nozero'] is not None:
            self.bool_nozero = False if (kwargs['bool_nozero'] is False) else True
        else:
            self.bool_nozero = True


        if 'pn_limit' in kwargs and kwargs['pn_limit'] is not None:
            bo = False
            if isinstance(kwargs['pn_limit'],list):
                self.pn_limit = kwargs['pn_limit']
                for i in self.pn_limit:
                    if ( not isinstance(i,list) ) or len(i) != 2 or ( not isinstance(i[0],int) ) or \
                        ( i[1] not in ['p','n'] ):
                        bo = True
                        break
            elif isinstance(kwargs['pn_limit'],str):
                if len(kwargs['pn_limit']) == 0 or len(kwargs['pn_limit'].split()) == 0:
                    self.pn_limit = []
                else:
                    self.log, plist = func_pro_pn_limit(kwargs['pn_limit'],bool_repeats=False)
                    if not self.log['nice']: return
                    # take care of index starting number is not from 0
                    # double check: make sure no negative values
                    self.pn_limit = []
                    for i in plist:
                        if i[0] - 1 < 0:
                            bo = True
                            break
                        self.pn_limit.append([i[0]-1,i[1]])
            else:
                bo = True
            if bo:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter pn_limit is not correctly defined\n' + \
                                   '     : {:}'.format(kwargs['pn_limit'])
                return
        else:
            self.pn_limit = []


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
            self.threshold = 0.8


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

        if self.total_charge == 0: self.bool_neutral = False

        if self.bool_neutral and self.nmround < 2:
            self.log['nice'] = False
            self.log['info'] = 'Error: When bool_neutral is set to True, the nmround should be not less than 2'
            return


        if 'charge_path' in kwargs and kwargs['charge_path'] is not None:
            self.charge_path = kwargs['charge_path']
            self.charge_list = self.prochargepath(kwargs['charge_path'])
            if not self.log['nice']: return
        else:
            self.charge_path = None
            self.charge_list = []

        if len(self.charge_list) != 0 and len(self.pn_limit) != 0:
            if max([i[0] for i in self.pn_limit]) > len(self.charge_list):
                self.log['nice'] = False
                self.log['info'] = 'Error: some entries in parameter pn_limit are out of the index\n' + \
                                   '     : the number of charge_path is ' + str(len(charge_list)) + '\n' + \
                                   '     : however, the number of pn_limit is ' + str(max(self.pn_limit))
                return


        symmetry_list = kwargs['symmetry_list'] if 'symmetry_list' in kwargs else None
        counter_list = kwargs['counter_list'] if 'counter_list' in kwargs else None
        offset_list = kwargs['offset_list'] if 'offset_list' in kwargs else None

        self.prolist = Prolist(symmetry_list=symmetry_list,counter_list=counter_list,offset_list=offset_list)
        if not self.prolist.log['nice']:
            self.log['nice'] = False
            self.log['info'] = self.prolist.log['info']
            return

        self.symmetry_list = self.prolist.symmetry_list
        self.reflist = self.prolist.reflist

        if len(self.symmetry_list) == 0 and len(self.charge_list) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: neither symmetry_list nor charge_path is defined!'
            return

        if len(self.symmetry_list) == 0:
            self.symmetry_list = list(range(len(self.charge_list)))
        elif len(self.symmetry_list) == 2 and len(self.reflist) != 0 and self.total_charge != 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: if only two parameters are in perturbation and they are set to counter \n' + \
                               '     : then the total_charge has to be equal to zero'
            return

        if len(self.charge_list) == 0:
            for i in range(self.prolist.symmetry_length):
                self.charge_list.append([-self.threshold/2,self.threshold/2])
        elif self.prolist.symmetry_length != 0 and len(self.charge_list) < self.prolist.symmetry_length:
            self.log['nice'] = False
            self.log['info'] = 'Error: the charge_path and symmetry_list are not corresponded'
            return


        ndxreflist = [i[0] for i in self.reflist] + [i[2] for i in self.reflist]
        if len(ndxreflist) != 0 and len(self.charge_list) < max(ndxreflist):
            self.log['nice'] = False
            self.log['info'] = 'Error: the charge_path and counter_list are not corresponded'
            return

        ndxpnlist = [i[0] for i in self.pn_limit]
        vulist = [i[1] for i in self.pn_limit]
        if len(ndxpnlist) != 0 and self.prolist.symmetry_length < max(ndxpnlist):
                self.log['nice'] = False
                self.log['info'] = 'Error: the symmetry_list and pn_limit are not corresponded'
                return
        for i in self.reflist:
            if (i[0] in ndxpnlist) and (i[2] in ndxpnlist):
                if vulist[i[0]] == vulist[i[2]]:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: the pn_limit is in conflict with counter_list\n' + \
                                        '     : they have to be one in positive and the other in negative'
                    return

        # softly update self.prolist.offset_ndx_list to avoid "counter_list" conflicts
        if len(self.prolist.offset_list) == 2:
            if self.prolist.offset_ndx_list[1] in ndxreflist:
                self.prolist.offset_ndx_list = [self.prolist.offset_ndx_list[0],]
                self.prolist.offset_1_ndx = 0
        if len(self.prolist.offset_list) == 1:
            if self.prolist.offset_ndx_list[0] in ndxreflist:
                self.prolist.offset_ndx_list = []

        # pre-process self.charge_list: make sure index(0) < index(1)
        self.prochargelist()



    def prochargelist(self):
        """Parameter:
              self.charge_list; self.bool_neutral; self.nmround; self.threshold
           Result:
              return a charge_list meeting the needed low-high bound"""

        if self.bool_neutral:
            calc_nmround = self.nmround - 1
        else:
            calc_nmround = self.nmround

        multibase = 10 ** calc_nmround
        for i in range(len(self.charge_list)):
            chmin = self.charge_list[i][0]
            chmax = self.charge_list[i][1]
            if chmax < chmin: chmax, chmin = chmin, chmax
            if chmin > 0:
                chmin = chmin if chmin < self.threshold else self.threshold
            else:
                chmin = chmin if chmin > -self.threshold else -self.threshold
            if chmax > 0:
                chmax = chmax if chmax < self.threshold else self.threshold
            else:
                chmax = chmax if chmax > -self.threshold else -self.threshold
            # from debug; take care of round off error
            if chmax-chmin < 20.0/multibase:
                tmp = chmax + 20.0 / multibase
                if tmp > self.threshold:
                    chmin = chmin - 20.0 / multibase
                else:
                    chmax = tmp

            self.charge_list[i][0] = chmin
            self.charge_list[i][1] = chmax


    def prochargepath(self,charge_path):
        """Parameter:
                charge_path, with defined chargeRange, either can be a 2D list, or a string file name
           Result:
                charge_list"""

        if isinstance(charge_path,list):
            # change the list name
            charge_list = charge_path
            if len(charge_path) == 0:
                return []

            for i in charge_list:
                if isinstance(i,list) and len(i) == 2 and isinstance(i[0],(float,int)) and isinstance(i[1],(float,int)):
                    pass
                else:
                    self.log['nice'] = False
                    self.log['info'] = 'Error: the charge_path has to be a 2D nested number list\n' + \
                                       '       and its each sublist only contains two indices'
                    return []
        elif isinstance(charge_path,str):
            if len(charge_path.split()) == 0:
                return []

            self.log = file_size_check(charge_path,fsize=100)
            if not self.log['nice']: return []

            charge_list = []
            with open(charge_path,mode='rt') as f:
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    else:
                        ltmp = line[:line.find('#')].split()
                        bo = False
                        if len(ltmp) == 0:
                            continue
                        elif len(ltmp) == 4 and ltmp[0] == self.in_keyword:
                            try:
                                t1 = float(ltmp[2])
                                t2 = float(ltmp[3])
                                charge_list.append([t1,t2])
                            except ValueError:
                                bo = True
                        else:
                            bo = True

                        if bo:
                            self.log['nice'] = False
                            self.log['info'] = 'Error: Wrong for the input file, in line\n' + \
                                               '     : %s' % line
                            return []
        return charge_list



    def run(self,filterlist=[]):
        """Randomly generate charge_piars based on the given charge range,
           symmetry_list and counter_list with no any repeats in 2D filterlist

           Result:
                self.chargepair with self-exclusive number of self.gennm pairs"""

        if self.bool_neutral:
            calc_total_charge = 1.0
            calc_nmround = self.nmround - 1
        else:
            calc_total_charge = self.total_charge
            calc_nmround = self.nmround

        pnlist = [self.symmetry_list[i[0]] for i in self.pn_limit]
        vulist = [i[1] for i in self.pn_limit]

        # make a SHALLOW copy of self.symmetry_list and remove self.reflist indices
        copysymmetry = self.symmetry_list[:]
        for i in self.reflist:
            si = self.symmetry_list[i[0]]
            sj = self.symmetry_list[i[2]]
            # Find symmetry indices
            for symi in copysymmetry:
                if isinstance(symi,int) and isinstance(si,int) and symi == si:
                    break
                elif isinstance(symi,list) and isinstance(si,list) and symi == si:
                    break
            for symj in copysymmetry:
                if isinstance(symj,int) and isinstance(sj,int) and symj == sj:
                    break
                elif isinstance(symj,list) and isinstance(sj,list) and symj == sj:
                    break
            # update
            copysymmetry.remove(symi)
            copysymmetry.remove(symj)

        trynmcnt = 1
        trynmtot = self.gennm * 100 if len(copysymmetry) > 1000 else 100000
        multibase = 10 ** calc_nmround
        self.chargepair = []
        while len(self.chargepair) < self.gennm:

            # add a condition avoid infinite looping
            if trynmcnt > trynmtot:
                self.log['nice'] = False
                self.log['info'] = 'Error: the gennm is too big for pairs generating'
                return
            trynmcnt += 1

            totcharge = 0.0
            subcharp = []

            # Take care of counter_list
            for i in self.reflist:
                chmin = self.charge_list[i[0]][0]
                chmax = self.charge_list[i[0]][1]

                chi = random.randrange(int(chmin*multibase),int(chmax*multibase))
                chi = float(chi) / multibase
                chj = 0 - chi * i[1] / i[3]

                while True:
                    bo,chi,i[1],chj,i[3] = func_roundoff_error(chi,i[1],chj,i[3],nmround=calc_nmround)

                    # apply self.bool_nozero
                    if bo and self.bool_nozero and ( chi == 0 or chj == 0 ): bo = False

                    # apply self.threshold
                    if bo and abs(chi) > self.threshold:
                        chi = chi - self.threshold if chi > 0 else chi - self.threshold
                        chj = 0 - chi * i[1] / i[3]
                        bo = False
                    if bo and abs(chj) > self.threshold:
                        chj = chj - self.threshold if chj > 0 else chj - self.threshold
                        chi = 0 - chj * i[3] / i[1]
                        bo = False

                    # apply self.pn_limit
                    if bo and ( symi in pnlist ):
                        v = vulist[pnlist.index(symi)]
                        if ( v == 'p' and chi <= 0 ) or ( v == 'n' and chi >= 0 ):
                            chi = 0 - chi
                            chj = 0 - chj
                            bo = False
                    if bo and ( symj in pnlist ):
                        v = vulist[pnlist.index(symj)]
                        if ( v == 'p' and chj <= 0 ) or ( v == 'n' and chj >= 0 ):
                            chi = 0 - chi
                            chj = 0 - chj
                            bo = False
                    if bo:
                        subcharp.append([symi,chi])
                        subcharp.append([symj,chj])
                        break

            # based on copysymmetry, calculate new offlist for self.prolist.offset_ndx_list
            offlist = []
            for i,tmp in enumerate(self.prolist.offset_list):
                t = self.symmetry_list[self.prolist.offset_ndx_list[i]]
                offlist.append(copysymmetry.index(t))

            ndxlist = list(range(len(copysymmetry)))
            while len(ndxlist) > len(offlist):
                while True:
                    ix = random.randrange( len(ndxlist) )
                    refndx = ndxlist[ix]
                    if refndx not in offlist:
                        ndx = copysymmetry[refndx]
                        # update ndxlist
                        ndxlist.remove(refndx)
                        break

                if isinstance(ndx,int):
                    ndxlth = 1
                    j = ndx
                else:
                    ndxlth = len(ndx)
                    ix = random.randrange(ndxlth)
                    j = ndx[ix]

                chmin = int( self.charge_list[j][0] * multibase )
                chmax = int( self.charge_list[j][1] * multibase )

                while True:
                    rch = random.randrange(chmin,chmax)

                    # apply self.bool_nozero & self.pn_limit
                    bo = True
                    if self.bool_nozero and rch == 0: bo = False
                    if bo and ndx in pnlist:
                        t = vulist[pnlist.index(ndx)]
                        if ( t == 'p' and rch <= 0 ) or ( t == 'n' and rch >= 0 ):
                            bo = False
                    if bo:
                        charget = round(float(rch)/multibase,calc_nmround)
                        subcharp.append([ndx,charget])
                        # update totcharge
                        totcharge += charget * ndxlth
                        break


            # Now, take care of the offset_nm to apply the charge constrain
            # it is divided into three different situations, where when the length of self.offset_list
            #   is equal to 0, 1 or 2
            if len(self.prolist.offset_list) == 0 or len(self.prolist.offset_list) == 1:
                if len(self.prolist.offset_list) == 1:
                    ndx = self.symmetry_list[self.prolist.offset_0_ndx]
                    if isinstance(ndx,int):
                        ndxlth = 1
                        j = ndx
                    else:
                        ndxlth = len(ndx)
                        ix = random.randrange(ndxlth)
                        j = ndx[ix]

                    chmin = int( self.charge_list[j][0] * multibase )
                    chmax = int( self.charge_list[j][1] * multibase )

                    while True:
                        rch = random.randrange(chmin,chmax)
                        rch = round(float(rch)/multibase,calc_nmround)
                        # apply self.bool_nozero & self.pn_limit
                        bo = True
                        if self.bool_nozero and rch == 0: bo = False
                        if bo and ndx in pnlist:
                            t = vulist[pnlist.index(ndx)]
                            if ( t == 'p' and rch <= 0 ) or ( t == 'n' and rch >= 0 ):
                                bo = False
                        if bo:
                            totcharge += rch * ndxlth
                            subcharp.append([ndx,rch])
                            break
            else:
                ndx_1 = self.symmetry_list[ self.prolist.offset_1_ndx ]
                if isinstance(ndx_1,int):
                    ndxlth_1 = 1
                    j = ndx_1
                else:
                    ndxlth_1 = len(ndx_1)
                    ix = random.randrange(ndxlth_1)
                    j = ndx_1[ix]

                chmin_1 = int( self.charge_list[j][0] * multibase )
                chmax_1 = int( self.charge_list[j][1] * multibase )

                ndx_0 = self.symmetry_list[ self.prolist.offset_0_ndx ]
                if isinstance(ndx_0,int):
                    ndxlth_0 = 1
                    j = ndx_0
                else:
                    ndxlth_0 = len(ndx_0)
                    ix = random.randrange(ndxlth_0)
                    j = ndx_0[ix]

                chmin_0 = self.charge_list[j][0]
                chmax_0 = self.charge_list[j][1]

                subcharsum = 0.0
                bool_charge_index = True
                offset_totcharge = totcharge
                for dump in range(self.offset_nm):
                    while True:
                        genrch = random.randrange(chmin_1,chmax_1)
                        genrch = round(float(genrch)/multibase,calc_nmround)
                        # apply self.bool_nozero & self.pn_limit
                        bo = True
                        if self.bool_nozero and genrch == 0: bo = False
                        if bo and ndx in pnlist:
                            t = vulist[pnlist.index(ndx)]
                            if ( t == 'p' and genrch <= 0 ) or ( t == 'n' and genrch >= 0 ):
                                bo = False
                        if bo:
                            break

                    subcharsum += genrch
                    offset_totcharge += genrch * ndxlth_1

                    rch = ( calc_total_charge - offset_totcharge ) / ndxlth_0
                    rch = round(rch,calc_nmround)
                    offset_totcharge += rch * ndxlth_0

                    # apply self.bool_nozero & self.pn_limit
                    bo = True
                    if rch < chmin_0 or rch > chmax_0: bo = False
                    if round(calc_total_charge - offset_totcharge,calc_nmround+2) != 0: bo = False
                    if bo and self.bool_nozero and rch == 0: bo = False
                    if bo and ndx_0 in pnlist:
                        t = vulist[pnlist.index(ndx_0)]
                        if ( t == 'p' and rch <= 0 ) or ( t == 'n' and rch >= 0 ):
                            bo = False
                    if bo:
                        bool_charge_index = False
                        break

                if bool_charge_index:
                    genrch = round(subcharsum/self.offset_nm,calc_nmround)

                    rch = calc_total_charge - totcharge - ( genrch * ndxlth_1 )
                    rch = round(rch / ndxlth_0,calc_nmround)

                # append ndx_1 and ndx_0 and their corresponding values
                subcharp.append([ndx_1, genrch])
                subcharp.append([ndx_0, rch])

                # update totcharge
                totcharge += genrch*ndxlth_1 + rch*ndxlth_0

            while round(totcharge - calc_total_charge, calc_nmround + 2) != 0:
                # randomly choose a chargepair but not the counter-pair-charge nor pnlist
                while True:
                    j = random.randrange(len(copysymmetry))
                    offsetndx = copysymmetry[j]
                    if offsetndx not in pnlist:
                        offset_lth = 1 if isinstance(offsetndx,int) else len(offsetndx)
                        break

                cnt = 0
                while cnt < len(subcharp):
                    if subcharp[cnt][0] == offsetndx: break
                    cnt += 1

                chartmp = ( calc_total_charge - totcharge ) / offset_lth
                chartmp = round(chartmp,calc_nmround)
                subcharp[cnt][1]  = round(chartmp+subcharp[cnt][1],calc_nmround)

                totcharge += chartmp * offset_lth


            # adjust subcharp list to correspond to symmetry_list
            pair = []
            for i in self.symmetry_list:
                for j in subcharp:
                    if ( isinstance(i,int) and isinstance(j[0],int) and i == j[0] ) or \
                        ( isinstance(i,list) and isinstance(j[0],list) and i == j[0] ):
                        pair.append(j[1])
                        break

            # now, it comes to most annoying and time-consuming part
            # again take care of self.threshold & self.pn_limit & self.bool_nozero
            # Caution: the indices in self.reflist has to be ruled first
            # the purpose is to squeeze generated values below self.threshold
            ndxreflist = [i[0] for i in self.reflist] + [i[2] for i in self.reflist]
            lglist = [1 if isinstance(i,int) else len(i) for i in self.symmetry_list]
            ndxpnlist = [i[0] for i in self.pn_limit]
            step = 1.0 / ( 10 ** calc_nmround )
            bignm = max(int( self.threshold / step ), 5)
            # in case of infinite loop, try certain times
            boall = True
            for dump in range(100):
                for rt,rch in enumerate(pair):
                    if ( rt not in ndxreflist) and ( abs(rch) > self.threshold ):
                        boall = False
                        break
                if boall: break

                # oppenent but not itself
                while True:
                    pt = random.randrange(len(pair))
                    if ( pt not in ndxreflist ) and ( pt != rt ): break

                ndx = lglist[rt]
                ndy = lglist[pt]
                pch = pair[pt]

                # calculate least common multiple
                if ndx < ndy: a, b = ndy, ndx
                else:   a, b = ndx, ndy
                v = a % b
                while v != 0:
                    a = b
                    b = v
                    v = a % b
                s = ndx * ndy // b

                dt = random.randrange(1,bignm)
                if rch > 0:
                    tmp_rch = round(rch - dt * s / ndx * step, calc_nmround)
                    tmp_pch = round(pch + dt * s / ndy * step, calc_nmround)
                    # again self.bool_nozero
                    if self.bool_nozero and ( tmp_rch == 0 or tmp_pch == 0 ):
                        tmp_rch = round(rch - (dt-1) * s / ndx * step, calc_nmround)
                        tmp_pch = round(pch + (dt-1) * s / ndy * step, calc_nmround)
                else:
                    tmp_rch = round(rch + dt * s / ndx * step, calc_nmround)
                    tmp_pch = round(pch - dt * s / ndy * step, calc_nmround)
                    # again self.bool_nozero
                    if self.bool_nozero and ( tmp_rch == 0 or tmp_pch == 0 ):
                        tmp_rch = round(rch + (dt+1) * s / ndx * step, calc_nmround)
                        tmp_pch = round(pch - (dt+1) * s / ndy * step, calc_nmround)
                # take care of overflow for self.pn_limit
                bosub = True
                if rt in ndxpnlist:
                    rndx = ndxpnlist.index(rt)
                    if ( vulist[rndx] == 'p' and tmp_rch < 0 ) or ( vulist[rndx] == 'n' and tmp_rch > 0 ): bosub = False
                if bosub and ( pt in ndxpnlist ):
                    pndx = ndxpnlist.index(pt)
                    if ( vulist[pndx] == 'p' and tmp_pch < 0 ) or ( vulist[pndx] == 'n' and tmp_pch > 0 ): bosub = False
                if bosub:
                    pair[rt] = tmp_rch
                    pair[pt] = tmp_pch
                    boall = True

                # if errors happen, start from the beginning
                if not boall: continue


            if self.bool_neutral:
                pair = [round(i*self.total_charge,self.nmround) for i in pair]

            # self inspection
            if not self.func_bool_repeats(self.chargepair,pair):
                # filter inspection
                if not self.func_bool_repeats(filterlist,pair):
                    self.chargepair.append(pair)


    def func_bool_repeats(self,reflist,complist):
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

            if len(self.symmetry_list) != 0:
                f.write('# The symmetry_list used is:\n')
                f.write('#    {:s}\n\n'.format(self.prolist.file_line_symmetry))
                if len(self.prolist.offset_list) != 0:
                    f.write('# The offset_list used is:\n')
                    f.write('#    {:s}\n\n'.format(self.prolist.file_line_offset))

            if len(self.reflist) != 0:
                f.write('# The counter_list used is:\n')
                f.write('#   {:s}\n\n'.format(self.prolist.file_line_counter))

            if len(self.pn_limit) != 0:
                tmp = [str(i[0]+1) + i[1] for i in self.pn_limit]
                f.write('# The pn_limit used is:\n')
                f.write('#   {:s}\n\n'.format(str(tmp)))

            f.write('# The total_charge is: < {:} >\n'.format(self.total_charge))
            f.write('# The bool_neutral is: < {:s} >\n'.format('ON' if self.bool_neutral else 'OFF'))
            f.write('# The bool_nozero is: < {:s} >\n\n'.format('ON' if self.bool_nozero else 'OFF'))

            if self.charge_path is None:
                f.write('# The used charge_range file is NotDefined\n')
            else:
                f.write('# The used charge_range file is: < {:s} >\n'.format(self.charge_path))
            f.write('# For each entry, the charge_range is:\n')
            j = 1
            for i in self.charge_list:
                f.write('#ATOM  {:>4}    {:>6}   {:>6}\n'.format(j,i[0],i[1]))
                j += 1

            f.write('\n\n# The randomly generated charges are: \n\n')

            for i in self.chargepair:
                f.write('PAIR ')
                for j in i:
                    f.write('{:>7.3}'.format(j))
                f.write('\n')
            f.write('\n\n')


