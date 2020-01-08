from GAML.functions import file_size_check, file_gen_new, func_file_input
from GAML.function_gen_range import func_gen_range
import matplotlib.pyplot as plt

class FSS_analysis(object):

    def __init__(self,**kwargs):
        self.log = {'nice':True,}

        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.filepath = kwargs['file_path']
            self.log = file_size_check(self.filepath,fsize=200)
            if not self.log['nice']: return
        else:
            self.log['nice'] = False
            self.log['info'] = 'Error: no file inputs'
            return
        

        if 'stepsize' in kwargs and kwargs['stepsize'] is not None:
            try:
                self.stepsize = float(kwargs['stepsize'])
                if self.stepsize <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter stepsize has to be a positive number'
                return
        else:
            self.stepsize = 0.01
            

        if 'percent' in kwargs and kwargs['percent'] is not None:
            try:
                self.percent = float(kwargs['percent'])
                if self.percent <= 0 or self.percent > 1:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter percent has to be a positive number within the range 0 to 1'
                return
        else:
            self.percent = 0.95
            

        if 'error_tolerance' in kwargs and kwargs['error_tolerance'] is not None:
            try:
                self.error_tolerance = float(kwargs['error_tolerance'])
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter error_tolerance has to be a number'
                return
        else:
            self.error_tolerance = 0.28


        if 'bool_abscomp' in kwargs:
            self.bool_abscomp = False if kwargs['bool_abscomp'] is False else True
        else:
            self.bool_abscomp = True
            

        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            self.cut_keyword = kwargs['cut_keyword']
        else:
            self.cut_keyword = 'MAE'

        
        if 'pallette_nm' in kwargs and kwargs['pallette_nm'] is not None:
            try:
                self.pallette_nm = int(kwargs['pallette_nm'])
                if self.pallette_nm <= 0:
                    raise ValueError
            except ValueError:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter pallette_nm has to be a positive integer'
                return
        else:
            self.pallette_nm = 50
            

        if 'atomtype_list' in kwargs and kwargs['atomtype_list'] is not None:
            if isinstance(kwargs['atomtype_list'],list):
                if len(kwargs['atomtype_list']) == 0:
                    self.atomtype_list = None
                else:
                    self.atomtype_list = kwargs['atomtype_list']
            else:
                self.log['nice'] = False
                self.log['info'] = 'Error: the parameter atomtype_list has to be a list'
                return
        else:
            self.atomtype_list = None
            

        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname']
        else:
            self.fname = 'FSS_analysis'
            

        if 'color_map' in kwargs and kwargs['color_map'] is not None:
            self.color_map = kwargs['color_map']
        else:
            self.color_map = 'rainbow'
            

        self._func_ready()
        if not self.log['nice']: return

        

    def func_fss(self):
        
        self.log,chargehvap = func_file_input(self.filepath,bool_tail=True,cut_keyword=self.cut_keyword,
                                              bool_force_cut_kw=True)
        if not self.log['nice']: return [],[],[]
        
        # filter the list using the error_tolerance
        prolist = []
        i = 0
        while i < len(chargehvap):
            if self.bool_abscomp:
                if abs(chargehvap[i][-1]) <= self.error_tolerance:
                    prolist.append(chargehvap[i])
            else:
                if chargehvap[i][-1] <= self.error_tolerance:
                    prolist.append(chargehvap[i])
            i += 1

        if len(prolist) == 0:
            self.log['nice'] = False
            self.log['info'] = 'Error: the error_tolerance is so small that getting rid of all the data\n' + \
                               'Error: please increase this number and try again'
            return [],[],[]
        elif len(prolist) < 50:
            self.log['nice'] = False
            self.log['info'] = 'Error: the total number of chosen pairs should be no less than 50\n' + \
                               'Error: please increase the error_tolerance and try again'
            return [],[],[]
        else:
            if self.atomtype_list is not None and len(prolist[0]) - 1 != len(self.atomtype_list):
                self.log['nice'] = False
                self.log['info'] = 'Error: the input file and atomtype_list are not corresponded'
                return [],[],[]
                

        valuelist = []
        i = 0
        lth = len(prolist[0]) - 1
        while i < lth:

            ls = []
            for perid in prolist:
                ls.append(perid[i])

            chmin = rmin = min(ls)
            rmax = max(ls)

            lp = []
            while rmin <= rmax:    
                count = 0
                for per in ls:
                    if per >= rmin and per < rmin + self.stepsize:
                        count += 1
                lp.append(count)
                rmin += self.stepsize
            
            self.log,atmp,btmp = func_gen_range(lp,percent=self.percent)
            if not self.log['nice']: return [],[],[]

            lt = []
            lt.append( round(chmin + self.stepsize * atmp,5) )
            lt.append( round(chmin + self.stepsize * btmp,5) )
            valuelist.append(lt)
            
            i += 1


        # process the prolist again to filfull the percent_setting
        newlist = []
        for chargepair in prolist:
            data_bool = True
            i = 0 
            for per in chargepair[:-1]:
                if per >= valuelist[i][1] or per < valuelist[i][0]:            
                    data_bool = False
                    break
                i += 1
            if data_bool:
                newlist.append(chargepair)
                
                
        if len(newlist) <= 50:
            self.log['nice'] = False
            self.log['info'] = 'Error: the percent parameter is not big enough to maintain the data sets\n' + \
                               'Error: please add more file contents or increase the error_tolerance\n' + \
                               'Error: the total number of chosen pairs should be no less than 50'
            return [],[],[]


        # prompt the information
        self.select_pairnm = len(newlist)
        print('\nThe selected charge_pair_number is:    ',self.select_pairnm)
        print('Do you want to continue? y/yes, else quit:    ',end='')
        get_input = input()
        if get_input.upper() != 'Y' and get_input.upper() != 'YES':
            self.log['nice'] = False
            self.log['info'] = 'Warning: you have decided to quit ...\n' + \
                               'Warning: nothing is generated\n'
            return [],[],[]
        else:
            print('\nProcessing ...\n')
            
        
        i = 0
        stderrlist = []
        plotlist = []
        valuerangelist = []
        lth = len(newlist[0]) - 1
        while i < lth:

            ls = []
            for per in newlist:
                ls.append(per[i])

            rmin = min(ls)
            rmax = max(ls)
            step = (rmax - rmin) / self.pallette_nm

            valuerangelist.append([rmin,rmax])

            lp = []
            while rmin <= rmax:    
                count = 0
                for per in ls:
                    if per >= rmin and per < rmin + step:
                        count += 1
                lp.append(count)
                rmin += step

            if len(lp) > self.pallette_nm:
                t = lp.pop()
                lp[-1] += t

            # note, the plotlist is not normalized
            
            plotlist.append(lp)
            

            aver = sum(ls) / len(ls)
            delta = max(ls) - min(ls)

            if delta == 0:
                stderrlist.append(0)
            else:
                total = 0
                for perdata in ls:
                    total += (perdata - aver) ** 2
                total = total / delta / delta

                stderrlist.append(total)

            i += 1
            

        return stderrlist,plotlist,valuerangelist



    def _func_ready(self):
             
        stderrlist,plotlist,self.valuerangelist = self.func_fss()
        if not self.log['nice']: return

        if self.atomtype_list is None:
            self.atomtype_list = [ str(i+1) for i in range(len(plotlist)) ]


        # normaliz the plotlist at the range [0,1]
        self.prolist = []
        for i in plotlist:
            rmax = max(i)
            ls = []
            for j in i:
                ls.append(j/rmax)
            self.prolist.append(ls)

            
        # prepare the y_ticks for the plot
        
        self.yticklist = []
        count = 0
        for i in self.valuerangelist:
            tmp = '  {:>6.3f} ~ {:>6.3f}'.format(i[0],i[1])
            self.yticklist.append(self.atomtype_list[count] + tmp)
            count += 1


        # prepare for the fss

        self.ndxlist = []
        reflist = list(range(len(stderrlist)))
        while len(reflist) > 0:
            errormax = max(stderrlist)
            ndx = stderrlist.index(errormax)
            self.ndxlist.append(reflist[ndx])

            reflist.remove(reflist[ndx])
            stderrlist.remove(errormax)


        # prepare the self.profile for print
        # note, here use the original plotlist

        self.profile = []
        line = ''
        for i in self.atomtype_list:
            line += ' {:>6} '.format(i)
        line = '#' + line[1:] + '\n\n'
        self.profile.append(line)
        
        i = 0  
        while i < self.pallette_nm:
            line = ''
            for j in plotlist:
                line +=  ' {:>6} '.format(j[i])
            self.profile.append(line)
            i += 1



    def file_print(self):

        self.figure_plot()
        
        pfname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        
        with open(pfname,mode='wt') as f:
            f.write('# This is the final calculation result, which is not normalized \n\n')
            f.write('# The corresponded parameters are: \n\n')
            f.write('# The input file used is: \n')
            f.write('#     {:s} \n\n'.format(self.filepath))
            
            f.write('# The error_tolerance is: < {} > \n'.format(self.error_tolerance))
            f.write('# The percent_range is: < {} > \n'.format(self.percent))
            f.write('# The stepsize is: < {} > \n'.format(self.stepsize))
            f.write('# The plot pallette_number is: < {} > \n\n\n'.format(self.pallette_nm))
            
            f.write('# Note: each column is corresponded to its own data_range \n')
            f.write('#       and those data_ranges are the final optimal charge_range \n\n')
            f.write('# For each different atomtype, the charge_range is: \n')


            i = 0
            for j in self.valuerangelist:
                f.write('#    {}'.format(self.atomtype_list[i]))
                f.write('    {:>8.3f}  {:>8.3f} \n'.format(j[0],j[1]))
                i += 1

            f.write('\n\n')              
            f.write('# From the Feature Statistical Standard Error Selection,\n')
            f.write('# the most influenced atomtype sequence is: \n')
            f.write('# ')
            for i in self.ndxlist:
                f.write('  {}  '.format(self.atomtype_list[i]))
            f.write('\n\n\n')


            f.write('# In total, the selected_charge_pair_number is: < {} > \n'.format(self.select_pairnm))
            f.write('# the dataset is:\n\n')
            for line in self.profile:
                f.write(line)
                f.write('\n')



    def figure_plot(self):
  
        cmap = plt.get_cmap(self.color_map)
        fig = plt.figure(facecolor='w',figsize=(10,6))
        
        ax = fig.add_subplot(111)
        ax.set_yticks(range(len(self.yticklist)))
        ax.set_yticklabels(self.yticklist)
        ax.get_xaxis().set_visible(False)
        ax.set_title('Error Tolerance: {}, Percent: {}'.format(self.error_tolerance,self.percent))
        
        getcmap = ax.imshow(self.prolist,cmap=cmap,aspect='auto')
        cb = plt.colorbar(mappable=getcmap,shrink=1.0,pad=0.02)
        cb.set_ticks([])

        pfname = file_gen_new(self.fname,fextend='png',foriginal=False)
        pfname = pfname[:pfname.rfind('.png')]
        plt.tight_layout()
        fig.savefig(pfname)


