class Prolist():
    """process input symmetry_list & counter_list & offset_list

    Args:
        symmetry_list   :   List[int,[int], ...]
        counter_list    :   List[[int,int]]
        offset_list     :   int or list

    If symmetry_list is provided, its indices should correspond to the atoms
    sequences, besides, the chemical equivalent information should also be
    provided. The parameter offset_list is meaningful only as symmetry_list
    is defined, which should be 1D integer list, contains no more than two
    values; the first one is used as the strong offset, the second one
    (if exist) is used as the weak offset. They should correspond to the
    indices in the symmetry_list, and be unique and exclusive.
    
    For parameter counter_list, it is used to tell the information about
    which pairs should be counterpart. Its indices should correspond to 
    the symmetry_list or the index of charge list.

    Examples:
        Ethanol, CH3CH2OH, sequenced by number the atoms;

        symmetry_list = [1,[2,3,4],5,[6,7],8,9]

        Then we define the corresponded charge indices;

        charge_input = [-0.18,0.06,0.145,0.06,-0.683,0.418]

        Then the offset_list can be defined as;

        offset_list = [8,5]

        OR

        offset_list = [8,]

        Note: offset_list is used to apply the charge constrain.


        Then the counter_list has two types definitions;

         counter_list = [[1,2]] or [1,2], [first_atom,second_atom]

        OR

        counter_list = [[1,1,2,3]] 
        OR
        counter_list = [1,1,2,3] ([first_atom,first_nm,second_atom,second_nm])
    """
    def __init__(self,symmetry_list=None,counter_list=None,offset_list=None):
        """
        Attributes:
            self.symmetry_list
            self.offset_list
            self.offset_ndx_list
            self.counter_list
            self.reflist    :   List[[int,int,int,int], ...]

        Note:
            assume inputs are human readable list, indice starts at 1
            if not exist, empty List will be returned
        """
        self.pro_symmetry_list(symmetry_list,offset_list)

        tmp = self.pro_counter_list(counter_list)

        self.reflist = self.prolist(self.symmetry_list,self.counter_list)

        # restore counter_list
        self.counter_list = [ [i[0]-1, i[1]-1] for i in tmp]

        # check the confliction between self.offset and self.reflist
        # by default, self.offset_list is always a list type
        for i in self.offset_list:
            for j in self.counter_list:
                if i in j:
                    print('offset_list is in conflict with counter_list')
                    raise ValueError('wrong defined')



    def pro_symmetry_list(self,symmetry_list=None,offset_list=None):
        """process symmetry_list
        
        Attributes:
            self.symmetry_list
            self.offset_list
            self.offset_ndx_list
        """
        if symmetry_list is None:
            symmetry_list = []
        elif isinstance(symmetry_list,(list,str)):
            if isinstance(symmetry_list,str):
                symmetry_list = symmetry_list.replace('"','').replace("'",'')
                try:
                    symmetry_list = eval(symmetry_list)
                except:
                    print('symmetry_list has to be an integer list')
                    raise ValueError('wrong defined')
        else:
            print('symmetry_list has to be an integer list')
            raise ValueError('wrong defined')

        if offset_list is None:
            offset_list = []
        else:
            if isinstance(offset_list,(list,str,int)):
                if isinstance(offset_list,(list,str)):
                    if isinstance(offset_list,str):
                        offset_list = offset_list.split()
                        if len(offset_list) == 0:
                            offset_list = []
                        elif len(offset_list) <= 2:
                            tmp = []
                            try:
                                v1 = int(offset_list[0])
                                tmp.append(v1)
                                if len(offset_list) == 2:
                                    v2 = int(offset_list[1])
                                    tmp.append(v2)
                            except ValueError:
                                print(offset_list)
                                raise ValueError('wrong defined')
                            offset_list = tmp
                else:
                    offset_list = [offset_list]
            else:
                print('offset_list has to be a 1D integer list')
                raise ValueError('wrong defined')

        rmax = 0
        lth = 0
        bool_unique = False
        self.offset_ndx_list = []
        self.symmetry_list = []
        flatten = []
        for cnt,i in enumerate(symmetry_list):
            if isinstance(i,int):
                if rmax == i: bool_unique = True
                rmax = max(rmax,i)
                lth += 1
                self.symmetry_list.append(i-1)
                flatten.append(i)
                if len(offset_list) == 1:
                    if offset_list[0] == i:
                        self.offset_ndx_list.append(cnt)
                elif len(offset_list) == 2:
                    if offset_list[0] == i:
                        self.offset_ndx_list.insert(0,cnt)
                    elif offset_list[1] == i:
                        self.offset_ndx_list.append(cnt)
            elif isinstance(i,list):
                ls = []
                for j in i:
                    if isinstance(j,int):
                        ls.append(j-1)
                        flatten.append(j)
                        if len(offset_list) == 1:
                            if offset_list[0] == j:
                                self.offset_ndx_list.append(cnt)
                        elif len(offset_list) == 2:
                            if offset_list[0] == j:
                                self.offset_ndx_list.insert(0,cnt)
                            elif offset_list[1] == j:
                                self.offset_ndx_list.append(cnt)
                    else:
                        print('symmetry_list has to be an integer 2D list')
                        raise ValueError('wrong defined')
                self.symmetry_list.append(ls)
                if rmax == max(i): bool_unique = True
                rmax = max(rmax,max(i))
                lth += len(set(i))
            else:
                print('symmetry_list has to be an integer 2D list')
                raise ValueError('wrong defined')

        self.offset_list = [i-1 for i in offset_list]
        if len(symmetry_list) == 0:
            self.offset_ndx_list = [i for i in self.offset_list]
        else:
            if bool_unique or (lth != rmax) or (rmax != len(set(flatten))):
                print('indices in symmetry_list have to be unique')
                raise ValueError('wrong defined')

            if len(offset_list) != len(self.offset_ndx_list):
                print('symmetry_list and offset_list are not corresponded')
                raise ValueError('not correspond')



    def pro_counter_list(self,counter_list):
        """
        Attributes:
            self.counter_list   :   List[[int,int/None,int,int/None], ...]
        """
        if counter_list is None: counter_list = []
        bo = False
        if isinstance(counter_list,(list,str)):
            if isinstance(counter_list,str):
                counter_list = counter_list.replace('"','').replace("'",'')
                try:
                    counter_list = eval(counter_list)
                except:
                    bo = True
        else:
            bo = True
        if bo:
            print('counter_list has to be correctly defined')
            raise ValueError('wrong defined')

        self.counter_list = []
        for i in counter_list:
            bo = False
            if isinstance(i,list):
                for j in i:
                    if not isinstance(j,int): bo = True
                # make a copy of this sublist to avoid any mistakes
                if len(i) == 2:
                    ndx = [t-1 for t in i]
                    ndx.insert(1,None)
                    ndx.append(None)
                elif len(i) == 4:
                    ndx = i[:]
                    ndx[0] = ndx[0] - 1
                    ndx[2] = ndx[2] - 1
                else:
                    bo = True
                self.counter_list.append(ndx)
            else:
                bo = True
            if bo:
                print('counter_list has to be correctly defined')
                raise ValueError('wrong defined')

        flatten = []
        for i in self.counter_list:
            flatten.append(i[0])
            flatten.append(i[2])
        if 2*len(self.counter_list) != len(set(flatten)):
            print('currently counter_list does not support multiple constrains')
            raise ValueError('wrong defined')

        return counter_list



    def prolist(self,symmetry_list,counter_list):
        """process all input lists"""

        def ratio(complist,v1,v2,v1_nm=None,v2_nm=None):
            reflist = []
            bo = True
            for cnt,i in enumerate(complist):
                if isinstance(i,int):
                    if i == v1:
                        if (v1_nm is not None) and v1_nm != 1:
                            bo = False
                            break
                        else:
                            reflist.insert(0,cnt)
                            reflist.insert(1,1)
                    elif i == v2:
                        if (v2_nm is not None) and v2_nm != 1:
                            bo = False
                            break
                        else:
                            reflist.append(cnt)
                            reflist.append(1)
                else:
                    if (v1 in i) and (v2 in i):
                        bo = False
                        break
                    if v1 in i:
                        if (v1_nm is not None) and v1_nm != len(i):
                            bo = False
                            break
                        reflist.insert(0,cnt)
                        reflist.insert(1,len(i))
                    elif v2 in i:
                        if (v2_nm is not None) and v2_nm != len(i):
                            bo = False
                            break
                        reflist.append(cnt)
                        reflist.append(len(i))

            if len(reflist) != 4: bo = False

            return bo,reflist


        if len(symmetry_list) == 0:
            if len(counter_list) == 0:
                return []
            
            reflist = []
            for i in counter_list:
                i[1] = 1 if i[1] is None else i[1]
                i[3] = 1 if i[3] is None else i[3]
                reflist.append(i)
            return reflist


        reflist = []
        for ndx in counter_list:
            bo,tlist = ratio(symmetry_list,ndx[0],ndx[2],ndx[1],ndx[3])
            if not bo:
                print('symmetry_list and counter_list are not corresponded')
                raise ValueError('not correspond')
            reflist.append(tlist)
        
        return reflist



