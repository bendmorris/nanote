import curses
import settings as settings_module
import re
from __init__ import VERSION


tab_symbols = ['*', 'o', '>', '-', '+']

class Editor:
    def __init__(self, start_note=None, debug=False):
        import settings
        self.settings = settings
        
        self.start_app()
        
        self.cursor = (0,0)
        self.pad_position = (0,0)
        self.status = ''
        self.altered = False
        self.history = [None]
        self.history_position = 0
        self.links = []
        self.cutting = False
        self.cuts = []
        
        self.load_note(start_note)
        self.current_note = start_note if start_note else 'untitled'
        
        if not start_note and debug:
            self.buffer = ['This is a test note.', '', 
                           'You can link to other notes like this: [school:homework].', 
                           'Put the cursor over a link and press ENTER to follow it.',
                           'Surround text in asterisks to *bold it*; underscores _underline text_.',
                           '',
                           'Make *bulleted lists* with indentation and asterisks, like this:',
                           '* one', '    * two', '        * three', '            * four',
                           ]


    def start_app(self):
        # start the application
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)

    def end_app(self):
        # end the application
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()
        
    def draw_screen(self):
        settings = self.settings
        
        self.screen.refresh()
        
        screen_size = self.screen.getmaxyx()
        self.height, self.width = screen_size
        height, width = self.height, self.width
        cy, cx = self.cursor
        py, px = self.pad_position

        self.buffer_pad = curses.newwin(height-4, width, 1, 0)
        #self.buffer_pad = curses.newpad(len(self.buffer) + height + 1, 
        #                                max([len(line) for line in self.buffer] + [width]))
        self.title_win = curses.newwin(1, width, 0, 0)
        self.shortcut_win = curses.newwin(3, width, height-3, 0)

        columns = int((len(settings.shortcuts)+.5)/2)
        column_width = width / (columns + 1)
        for n, shortcut in enumerate(settings.shortcuts):
            x = (n/2) * column_width
            y = 1 if not n%2 else 2
            self.shortcut_win.addstr(y, x, '^' + shortcut[0], curses.A_REVERSE)
            self.shortcut_win.addstr(' ' + shortcut[1])
        
        if self.status: status_text = self.status
        else: status_text = '"%s"  line %s/%s, col %s/%s' % (self.current_note, cy+1, len(self.buffer) + 1, 
                                                             cx+1, len(self.buffer[cy]) if cy < len(self.buffer) else 0)
        
        total_gap = width - len(status_text) - 1
        left_gap = total_gap/2
        right_gap = total_gap-left_gap
        self.shortcut_win.addstr(0, 0, ' '*(left_gap) + status_text + ' '*(right_gap), curses.A_REVERSE)
        self.status = ''
            
        self.shortcut_win.noutrefresh()

        note_name = self.current_note if self.current_note else 'untitled'
        title_text = '  nanote %s' % (VERSION)
        total_gap = width - len(title_text) - len(str(note_name)) - 1
        left_gap = total_gap/2
        right_gap = total_gap-left_gap
        self.title_win.addstr(title_text + ' '*left_gap + str(note_name) + ' '*right_gap, curses.A_REVERSE)
        self.title_win.noutrefresh()

        onscreen_range = range(py, 
                               min(py + height-3 + 1, len(self.buffer) - 1)+1)

        for n, i in enumerate(onscreen_range):
            try: self.buffer_pad.addstr(n, 0, self.buffer[i][:width-1])
            except: pass
        self.links = []
        link_re = re.compile("\[[a-zA-Z\_\-\.\:]+\]")
        bold_re = re.compile("\*[^ ^\[^\]^*^_][^\[^\]^*^_]*?\*")
        underline_re = re.compile("\_[^ ^\[^\]^*^_][^\[^\]^*^_]*?\_")
        bullet_re = re.compile('^ *\* .*')
        for n, i in enumerate(onscreen_range):
            for m in link_re.finditer(self.buffer[i]):
                pos = m.start(); text = m.group()
                try: self.buffer_pad.addstr(n, pos, text, curses.A_REVERSE)
                except: pass
                if i == cy: self.links.append((pos, text))
            for m in bold_re.finditer(self.buffer[i]):
                pos = m.start(); text = m.group()
                try: self.buffer_pad.addstr(n, pos+1, text[1:-1], curses.A_BOLD)
                except: pass
            for m in underline_re.finditer(self.buffer[i]):
                pos = m.start(); text = m.group()
                try: self.buffer_pad.addstr(n, pos+1, text[1:-1], curses.A_UNDERLINE)
                except: pass
            for m in bullet_re.finditer(self.buffer[i]):
                pos = m.start(); text = m.group()
                stripped_text = text.lstrip(' ')
                indentation = len(text)-len(stripped_text)
                indent_level = (indentation / settings.args['tab_width']) % len(tab_symbols)
                try: self.buffer_pad.addstr(n, pos + indentation, tab_symbols[indent_level], curses.A_BOLD)
                except: pass

        #self.buffer_pad.refresh(py, 0, 1, 0, height-4, width)
        self.buffer_pad.noutrefresh()

        self.screen.move(cy+1-py, cx)
        self.screen.noutrefresh()
        
        curses.doupdate()

        
    def dialog(self, prompt, default_text='', yesno=False):
        running = True
        entered_text = default_text
        
        while running:
            try:
                self.draw_screen()
                
                total_gap = self.width - len(prompt) - 3 - len(entered_text)
                self.shortcut_win.addstr(0, 0, ' %s %s%s' % (prompt, entered_text, ' '*total_gap), curses.A_REVERSE)
                self.screen.move(self.height-3, len(prompt) + 2 + len(entered_text))
                self.shortcut_win.refresh()
                
                c = self.screen.getch()
                
                if yesno:
                    if c in (ord('y'), ord('Y')):
                        return True
                    elif c in (ord('n'), ord('N')):
                        return False
                    
                else:
                    if c == curses.KEY_BACKSPACE:
                        entered_text = entered_text[:-1]
                    elif c == ord('\n'):
                        return entered_text
                    elif 0 < c < 255:
                        if len(entered_text) < 100:
                            entered_text += chr(c)
                
            except KeyboardInterrupt:
                return None

    
    def correct_cursor(self, cy, cx):
        buffer = self.buffer
        py, px = self.pad_position
        if cy < 0: 
            # up too far; move to top
            cy = 0; cx = 0
        if cy >= len(buffer): 
            # down too far; move to bottom
            cy = len(buffer)
        if cx < 0:
            # left too far; move up and to the end of the previous line
            return self.correct_cursor(cy-1, len(buffer[cy-1]))
        if (cy < len(buffer)) and (cx > len(buffer[cy])): 
            # right too far; move down and to the beginning of the next line
            return self.correct_cursor(cy+1, 0)
        if (cy >= len(buffer)) and cx > 0:
            cy = len(buffer); cx = 0

        while cy < py: py -= 1
        while cy > py + self.height-5: py += 1
        #while cx < px: px -= 1
        while cx > self.width-1: cx -= 1
        self.cursor = (cy, cx)
        self.pad_position = (py, px)
        
    def load_note(self, note_name, title=None, going_back = False):
        settings = self.settings
        if not title: 
            title = note_name if note_name else 'untitled'
        
        if self.altered:
            response = self.dialog('Save changes to old note? (Y or N, ^C to cancel)', yesno=True)
            if response is None: return
            self.altered = False
            if response:
                self.save_note(self.current_note)
        try:
            if not note_name:
                self.buffer = []
            else:
                note_path = settings.find_note(note_name)
                with open(note_path) as note_file:
                    self.buffer = [r.rstrip('\n') for r in note_file.readlines()]    
            if not going_back and not (self.history_position == len(self.history)-1 and self.history[-1] == note_name):
                if note_name in self.history: 
                    self.history.remove(note_name)
                    self.history_position -= 1
                self.history = self.history[:self.history_position+1] + [note_name]
                self.history_position = len(self.history) - 1
        except: 
            self.buffer = []
            self.status = "new note: %s" % note_name
            return self.load_note(None, title=title, going_back=going_back)
            
        self.current_note = title
        self.cursor = (0,0)
        self.altered = False
        
    def save_note(self, note_name):
        settings = self.settings
        
        if note_name == 'untitled': note_name = ''
        
        note_name = self.dialog('Enter the name of the note to save (^C to cancel):', note_name)
        if not note_name: return
        
        note_path = settings.find_note(note_name)
        if not note_path: note_path = settings.default_note_path(note_name)
        directory = '/'.join(note_path.split('/')[:-1])
        settings.make_dir_if_not_exists(directory)
        with open(note_path, 'w') as note_file:
            note_file.write('\n'.join(self.buffer))
        self.status = 'Saved note "%s" to %s' % (note_name, note_path)
        self.altered = False
        self.current_note = note_name
        self.history[self.history_position] = note_name
        
        if note_name == '**settings**':
            self.settings = reload(settings)
        
    def forward(self):
        if self.history_position < len(self.history)-1:
            self.history_position += 1
            self.load_note(self.history[self.history_position], going_back=True)
    
    def back(self):
        if self.history_position > 0:
            self.history_position -= 1
            self.load_note(self.history[self.history_position], going_back=True)
