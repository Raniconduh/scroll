#!/usr/bin/env python3

import readchar
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

cd = os.getenv("PWD") + '/'

EDITOR = os.getenv("EDITOR") if os.getenv("EDITOR") else "editor"

MEDIA_OPEN = "open" if platform.system() == "Darwin" else "xdg-open"

# maybe remove these tuples and use mime type checking instead..
MEDIA_EXTENSIONS = (
        "jpg", "jpeg", "png", "svg",
        "m4v", "mp4", "mkv", "m4a",
        "mp3", "webm"
)

MEDIA_MIMES = ("video", "image")

ARCHIVE_EXTENSIONS = (
        "tar", "xz", "bz2", "gz",
        "zip", "rar"
)


# keypresses
OPEN_KEYS = (readchar.key.ENTER, readchar.key.RIGHT,  'l')
BACK_KEYS = (readchar.key.LEFT, 'h')
UP_KEYS = (readchar.key.UP, 'k')
DOWN_KEYS = (readchar.key.DOWN, 'j')
TOP_KEYS = ('g')
BOTTOM_KEYS = ('G')


# if the current dir is not readable / gives a permission error
perm_error = False

# whether or not to show dotfiles
show_hidden = False

# whether or not to print the path name when scroll exits
print_on_exit = False

def list_files():
    """
    list all the files in the current dir\n
    listed files will be appended to the dir_contents list/dict\n
    files names may also end in special character:\n
        ?) file does not exist?\n
        /) file is a dir\n
        @) file is a symbolic link\n
        *) file is executable\n
        |) file is pip / fifo
    """
    tmp_contents = {"dirs": [], "files": []}

    global perm_error

    try:
        items = os.scandir(cd)

        perm_error = False

        for item in items:
            # do not append dotfiles to list if show_hidden is false
            if not show_hidden and (item.name[0] == '.') : pass

            elif not os.access(item, os.F_OK):
                tmp_contents["files"].append(item.name + '?')

            elif item.is_dir():
                tmp_contents["dirs"].append(item.name + "/")

            else:
                if item.is_symlink():
                    tmp_contents["files"].append(item.name + "@")

                elif os.access(item.path, os.X_OK):
                    tmp_contents["files"].append(item.name + "*")

                elif stat.S_ISFIFO(os.stat(item.path).st_mode):
                    tmp_contents["files"].append(item.name + "|")

                else:
                    tmp_contents["files"].append(item.name)

        tmp_contents["dirs"].sort()
        tmp_contents["files"].sort()

        for tmp_dir in tmp_contents["dirs"]:
            dir_contents.append(tmp_dir)

        for tmp_file in tmp_contents["files"]:
            dir_contents.append(tmp_file)
        
        if not len(dir_contents) : dir_contents.append("../")
    except PermissionError:
        perm_error = True
        dir_contents.append('../')


# cd into .. without uglying the path
def cdback():
    """
    cd into .. without making the path ugly
    """
    global cd
    global dir_contents

    # remove the last two segments of the path and append a '/'
    cd = '/'.join(cd.split('/')[:-2]) + '/'
    dir_contents = []
    list_files()


def isdir(item):
    """
    checks if a file is a dir\n
    files ending in '/' are directories
    """
    return item[-1] == '/'


def issymlink(item):
    """
    check if a file is a symbolic link\n
    files ending with '@' are symlinks
    """
    return item[-1] == '@'


def isexec(item):
    """
    check if a file is executable\n
    files ending with '*' are executable
    """
    return item[-1] == '*'


def isascii(item):
    """
    check if a file is not anything special\n
    files that do not end in special characters are normal / ascii
    """
    if not isdir(item) and not issymlink(item) and not isexec(item):
        return True
    return False


def isfifo(item):
    """
    check if file is fifo aka named pipe\n
    files ending with '|' are fifos
    """
    return item[-1] == '|'


def exists(item):
    """
    check if file exist i.e.e the last character is not '?'
    """
    return item[-1] != '?'


def get_file_ext(item):
    """
    return th extension of the file\n
    e.g. 'file.txt' will return 'txt'\n
    no extension e.g. 'file' will return None
    """
    item_split = item.split('.')
    if len(item_split) == 1:
        return None
    return item_split[-1].lower()


def print_file_name(screen, row, item, column=0, highlight=False):
    """
    print a file name based on what kind of file it is\n
    may also print a highlighted or non-highlited file\n
    this function is similar to curses.window.addstr()
    """

    color = 14
    ext = True

    # assign colors and whether or not th file is special
    if isdir(item):                                color = 1
    elif issymlink(item):                          color = 3
    elif isexec(item):                             color = 5
    elif get_file_ext(item) in MEDIA_EXTENSIONS:   color, ext = 7,  False
    elif isfifo(item):                             color = 9
    elif get_file_ext(item) in ARCHIVE_EXTENSIONS: color, ext = 11, False
    elif not exists(item):                         color = 11
    else:                                          color, ext = 13, False

    if highlight: color += 1
    if not ext: screen.addstr(row, column, item, curses.color_pair(color))
    else:
        screen.addstr(row, column, item[:-1], curses.color_pair(color))
        screen.addstr(row, len(item[:-1]) + column, item[-1])
 

def file_options(item, screen):
    """
    the options menu for a given file
    """
    curses.curs_set(0)
    curses.start_color()

    screen.clear()
    screen.refresh()

    cursor = 0
    
    mime = mimetypes.guess_type(f"{cd}/{item}")[0]
    if mime: mime = mime.partition('/')[0].lower()

    options = ["View File", "Edit File", "Delete File", "Rename File", "Open File with Command"]
    if mime in MEDIA_MIMES: options.remove("Edit File") # cannot edit media files

    while True:
        row = 0
        column = 2
        screen.erase()

        screen.border('|', 1, 1, 1, 1, 1, 1, 1)
        
        print_file_name(screen, row, item, column=column)
        row += 2

        for option in options:
            if options.index(option) == cursor:
                print_file_name(screen, row, option, column=column, highlight=True)
                row += 1
            else:
                print_file_name(screen, row, option, column=column)
                row += 1

        screen.refresh()

        key_pressed = readchar.readkey()

        # up arrow pressed
        if key_pressed in UP_KEYS and cursor > 0:
            cursor -= 1

        # down arrow pressed
        elif key_pressed in DOWN_KEYS and cursor < len(options) - 1:
            cursor += 1

        # 'q' key or left arrow pressed exits the file menu
        elif key_pressed in BACK_KEYS or key_pressed == 'q':
            screen.clear()
            screen.refresh()
            break

        elif key_pressed in OPEN_KEYS:
            if "View" in options[cursor]:
                curses.endwin()

                open_cmd = 'less -N'

                if mime in MEDIA_MIMES:
                    open_cmd = MEDIA_OPEN

                if isascii(item):
                    os.system(f"{open_cmd} '{cd}{item}'")
                else:
                    os.system(f"{open_cmd} '{cd}{item[:-1]}'")

                screen = curses.initscr()
                return

            elif "Edit" in options[cursor]:
                curses.endwin()

                if isascii(item):
                    os.system(f"{EDITOR} '{cd}{item}'")
                else:
                    os.system(f"{EDITOR} '{cd}{item[:-1]}'")

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
                    if isascii(item):
                        rem_path = cd + item
                    else:
                        rem_path = cd + item[:-1]

                    os.path.exists(rem_path) and os.remove(rem_path)
                    screen.clear()
                    screen.refresh()
                    return

            elif "Rename" in options[cursor]:
                if isascii(item):
                    file_name = item
                else:
                    file_name = item[:-1]

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
                        os.rename(cd + file_name, cd + to_rename)
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

                    if isascii(item):
                        file_name = item
                    else:
                        file_name = item[:-1]

                    command += f" '{cd + file_name}'"

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

        key_pressed = readchar.readkey()

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
        if key_pressed == readchar.key.CTRL_C or key_pressed == 'q':
            break
        # up arrow key pressed
        elif key_pressed in UP_KEYS and cursor > 0:
            cursor -= 1
        # down arrow key pressed
        elif key_pressed in DOWN_KEYS and cursor < len(dir_contents) - 1:
            cursor += 1
        # enter is pressed on a dir
        elif key_pressed in OPEN_KEYS and isdir(dir_contents[cursor]):
            if dir_contents[cursor] == "../":
                cdback()
                cursor = 0

            else:
                cd += dir_contents[cursor]

                dir_contents = []
                list_files()
                cursor = 0

            first_file = 0
            last_file = term_lines - 5 if len(dir_contents) > term_lines else len(dir_contents)

        elif key_pressed in BACK_KEYS  and cd != '/':
            cdback()
            cursor = 0
            first_file = 0
            last_file = term_lines - 5 if len(dir_contents) > term_lines else len(dir_contents)

        # enter pressed on anything other than a dir
        elif key_pressed in OPEN_KEYS and (
                not isfifo(dir_contents[cursor])
                and exists(dir_contents[cursor])):
            options_screen = curses.newwin(25, 35, 3, 15)

            try:
                file_options(dir_contents[cursor], options_screen)
            except KeyboardInterrupt:
                return

            dir_contents = []
            list_files()

            screen.clear()

        # run a command on '!''
        elif key_pressed == '!':
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
        elif key_pressed == '.':
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
                cd += '/' if cd[-1] != '/' else ''

    if not os.path.exists(cd):
        print(f"scroll: {cd}: path does not exist", file=sys.stderr)
        quit(1)

    screen = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()

    curses.start_color()

    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLUE)

    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)

    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_GREEN)

    curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_MAGENTA)

    curses.init_pair(9, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    curses.init_pair(11, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_RED)

    curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_WHITE)

    try:
        scroll(screen)
    except KeyboardInterrupt:
        pass

    screen.clear()
    screen.refresh()

    curses.nocbreak()
    curses.echo()
    curses.curs_set(1)
    curses.endwin()
    
    if print_on_exit: print(cd)

