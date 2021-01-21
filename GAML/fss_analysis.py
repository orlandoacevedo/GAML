from GAML.functions import file_size_check, file_gen_new, func_file_input
from GAML.function_gen_range import func_gen_range
import matplotlib.pyplot as plt


class FSS_analysis(object):
    def __init__(self,**kwargs):
        if 'file_path' in kwargs and kwargs['file_path'] is not None:
            self.filepath = kwargs['file_path'].strip()
            file_size_check(self.filepath,fsize=200)
        else:
            raise ValueError('no inputs')

        if 'stepsize' in kwargs and kwargs['stepsize'] is not None:
            try:
                self.stepsize = float(kwargs['stepsize'])
                if self.stepsize <= 0:
                    raise ValueError
            except ValueError:
                print('stepsize has to be a positive number')
                raise ValueError('wrong defined')
        else:
            self.stepsize = 0.01

        if 'percent' in kwargs and kwargs['percent'] is not None:
            try:
                self.percent = float(kwargs['percent'])
                if self.percent <= 0 or self.percent > 1:
                    raise ValueError
            except ValueError:
                print('percent has to be a number within the range 0 to 1')
                raise ValueError('wrong defined')
        else:
            self.percent = 0.95

        if 'error_tolerance' in kwargs and kwargs['error_tolerance'] is not None:
            try:
                self.error_tolerance = float(kwargs['error_tolerance'])
            except ValueError:
                print('error_tolerance has to be a number')
                raise ValueError('wrong defined')
        else:
            self.error_tolerance = 0.28

        if 'bool_abscomp' in kwargs:
            self.bool_abscomp = False if kwargs['bool_abscomp'] is False else True
        else:
            self.bool_abscomp = True

        if 'cut_keyword' in kwargs and kwargs['cut_keyword'] is not None:
            self.cut_keyword = kwargs['cut_keyword'].strip()
            if len(self.cut_keyword) == 0: self.cut_keyword = 'MAE'
        else:
            self.cut_keyword = 'MAE'

        if 'pallette_nm' in kwargs and kwargs['pallette_nm'] is not None:
            try:
                self.pallette_nm = int(kwargs['pallette_nm'])
                if self.pallette_nm <= 0:
                    raise ValueError
            except ValueError:
                print('pallette_nm has to be a positive integer')
                raise ValueError('wrong defined')
        else:
            self.pallette_nm = 50

        if 'atomtype_list' in kwargs and kwargs['atomtype_list'] is not None:
            if isinstance(kwargs['atomtype_list'],list):
                if len(kwargs['atomtype_list']) == 0:
                    self.atomtype_list = None
                else:
                    self.atomtype_list = kwargs['atomtype_list']
            else:
                print('atomtype_list has to be a list')
                raise ValueError('wrong defined')
        else:
            self.atomtype_list = None

        if 'fname' in kwargs and kwargs['fname'] is not None:
            self.fname = kwargs['fname'].strip()
            if len(self.fname) == 0: self.fname = 'FSS_analysis'
        else:
            self.fname = 'FSS_analysis'

        if 'color_map' in kwargs and kwargs['color_map'] is not None:
            self.color_map = kwargs['color_map']
        else:
            self.color_map = 'rainbow'



    def func_fss(self):
        """Feature Statistic Selection"""
        chargehvap = func_file_input(self.filepath,bool_tail=True,
                                     cut_keyword=self.cut_keyword,
                                     bool_force_cut_kw=True)

        # filter the list using the error_tolerance
        prolist = []
        for i in range(len(chargehvap)):
            if self.bool_abscomp:
                if abs(chargehvap[i][-1]) <= self.error_tolerance:
                    prolist.append(chargehvap[i])
            else:
                if chargehvap[i][-1] <= self.error_tolerance:
                    prolist.append(chargehvap[i])


        if len(prolist) == 0:
            print('error_tolerance is too small, all the data is filtered out')
            print('please increase this number and try again')
            raise ValueError('wrong inputs')
        elif len(prolist) < 50:
            print('Total number of chosen pairs should be no less than 50')
            print('please increase the error_tolerance and try again')
            raise ValueError('too less')
        else:
            if self.atomtype_list is not None:
                for i in prolist:
                    if len(i) - 1 != len(self.atomtype_list):
                        print(i,'\n',self.atomtype_list)
                        print('input file and atomtype_list')
                        raise ValueError('not correspond')


        valuelist = []
        lth = len(prolist[0]) - 1
        for i in range(lth):
            ls = [per[i] for per in prolist]
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

            a, b = func_gen_range(lp,percent=self.percent)
            v1 = round(chmin + self.stepsize * a, 5)
            v2 = round(chmin + self.stepsize * b, 5)
            valuelist.append([v1,v2])


        # process the prolist again to fulfill the percent setting
        newlist = []
        for chargepair in prolist:
            bo = True
            for i, per in enumerate(chargepair[:-1]):
                if per >= valuelist[i][1] or per < valuelist[i][0]:
                    bo = False
                    break
            if bo:
                newlist.append(chargepair)


        if len(newlist) <= 50:
            info = 'percent is too small to maintain the data sets\n'
            info += 'please add more data entries or increase error_tolerance\n'
            info += 'total number of chosen pairs should be no less than 50'
            print(info)
            raise ValueError('not enough')

        # prompt the information
        self.pnm = len(newlist)
        print('\nThe selected number of charge pair is:    ',self.pnm)
        print('Do you want to continue? y/yes, else quit:    ',end='')
        tmp = input()
        if tmp.upper() != 'Y' and tmp.upper() != 'YES':
            info = 'Warning: you have decided to quit ...\n'
            info += 'Warning: nothing is generated'
            print(info)
            raise RuntimeError('user decided quit')
        else:
            print('\nProcessing ...\n')


        stderrlist = []
        plotlist = []
        valuerangelist = []
        lth = len(newlist[0]) - 1
        for i in range(lth):
            ls = [per[i] for per in newlist]
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
                for perdata in ls: total += (perdata - aver) ** 2
                total = total / delta / delta
                stderrlist.append(total)

        return stderrlist,plotlist,valuerangelist



    def run(self):

        stderrlist,plotlist,self.valuerangelist = self.func_fss()
        if self.atomtype_list is None:
            self.atomtype_list = [ str(i+1) for i in range(len(plotlist)) ]

        # normaliz plotlist to range [0,1]
        self.prolist = []
        for i in plotlist:
            rmax = max(i)
            ls = [j/rmax for j in i]
            self.prolist.append(ls)

        # prepare the y_ticks for the plot
        self.yticklist = []
        for cnt, i in enumerate(self.valuerangelist):
            tmp = '  {:>6.3f} ~ {:>6.3f}'.format(i[0],i[1])
            self.yticklist.append(self.atomtype_list[cnt] + tmp)

        # prepare for fss
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
            line += ' {:>6}'.format(i)
        line = '#' + line[1:]
        self.profile.append(line)

        for i in range(self.pallette_nm):
            line = ''
            for j in plotlist: line +=  ' {:>6}'.format(j[i])
            self.profile.append(line)



    def file_print(self):
        """write to file"""
        self.figure_plot()

        pfname = file_gen_new(self.fname,fextend='txt',foriginal=False)
        print('Note: new file < {:} >'.format(pfname))
        with open(pfname,mode='wt') as f:
            f.write('# Final calculation result (not normalized)\n\n')
            f.write('# input file: < {:} >\n'.format(self.filepath))

            f.write('# error_tolerance: < {:} >\n'.format(self.error_tolerance))
            f.write('# percent_range: < {:} >\n'.format(self.percent))
            f.write('# stepsize: < {:} >\n'.format(self.stepsize))
            f.write('# pallette_number: < {:} >\n\n\n'.format(self.pallette_nm))

            f.write('# Column corresponds to its own data range (optimized)\n')
            f.write('# For each different atomtype, charge range is:\n')

            for i, j in enumerate(self.valuerangelist):
                f.write('#    {:}'.format(self.atomtype_list[i]))
                f.write('    {:>8.3f}  {:>8.3f}\n'.format(j[0],j[1]))

            f.write('\n\n')
            f.write('# Feature Statistical Standard Error Selection\n')
            f.write('# the most influenced atomtype sequence is:\n')
            f.write('#')
            for i in self.ndxlist:
                f.write('  {:}  '.format(self.atomtype_list[i]))
            f.write('\n\n\n')


            f.write('# Number of selection is: < {:} >\n'.format(self.pnm))
            f.write('# Dataset is:\n')
            for line in self.profile:
                f.write(line)
                f.write('\n')



    def figure_plot(self):
        """matplotlib"""
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
        print('Note: Figure name < {:}.png >'.format(pfname))



