#!/usr/bin/env python3

import os
import subprocess
import stat
import sys
from sys import argv
import curses
import platform
import mimetypes

VERSION = "scroll 1.0"

dir_contents = []

cd = os.getenv("PWD")

EDITOR = os.getenv("EDITOR") if os.getenv("EDITOR") else "editor"

MEDIA_OPEN = "open" if platform.system() == "Darwin" else "xdg-open"


# keypresses
OPEN_KEYS = (curses.KEY_ENTER, ord('\n'), curses.KEY_RIGHT, ord('l'))
BACK_KEYS = (curses.KEY_LEFT, ord('h'))
UP_KEYS = (curses.KEY_UP, ord('k'))
DOWN_KEYS = (curses.KEY_DOWN, ord('j'))
TOP_KEYS = (ord('g'),)
BOTTOM_KEYS = (ord('G'),)


# if the current dir is not readable / gives a permission error
perm_error = False

# whether or not to show dotfiles
show_hidden = False

# whether or not to print the path name when scroll exits
print_on_exit = False


class FileType():
    F_UKNWN = 0
    F_DIR = 1
    F_LNK = 2
    F_FIFO = 3
    F_REG = 4

    F_COLORS = {F_UKNWN: 6, F_DIR: 1, F_LNK: 2, F_FIFO: 5}
    F_IDENTS = {F_UKNWN: '?', F_DIR: '/', F_LNK: '@', F_FIFO: '|', F_REG: ''}
    F_MEDIA_EXTS = (
        "jpg", "jpeg", "png", "svg", "m4v", "mp4",
        "mkv", "m4a",  "mp3", "webm"
    )
    F_ARCHIVE_EXTS = (
        "tar", "xz",   "bz2", "gz",  "zip", "rar"
    )
    F_MEDIA_MIMES = ("video", "image")

class FileEntry():
    f_name = ""
    f_type = FileType.F_REG
    f_exec = False

    def __init__(self, de):
        if de == None:
            self.f_name = ".."
            self.f_type = FileType.F_DIR
            return

        self.f_name = de.name

        if not os.access(de, os.F_OK):  self.f_type = FileType.F_UKNWN
        elif de.is_dir():               self.f_type = FileType.F_DIR
        elif de.is_symlink():           self.f_type = FileType.F_LNK
        elif stat.S_ISFIFO(os.stat(de.path).st_mode):
            self.f_type = FileType.F_FIFO
        else:                           self.f_type = FileType.F_REG

        if self.f_type != FileType.F_DIR and os.access(de.path, os.X_OK):
            self.f_exec = True

    def color(self):
        if self.f_type in FileType.F_COLORS:
            return FileType.F_COLORS[self.f_type]
        ext = self.f_name.split('.')
        ext = None if len(ext) == 1 else ext[-1]
        if ext in FileType.F_MEDIA_EXTS:   return 4 # purple
        if ext in FileType.F_ARCHIVE_EXTS: return 6 # red

        if self.f_exec: return 3 # green

        return 7 # regular file -- white

    def ident(self):
        if self.f_type in FileType.F_IDENTS:
            return FileType.F_IDENTS[self.f_type]
        if self.f_exec: return '*'

        return ''


def list_files():
    """
    list all the files in the current dir\n
    listed files will be appended to the dir_contents list/dict\n
    as a FileEntry object
    """
    tmp_contents = {"dirs": [], "files": []}

    global perm_error

    try:
        items = os.scandir(cd)

        perm_error = False

        for item in items:
            # do not append dotfiles to list if show_hidden is false
            if not show_hidden and (item.name[0] == '.'): continue

            i = FileEntry(item)

            if i.f_type == FileType.F_DIR:
                tmp_contents["dirs"].append(i)
            else:
                tmp_contents["files"].append(i)

        tmp_contents["dirs"].sort(key=lambda n:n.f_name)
        tmp_contents["files"].sort(key=lambda n:n.f_name)

        for tmp_dir in tmp_contents["dirs"]:
            dir_contents.append(tmp_dir)

        for tmp_file in tmp_contents["files"]:
            dir_contents.append(tmp_file)
        
    except PermissionError:
        perm_error = True

    if not len(dir_contents):
        i = FileEntry(None)
        dir_contents.append(i)


# cd into .. without uglying the path
def cdback():
    """
    cd into .. without making the path ugly
    """
    global cd
    global dir_contents

    # remove the last segment of the path
    cd = '/'.join(cd.split('/')[:-1])
    if not cd: cd = '/'
    dir_contents = []
    list_files()


def print_file_name(screen, row, item, column=0, highlight=False):
    """
    print a file name based on what kind of file it is\n
    may also print a highlighted or non-highlited file\n
    """

    color = item.color()
    ident = item.ident()

    if item.f_exec:
        ident = '*'

    color = curses.color_pair(color)
    if highlight: color |= curses.A_REVERSE

    screen.addstr(row, column, item.f_name, color)
    screen.addstr(row, len(item.f_name) + column, ident)
 

def file_options(item, screen):
    """
    the options menu for a given file
    """
    curses.curs_set(0)
    curses.start_color()
    screen.keypad(True)

    screen.clear()
    screen.refresh()

    cursor = 0
    
    mime = mimetypes.guess_type(f"{cd}/{item.f_name}")[0]
    if mime: mime = mime.partition('/')[0].lower()

    options = ["View File", "Edit File", "Delete File", "Rename File", "Open File with Command"]
    if mime in FileType.F_MEDIA_MIMES:
        options.remove("Edit File") # cannot edit media files

    while True:
        row = 0
        column = 2
        screen.erase()

        screen.border('|', 1, 1, 1, 1, 1, 1, 1)
        
        print_file_name(screen, row, item, column=column)
        row += 2

        for option in range(len(options)):
            if option == cursor:
                screen.addstr(row, column, options[option],
                        curses.color_pair(7) | curses.A_REVERSE)
            else:
                screen.addstr(row, column, options[option])
            row += 1

        screen.refresh()

        key_pressed = screen.getch()

        # up arrow pressed
        if key_pressed in UP_KEYS:
            if cursor > 0: cursor -= 1

        # down arrow pressed
        elif key_pressed in DOWN_KEYS:
            if cursor < len(options) - 1: cursor += 1

        # 'q' key or left arrow pressed exits the file menu
        elif key_pressed in BACK_KEYS or key_pressed == ord('q'):
            screen.clear()
            screen.refresh()
            break

        elif key_pressed in OPEN_KEYS:
            if "View" in options[cursor]:
                curses.endwin()

                open_cmd = 'less -N'

                if mime in FileType.F_MEDIA_MIMES:
                    open_cmd = MEDIA_OPEN

                    os.system(f"{open_cmd} '{cd}/{item.f_name}'")

                screen = curses.initscr()
                return

            elif "Edit" in options[cursor]:
                curses.endwin()

                os.system(f"{EDITOR} '{cd}/{item.f_name}'")

                screen = curses.initscr()
                return

            elif "Delete" in options[cursor]:
                screen.addstr(row, column, "Are you sure you want to delete this file? [y/N]: ")
                row += 2
                screen.refresh()

                curses.echo()
                inp = screen.getstr(row, column)
                curses.noecho()

                if inp.lower() == b'y':
                    rem_path = f"{cd}/{item.f_name}"

                    os.path.exists(rem_path) and os.remove(rem_path)
                    screen.clear()
                    screen.refresh()
                    return

            elif "Rename" in options[cursor]:
                file_name = item.f_name

                screen.addstr(row, column, f"Rename file '{file_name}' to what? : ")
                row += 2
                screen.refresh()

                curses.echo()
                to_rename = screen.getstr(row, column).decode("utf-8")
                row += 2
                curses.noecho()

                # make sure empty string is not passed
                if to_rename:
                    screen.addstr(row, column, f"Are you sure you want to rename '{file_name}' to '{to_rename}'?")
                    row += 1
                    screen.addstr("[y/N]")
                    row += 2
                    screen.refresh()

                    curses.echo()
                    user_assuredness = screen.getstr(row, column)
                    row += 1
                    curses.noecho()

                    if user_assuredness.lower() == b"y":
                        os.rename(f"{cd}/{file_name}", f"{cd}/{to_rename}")
                        screen.clear()
                        screen.refresh()
                        return

            elif "Command" in options[cursor]:
                row += 1
                screen.addstr(row, column, "cmd: ")

                curses.echo()
                curses.curs_set(1)
                command = screen.getstr(row, column + 6).decode("utf-8")
                curses.curs_set(0)
                curses.echo()
    
                # make sure command in not empty before continuing
                if command:

                    file_name = item.f_name

                    command += f" '{cd}/{file_name}'"

                    curses.endwin()
                    try:
                        subprocess.run(["sh", "-c", command])
                    except Exception as err:
                        print(f"Command failed with exception {err}")

                    print("\nPress enter to continue\n")
                    input()
                    screen = curses.initscr()

                    return

    return


def scroll(screen):
    """
    the main file manager\n
    this will list all the files, allow commands, etc.
    """
    curses.curs_set(0)

    list_files()

    cursor = 0

    global dir_contents
    global cd
    global show_hidden

    term_size = os.get_terminal_size()
    term_lines = term_size.lines - 1

    first_file = 0
    last_file = 1
    last_file = term_lines - 1 if len(dir_contents) > term_lines else len(dir_contents)

    while True:
        row = 1
        screen.erase()
        screen.addstr(row, 0, cd)
        if perm_error:
            screen.addstr(row, len(cd) + 1, "Permission Denied", curses.color_pair(11))
        row += 2

        # print all the items of the dir
        for item in dir_contents[first_file:last_file]:
            to_highlight = False
            # highlight file name if the cursor is on it
            if cursor == dir_contents.index(item):
                to_highlight = True

            print_file_name(screen, row, item, highlight=to_highlight)
            row += 1


        # highlight the file the cursor is on if it is higher than len(dir_contents)
        if cursor > len(dir_contents) - 1:
            cursor = len(dir_contents) - 1
            print_file_name(screen, cursor + 3, dir_contents[cursor], highlight=True)


        row += 1
        try:
            screen.addstr(row, 0, f"{cursor + 1}/{len(dir_contents)}")
        except curses.error: # force continue on error
            pass

        row += 1

        screen.refresh()

        key_pressed = screen.getch()

        # scroll terminal if needed
        if cursor == last_file - 3 and last_file < len(dir_contents):
            first_file += 1
            last_file += 1
        elif cursor == first_file + 2 and first_file > 0 and last_file > 9:
            first_file -= 1
            last_file -= 1

            dir_contents = []
            list_files()

        # quit options
        if key_pressed == ord('q'):
            break
        # up arrow key pressed
        elif key_pressed in UP_KEYS:
            if cursor > 0: cursor -= 1
        # down arrow key pressed
        elif key_pressed in DOWN_KEYS:
            if cursor < len(dir_contents) - 1: cursor += 1
        # enter is pressed on a dir
        elif key_pressed in OPEN_KEYS and dir_contents[cursor].f_type == FileType.F_DIR:

            if dir_contents[cursor].f_name == "..":
                cdback()
                cursor = 0

            else:
                cd += "/" + dir_contents[cursor].f_name

                dir_contents = []
                list_files()
                cursor = 0

            first_file = 0
            last_file = term_lines - 5 if len(dir_contents) > term_lines else len(dir_contents)

        elif key_pressed in BACK_KEYS:
            if cd == '/': continue

            cdback()
            cursor = 0
            first_file = 0
            last_file = term_lines - 5 if len(dir_contents) > term_lines else len(dir_contents)

        # enter pressed on anything other than a dir
        elif key_pressed in OPEN_KEYS:
            if dir_contents[cursor].f_type == FileType.F_FIFO or (
            dir_contents[cursor].f_type == FileType.F_UKNWN): continue

            options_screen = curses.newwin(25, 35, 3, 15)

            try:
                file_options(dir_contents[cursor], options_screen)
            except KeyboardInterrupt:
                return

            dir_contents = []
            list_files()

            screen.clear()

        # run a command on '!''
        elif key_pressed == ord('!'):
            row -= 1
            screen.addstr(row, 0, "cmd: ")

            curses.echo()
            curses.curs_set(1)
            command = screen.getstr(row, 6).decode("utf-8")
            curses.curs_set(0)
            curses.noecho()

            # make sure command is not empty
            if command:
                curses.endwin()

                try:
                    subprocess.run(["sh", "-c", command], cwd=cd)
                except Exception as err:
                    print("Command failed with exception " + str(err))

                print("\nPress enter to continue")
                input()
                screen = curses.initscr()

                dir_contents = []
                list_files()

        # toggle showing / hiding dotfiles
        elif key_pressed == ord('.'):
            show_hidden = not show_hidden
            dir_contents = []
            list_files()

            first_file = 0
            last_file = term_lines - 5 if len(dir_contents) > term_lines else len(dir_contents)

        # jump to first dir entry
        elif key_pressed in TOP_KEYS:
            cursor = 0
            d_len = len(dir_contents)
            first_file = 0
            last_file = term_lines - 5 if d_len > term_lines else d_len
        # jump to last dir entry
        elif key_pressed in BOTTOM_KEYS:
            d_len = len(dir_contents)
            cursor = d_len - 1
            if d_len > term_lines:
                last_file = d_len
                first_file = d_len - term_lines + 5


def help_menu():
    """
    prints the help text for the program\n
    i.e. command line args, options, etc.
    """
    print(
            "Scroll file manager\n"
            "Manage files using scroll; the console file manager\n"
            "\n"
            "Use:\n"
            "  scroll [OPTION] [DIR]\n"
            "  Run scroll with one of the optional options or an optional directory\n"
            "\n"
            "Options:\n"
            "  -h, --help\t\tPrint this screen and exit\n"
            "  -p, --print\t\tPrint the last directory scroll was in when it exists\n"
            "  -v, --verion\t\tPrint the version and exit\n"
            )


if __name__ == "__main__":
    if len(argv) > 1:
        for arg in argv[1:]:
            if arg == "--help" or arg == "-h":
                help_menu()
                quit()
            elif arg == "--print" or arg == "-p":
                print_on_exit = True
            elif arg == "--version" or arg == "-v":
                print(VERSION)
                quit()
            elif arg[0] == '-':
                print(f"scroll: {arg}: Invalid argument", file=sys.stderr)
                quit(1)
            else:
                cd = os.path.abspath(arg)
                if cd[-1] == '/' and cd != '/': cd = cd[:-1]

    if not os.path.exists(cd):
        print(f"scroll: {cd}: path does not exist", file=sys.stderr)
        quit(1)

    screen = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    screen.keypad(True)

    curses.start_color()

    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    try:
        scroll(screen)
    except KeyboardInterrupt:
        pass

    screen.clear()
    screen.refresh()

    curses.echo()
    curses.curs_set(1)
    curses.endwin()
    
    if print_on_exit: print(cd)

