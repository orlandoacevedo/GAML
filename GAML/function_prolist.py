class Pro_list(object):
    """
    This class is used to process symmetry_list and counter_list, the symmetry_list is a 2D integer
    list, while the counter_list either can be a 2D integer list or a 1D integer list. One of them
    must be provided. If symmetry_list is provided, its indices should correspond to the atoms'
    sequences, besides, the chemical equivalent information should also be provided. The parameter
    offset_list is meaningful only as the symmetry_list is defined. It is a 1D integer list, no more
    than two number can be used, the first one is used as the strong offset, the second one (if exist)
    is used as the weaker offset. They should correspond to the indices in the symmetry_list, and
    be unique and exclusive. For parameter counter_list, it is used to tell the information about
    which pairs should be couterpart. Its indices should correspond to the symmetry_list or the
    index of charge list. If symmetry_list is defined, it either can be a 2D nested or 1D integer
    list. If not, it only can be a 2D nested integer list.

    For example, ethanol, we have CH3CH2OH, if we sequenced number the atoms, then we will get,

    symmetry_list = [1,[2,3,4],5,[6,7],8,9]

    Then we define the corresponded charge indices;
 
    charge_input = [-0.18,0.06,0.145,0.06,-0.683,0.418]


    Then the offset_list can be defined as;

    offset_list = [8,5]

    OR

    offset_list = [8,]
 
    The offset_list is used to apply the charge constrain.
 
   

    Then the counter_list has two types definitions;

    counter_list = [[1,2]] or [1,2], [first_atom,second_atom]

    OR

    counter_list = [[1,1,2,3]], or,[1,1,2,3], [first_atom,first_nm,second_atom,second_nm]

    If it has multiple counter pairs, only 2D nested list is valid, like [[1,2],[5,6]] or
    [[1,1,2,3],[5,1,6,2]] or [[1,2],[5,1,6,2]]
    """


    def __init__(self,symmetry_list=None,counter_list=None,offset_list=None):
        """The final initiated parameters;
           Note: for any non-exist parameter, the length of return value is always zero

           For symmetry_list;
               self.symmetry_list, [self.symmetry_length], [self.file_line_symmetry], [self.bool_offset]
               
               For offset_list;
                   self.file_line_offset
                   self.offset_list, self.offset_ndx_list, self.bool_offset_0, self.offset_0_ndx,
                   self.bool_offset_1, self.offset_1_ndx
                   

           For counter_list;
               self.reflist, [self.file_line_counter]"""

        if symmetry_list is None:
            pass
        elif not isinstance(symmetry_list,list):
            print('Error: symmetry_list has to be a list')
            exit()
        elif len(symmetry_list) == 0:
            symmetry_list = None

        if counter_list is None:
            pass
        elif not isinstance(counter_list,list):
            print('Error: the counter_list has to be a list')
            exit()
        elif len(counter_list) == 0:
            counter_list = None

        if (symmetry_list is None) and (counter_list is None):
            print('Error: at least one of symmetry_list and counter_list has to be provided')
            exit()
        
        if symmetry_list is None:
            self.symmetry_list = []
            self.offset_list = []
            pro_reflist = self._f_pro_counter_list(counter_list)
        else:
            self.symmetry_list,self.offset_list = self._f_pro_symmetry_list(symmetry_list,offset_list)
            if counter_list is None:
                pro_reflist = []
            else:
                pro_counter_list = self._f_pro_counter_list(counter_list)
                pro_reflist = self._f_pro_symmetry_counter_list(self.symmetry_list,pro_counter_list)                               


        self.reflist = []
        if len(pro_reflist) != 0:
            for i in pro_reflist:
                if i[1] is None:
                    i[1] = 1
                if i[3] is None:
                    i[3] = 1

                #if max(i[1],i[3]) % min(i[1],i[3]) != 0:
                #   print('Error: the parameters in counter_list have to be divided evenly')
                #   exit()
                self.reflist.append(i)

            # check the confliction between self.offset and self.reflist
            # by default, self.offset_list is always a list type
            for i in self.offset_list:
                for j in self.reflist:
                    if i in (j[0],j[2]):
                        print('Error: the offset_list is in conflict with counter_list')
                        exit()  
        
            

    def _f_pro_symmetry_list(self,symmetry_list,offset_list=None):
        """For this method, the final processed parameters are, pro_symmetry_list, pro_offset,
           self.bool_offset, self.bool_offset_0, self.bool_offset_1, self.file_line_symmetry,
           self.file_line_offset"""

        self.bool_offset = False
        self.file_line_offset = ''
        if offset_list is not None:
            self.bool_offset = True
            if isinstance(offset_list,list):
                if len(offset_list) == 0:
                    self.bool_offset = False
                elif len(offset_list) == 1 and isinstance(offset_list[0],int):
                    self.file_line_offset += str(offset_list[0])
                elif len(offset_list) == 2 and isinstance(offset_list[0],int) and \
                     isinstance(offset_list[1],int) and offset_list[0] != offset_list[1]:
                    self.file_line_offset += str(offset_list[0]) + '  ' + str(offset_list[1])
                else:
                    print('Error: offset_list has to be a 1D integer list')
                    print('       the maximum number of its parameters is 2')
                    exit()
            else:
                print('Error: offset_list has to be a list')
                exit()
                
        rmax = 0
        lth = 0
        count = 0
        bool_unique = False
        self.bool_offset_0 = False
        self.bool_offset_1 = False
        self.offset_0_ndx = 0
        self.offset_1_ndx = 0
        self.offset_ndx_list = []
        self.file_line_symmetry = '[ '
        pro_symmetry_list = []
        pro_1D = []
        for i in symmetry_list:
            if isinstance(i,int):
                if rmax == i:
                    bool_unique = True
                rmax = max(rmax,i)
                lth += 1
                pro_symmetry_list.append(i-1)
                pro_1D.append(i)
                self.file_line_symmetry += str(i) + ' '
                if self.bool_offset:
                    if len(offset_list) == 1:
                        if offset_list[0] == i:
                            self.offset_0_ndx = count
                            self.offset_ndx_list.append(count)
                    else:
                        if offset_list[0] == i:
                            self.offset_0_ndx = count
                            self.offset_ndx_list.insert(0,count)
                        elif offset_list[1] == i:
                            self.offset_1_ndx = count
                            self.offset_ndx_list.append(count)
            elif isinstance(i,list):
                ls = []
                self.file_line_symmetry += '['
                for j in i:
                    if isinstance(j,int):
                        ls.append(j-1)
                        pro_1D.append(j)
                        self.file_line_symmetry += str(j) + ' '
                        if self.bool_offset:
                            if len(offset_list) == 1:
                                if offset_list[0] == j:
                                    self.bool_offset_0 = True
                                    self.offset_0_ndx = count
                                    self.offset_ndx_list.append(count)
                            else:
                                if offset_list[0] == j:
                                    self.bool_offset_0 = True
                                    self.offset_0_ndx = count
                                    self.offset_ndx_list.insert(0,count)
                                elif offset_list[1] == j:
                                    self.bool_offset_1 = True
                                    self.offset_1_ndx = count
                                    self.offset_ndx_list.append(count)
                    else:                       
                        print('Error: symmetry_list has to be an integer list')
                        exit()
                pro_symmetry_list.append(ls)
                self.file_line_symmetry = self.file_line_symmetry[:-1] + '] '
                if rmax == max(i):
                    bool_unique = True
                rmax = max(rmax,max(i))
                lth += len(set(i))
            else:
                print('Error: symmetry_list has to be correctly defined')
                exit()
            count += 1
        self.file_line_symmetry += ']'


        if bool_unique or (lth != rmax) or (rmax != len(set(pro_1D))):
            print('Error: the indices in symmetry_list has to be unique and correctly defined')
            exit()
        self.symmetry_length = rmax
        
        pro_offset = []
        if self.bool_offset:
            try:               
                if len(offset_list) == 1:
                    ndx = pro_1D.index(offset_list[0])
                    pro_offset.append(offset_list[0]-1)
                else:
                    ndx = pro_1D.index(offset_list[0])
                    ndx = pro_1D.index(offset_list[1])
                    pro_offset.append(offset_list[0]-1)
                    pro_offset.append(offset_list[1]-1)
            except ValueError:
                print('Error: the parameters in offset_list have to be correctly defined')
                exit()

        return pro_symmetry_list,pro_offset
                


    def _f_pro_counter_list(self,counter_list):
        """This function assumed the symmetry_list has been already properly processed,
           the final parameters are, pro_counter_list

           Note the reserved word None is used as the place holder"""

        bool_1D = False
        pro_counter_list = []
        self.file_line_counter = '[ '
        error_info = 'Error: the counter_list has to be correctly defined'
        for i in counter_list:
            if isinstance(i,int):
                bool_1D = True
                self.file_line_counter += str(i) + ' '
            elif isinstance(i,list):
                if bool_1D:
                    print(error_info)
                    exit()

                line = '['
                for j in i:
                    if not isinstance(j,int):
                        print(error_info)
                        exit()
                    line += str(j) + ' '
                self.file_line_counter += line[:-1] + '] '

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
                    print(error_info)
                    exit()
                pro_counter_list.append(ndx)
            else:
                print(error_info)
                exit()
        self.file_line_counter += ']'
                
        if bool_1D:
            if len(counter_list) == 2:
                ndx = [t-1 for t in counter_list]
                ndx.insert(1,None)
                ndx.append(None)
                pro_counter_list.append(ndx)
            elif len(counter_list) == 4:
                ndx = counter_list[:]
                ndx[0] = ndx[0] - 1
                ndx[2] = ndx[2] - 1
                pro_counter_list.append(ndx)
            else:
                print(error_info)
                exit()

        ls = []
        for i in pro_counter_list:
            ls.append(i[0])
            ls.append(i[2])

        if 2*len(pro_counter_list) != len(set(ls)):
            print('Warning: currently, the counter does not support multiple constrains')
            exit()

        return pro_counter_list




    def _f_pro_symmetry_counter_list(self,symmetry_list,counter_list):
        """Just as its name defined, to process the relation between symmetry_list
           and counter_list, the return value is a 2D nested integer list, each
           sub-list contains 4 values, they are value index in symmetry_list;
           [first_index,length_number,second_index,length_number]"""

        def _f_refer_list(complist,v1,v2,v1_nm=None,v2_nm=None):
            reflist = []
            count = 0
            bool_ref = True
            for i in complist:
                if isinstance(i,int):
                    if i == v1:
                        if (v1_nm is not None) and v1_nm != 1:
                            bool_ref = False
                            break
                        else:
                            reflist.insert(0,count)
                            reflist.insert(1,1)
                    elif i == v2:
                        if (v2_nm is not None) and v2_nm != 1:
                            bool_ref = False
                            break
                        else:
                            reflist.append(count)
                            reflist.append(1)
                else:
                    if (v1 in i) and (v2 in i):
                        bool_ref = False
                        break
                    if v1 in i:
                        if (v1_nm is not None) and v1_nm != len(i):
                            bool_ref = False
                            break
                        reflist.insert(0,count)
                        reflist.insert(1,len(i))
                    elif v2 in i:
                        if (v2_nm is not None) and v2_nm != len(i):
                            bool_ref = False
                            break
                        reflist.append(count)
                        reflist.append(len(i))
                count += 1

            if len(reflist) != 4:
                bool_ref = False
                
            return bool_ref,reflist


        pro_ndx_list = []
        for ndx in counter_list:           
            bo,reflist = _f_refer_list(symmetry_list,ndx[0],ndx[2],ndx[1],ndx[3])
            if not bo:
                print('Error: the symmetry_list and counter_list are not corresponded')
                print('       OR, they are not correctly defined')
                exit()
            #if max(reflist[1],reflist[3]) % min(reflist[1],reflist[3]) != 0:
            #   print('Error: the parameters in counter_list have to be divided evenly')
            #   exit()
                
            pro_ndx_list.append(reflist)

        return pro_ndx_list

