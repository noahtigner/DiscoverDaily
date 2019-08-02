import sys
import time
import datetime
import json

STYLES = {
    'reset':        '\033[0m',
    'bold':         '\033[01m',
    'disable':      '\033[02m',
    'underline':    '\033[04m',
    'reverse':      '\033[07m',
    'strikethrough':'\033[09m',
    'invisible':    '\033[08m',
}

FOREGROUND = {
    # Low Contrast
    # --------------------------------
    'dim_black':    '\033[30m',
    'dim_red':      '\033[31m',   
    'dim_green':    '\033[32m',   
    'dim_yellow':   '\033[33m',   
    'dim_blue':     '\033[34m',   
    'dim_magenta':  '\033[35m',   
    'dim_cyan':     '\033[36m',   
    'dim_white':    '\033[37m',  
    # High Contrast
    # --------------------------------
    'black':        '\033[90m',
    'red':          '\033[91m',   
    'green':        '\033[92m',   
    'yellow':       '\033[93m',   
    'blue':         '\033[34m',     # HC Blue looks purple, used LC Blue
    'purple':       '\033[94m',     # HC Blue looks purple, used LC Blue
    'magenta':      '\033[95m',   
    'cyan':         '\033[96m',   
    'white':        '\033[97m',
}

BACKGROUND = {
    'black':        '\033[40m',
    'red':          '\033[41m',
    'green':        '\033[42m',
    'orange':       '\033[43m',
    'blue':         '\033[44m',
    'purple':       '\033[45m',
    'cyan':         '\033[46m',
    'lightgrey':    '\033[47m',
}

def my_print(message='', color='green', high_contrast=True, file=None):
    if not high_contrast and 'dim' not in color:
        color = 'dim_' + color
    print(FOREGROUND[color] + str(message) + STYLES['reset'], file=file)

def my_input(prompt, default=None, options=None, color='green', dcolor='green', high_contrast=True):
    if options:
        options = list(options)
        options = FOREGROUND[dcolor] + '[' + str(', '.join(options)) + '] '
    else:
        options = ''

    if default:
        dflt = FOREGROUND[dcolor] + '{' + str(default) + '} '
    else:
        dflt = ''
    
    return input('' + FOREGROUND[color] + str(prompt) + options + dflt + STYLES['reset']) or default

def clear_screen():
    print(chr(27) + '[2J')

class ProgressBar:
    """
    A Progress Bar that is dependant on the progress of a function or process.

    Usage: Create a ProgressBar object
           Before or After each checkpoint, call update with the checkpoint name
    Args: name. steps (nuber of checkpoints), width (amount of '-' characters)
    Returns:
    """
    
    def __init__(self, name='Progress', steps=3, width=48, completion='Complete'):
        self.name = name
        self.steps = steps
        self.width = width
        self.completion = completion
        self.cur_step = 0
        self.last_label = ''

        print('\n' + name)
        print('[' + ' '*self.width + ']', end='\r', flush=True)

    def update(self, step_name, color='yellow'):
        self.cur_step += 1
        self.draw_bar(step_name, color)

        if self.cur_step == self.steps:

            label = self.completion + (' '*(len(self.last_label) - len(self.completion)))
            bar = FOREGROUND[color] + ('-' * self.width) + STYLES['reset']
            line = '[' + bar + '] ' + label

            print(line, end='\r', flush=True)
            print('\n')

    def draw_bar(self, step_name, color):
        width = int((self.width / self.steps) * self.cur_step)
        previous = int(width - (self.width / self.steps))
        width = width - previous

        for i in range(width + 1):
            time.sleep(0.05)

            label = step_name + (' ' * (len(self.last_label) - len(step_name)))
            bar = FOREGROUND[color] + ('-' * (previous + i)) + (' ' * (self.width - (previous + i))) + STYLES['reset']
            line = '[' + bar + '] ' + label
            print(line, end='\r', flush=True)

        self.last_label = step_name

def test_progBar():
    p = ProgressBar('Email', 3, width=64, completion='Email Sent')

    time.sleep(0.5)
    p.update('Connecting to Server')

    time.sleep(0.5)
    p.update('Preparing Message')

    time.sleep(0.5)
    p.update('Sending Email')

class CountDown:
    def __init__(self, seconds=0, minutes=0, hours=0, show_milli=False, message='', completion='None', color='yellow', ccolor='green'):
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.message = message
        self.completion = completion + ' ' * 16
        self.color = color
        self.ccolor = ccolor

        delta = datetime.timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)
        total_seconds = int(delta.total_seconds())


        while total_seconds > 1:
            total_seconds -= 1

            hours, remainder = divmod(total_seconds, 60*60)
            minutes, seconds = divmod(remainder, 60)

            # Looks cool, but milliseconds drift due to OS
            if show_milli:
                milli = 1000

                while milli > 0:
                    milli -= 1
                    t = f'{hours:02}:{minutes:02}:{seconds:02}.{milli:03}'
                    time.sleep(0.0009)
                    print(t, end='\r', flush=True)

            # More reliable
            else:
                t = f'{hours:02}:{minutes:02}:{seconds:02}'
                print(str(self.message) + FOREGROUND[self.color] + ' ' + t + STYLES['reset'], end='\r', flush=True)

                time.sleep(1)
        
        print(FOREGROUND[self.ccolor] + str(self.completion) + STYLES['reset'], flush=True)

# cd = CountDown(5, message='Countdown:', completion='Done')

def print_json(to_print):
    print(json.dumps(to_print, sort_keys=True, indent=4))