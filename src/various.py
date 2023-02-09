import math
import time


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProgressBar:

    def __init__(self, title, pct_interval=1) -> None:
        self.title = title
        self.pct_interval = pct_interval
        self.prog_bar_char_width = 100
        self.additional_info = ''
        self.disabled = False

    def progress(self, pct):
        if not self.disabled:
            if type(pct) == float:
                pct = math.floor(pct)
            if pct > self.prog_bar_char_width:
                pct = self.prog_bar_char_width - 1

            if pct < self.prog_bar_char_width - 1:
                output = (
                    f"\r[{colors.OKGREEN}{'━'*(pct+1)}{colors.ENDC}{colors.FAIL}"
                    f"{'━'*(self.prog_bar_char_width-(pct+1))}{colors.ENDC}] {pct+1}% {f'{self.additional_info}' if self.additional_info else ''}"
                )
                print(output, end='')

            if pct >= self.prog_bar_char_width - 1:
                output = f"\r{colors.OKGREEN}{self.title}{colors.ENDC} complete.{' '*(130+len(self.title))}\n"
                print(output, end='')
                self.disabled = True

    def exit(self):
        self.progress(100)


class ModelProgressBar:

    def __init__(self, title, pct_interval=1) -> None:
        self.title = title
        self.pct_interval = pct_interval
        self.prog_bar_char_width = 100
        self.additional_info = ''
        self.disabled = False
        self.ts_1 = None
        self.ts_2 = None
        self.time_in_seconds = 0
        self.measured_cycles = 0
        self.cycles_per_second = ''

    def progress(self, pct, additional_info=None, measure_gap=0.01):
        # print(pct%measure_gap)
        self.measured_cycles += 1
        if pct%measure_gap == 0:
            if self.ts_1 is None:
                self.ts_1 = time.time()
            else:
                self.ts_2 = time.time()
                self.time_in_seconds = self.ts_2 - self.ts_1
                self.ts_1 = None
                # print(self.ts_1, self.ts_2)
                # print(self.time_in_seconds, self.measured_cycles)
                self.cycles_per_second = (1/self.time_in_seconds)*self.measured_cycles
                # round it to 3 decimal places
                self.cycles_per_second = round(self.cycles_per_second, 5)

        
        if not self.disabled:
            if type(pct) == float:
                pct = math.floor(pct)
            if pct > self.prog_bar_char_width:
                pct = self.prog_bar_char_width - 1


            additional_info = round(float(additional_info), 5)

            if pct < self.prog_bar_char_width - 1:
                output = (
                    f"\r[{colors.OKGREEN}{'━'*(pct+1)}{colors.ENDC}{colors.FAIL}"
                    f"{'━'*(self.prog_bar_char_width-(pct+1))}{colors.ENDC}] {pct+1}% loss is {f'{additional_info}' if additional_info else ''}, CPS={self.cycles_per_second}"
                )
                print(output, end='')

            if pct >= self.prog_bar_char_width - 1:
                output = f"\r{colors.OKGREEN}{self.title}{colors.ENDC} complete.{' '*(130+len(self.title))}\n"
                print(output, end='')
                self.disabled = True

    def exit(self):
        self.progress(100)