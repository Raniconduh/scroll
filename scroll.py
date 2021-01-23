#!/usr/bin/env python3

import readchar
import os
import subprocess
import stat
from sys import argv
import curses
import signal

RESET = "\u001B[0m"
BLACK = "\u001B[30m"
RED = "\u001B[31m"
GREEN = "\u001B[32m"
YELLOW = "\u001B[33m"
BLUE = "\u001B[34m"
PURPLE = "\u001B[35m"
CYAN = "\u001B[36m"
WHITE = "\u001B[37m"
CLEAR = "\033[H\033[2J"

HBLACK = "\u001b[40m"
HRED = "\u001b[41m"
HGREEN = "\u001b[42m"
HYELLOW = "\u001b[43m"
HBLUE = "\u001b[44m"
HPURPLE = "\u001b[45m"
HCYAN = "\u001b[46m"
HWHITE = "\u001b[47m"

CLRLINE = "\033[2K\r"


#dir_contents = {"files": [], "dirs": [], "dotdirs": [], "dotfiles": []}
dir_contents = []

cd = os.getenv("PWD") + '/'
#home_dir = os.getenv("HOME")

PHOTO_EXTENSIONS = ["jpg", "jpeg", "png", "svg"]
ARCHIVE_EXTENSIONS = ["tar", "xz", "bz2", "gz", "zip", "rar"]


# list and store all the files in dir
def list_files():
    tmp_contents = {"dirs":[], "files":[]}

    dir_contents.append("../")

    try:
        items = os.scandir(cd)

        for item in items:
            if not os.access(item, os.F_OK):
                pass
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

    except PermissionError:
        pass


# check if a file name is a directory
# files ending with '/' are directories
def isdir(item):
    if item[-1] == '/':
        return True
    return False


# check if a file name is a symbolic link
# files ending with '@' are symlinks
def issymlink(item):
    if item[-1] == '@':
        return True
    return False

# check if a file name is executeable
# files ending with '*' are executeable
def isexec(item):
    if item[-1] == "*":
        return True
    return False

def isascii(item):
    if not isdir(item) and not issymlink(item) and not isexec(item):
        return True
    return False

# check if file is fifo aka named pipe
# files ending with '|' are fifos
def isfifo(item):
    if item[-1] == "|":
        return True
    return False


# return the extension of the file
# e.g. 'file.txt' will return txt
# no extension e.g. 'file' will return None
def get_file_ext(item):
    item_split = item.split('.')
    if len(item_split) == 1:
        return None
    return item_split[-1].lower()


# print a file name based on what kind of file it is
def print_file_name(item, highlight=False, end='\n'):
    if isdir(item):
        if highlight:
            print(HBLUE + BLACK + item[:-1] + RESET + item[-1], end=end)
        else:
            print(BLUE + item[:-1] + RESET + item[-1], end=end)

    elif issymlink(item):
        if highlight:
            print(HCYAN + BLACK + item[:-1] + RESET + item[-1], end=end)
        else:
            print(CYAN + item[:-1] + RESET + item[-1], end=end)

    elif isexec(item):
        if highlight:
            print(HGREEN + BLACK + item[:-1] + RESET + item[-1], end=end)
        else:
            print(GREEN + item[:-1] + RESET + item[-1], end=end)

    elif get_file_ext(item) in PHOTO_EXTENSIONS:
        if highlight:
            print(HPURPLE + BLACK + item + RESET, end=end)
        else:
            print(PURPLE + item + RESET, end=end)
            
    elif isfifo(item):
        if highlight:
            print(HYELLOW + BLACK + item[:-1] + RESET + item[-1])
        else:
            print(YELLOW + item[:-1] + RESET + item[-1])

    elif get_file_ext(item) in ARCHIVE_EXTENSIONS:
        if highlight:
            print(HRED + BLACK + item + RESET, end=end)
        else:
            print(RED + item + RESET, end=end)
    else:
        if highlight:
            print(HWHITE + BLACK + item + RESET, end=end)
        else:
            print(item, end=end)


def file_options(item):
    curses.curs_set(0)

    cursor = 0
    options = ["View File", "Edit File", "Delete File", "Rename File"]

    while True:
        print(CLEAR)
        print(CLRLINE, end='')
        print_file_name(item, end="\n\n")

        for option in options:
            print(CLRLINE, end='')
            if options.index(option) == cursor:
                print(HWHITE + BLACK + option + RESET)
            else:
                print(option)

        key_pressed = readchar.readkey()

        # technincally sigill
        if key_pressed == readchar.key.CTRL_C:
            quit()

        # up arrow pressed
        elif key_pressed == readchar.key.UP and cursor > 0:
            cursor -= 1

        # down arrow pressed
        elif key_pressed == readchar.key.DOWN and cursor < len(options) - 1:
            cursor += 1

        # 'q' key or left arrow pressed exits the file menu
        elif key_pressed == readchar.key.LEFT or key_pressed == 'q':
            break

        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT:
            if "View" in options[cursor]:
                if isascii(item):
                    subprocess.run(["less", "-N", cd + item])
                else:
                    subprocess.run(["less", "-N", cd + item[:-1]])

            elif "Edit" in options[cursor]:
                if isascii(item):
                    subprocess.run(["editor", cd + item])
                else:
                    subprocess.run(["editor", cd + item[:-1]])

            elif "Delete" in options[cursor]:
                print(CLRLINE, end='')
                print("Are you sure you want to delete this file? [y/N]", end=": ")
                inp = input()
                if inp.lower() == 'y':
                    if isascii(item):
                        subprocess.run(["rm", cd + item])
                    else:
                        subprocess.run(["rm", cd + item[:-1]])
                    return None
            
            elif "Rename" in options[cursor]:
                if isascii(item):
                    file_name = item
                else:
                    file_name = item[:-1]

                print(CLRLINE, end='')
                print("Rename file '" + file_name + "' to what? : ", end = "")
                to_rename = input()
                
                print(CLRLINE, end='')
                print("Are you sure you want to rename '" + file_name + "' to '" + to_rename + "'?", end="\n[y/N]\n")
                user_assuredness = input()

                if user_assuredness.lower() == "y":
                    subprocess.run(["mv", cd + file_name, cd + to_rename])
                    return None

    return None


def scroll():
    print(CLRLINE)
    print(CLEAR)

    curses.curs_set(0)

    list_files()

    cursor = 0;

    global dir_contents
    global cd

    # scrolling = False

    term_size = os.get_terminal_size()

    first_file = 0
    last_file = 1
    last_file = term_size.lines - 5 if len(dir_contents) > term_size.lines else len(dir_contents)

    while True:
        print(CLEAR)

        print(CLRLINE, end='')
        print(cd, end="\n\n")

        for item in dir_contents[first_file:last_file]:
            print(CLRLINE, end='')
            if cursor == dir_contents.index(item):
                print_file_name(item, highlight=True)
            else:
                print_file_name(item)

        print(CLRLINE, end='')
        print("\n" + str(cursor + 1) + "/" + str(len(dir_contents)))

        key_pressed = readchar.readkey()

        # scroll terminal if needed
        if cursor == last_file - 3 and last_file < len(dir_contents):
            first_file += 1
            last_file += 1
        elif cursor == first_file + 2 and first_file > 0 and last_file > 9:
            first_file -= 1
            last_file -= 1

        # cd into .. without uglying the path
        def cdback():
            global cd
            global dir_contents

            cd = cd.split('/')
            cd = cd[:-2]
            cd = '/'.join(cd)
            cd += '/'

            dir_contents = []
            list_files()
            cursor = 0

        # quit options
        if key_pressed == readchar.key.CTRL_C or key_pressed == 'q':
            break
        # up arrow key pressed
        elif key_pressed == readchar.key.UP and cursor > 0:
            cursor -= 1
        # down arrow key pressed
        elif key_pressed == readchar.key.DOWN and cursor < len(dir_contents) - 1:
            cursor += 1
        # enter is pressed on a dir
        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT and isdir(dir_contents[cursor]):
            if dir_contents[cursor] == "../":
                cdback()
                cursor = 0

            else:
                cd += dir_contents[cursor]

                dir_contents = []
                list_files()
                cursor = 0

            first_file = 0
            last_file = term_size.lines - 5 if len(dir_contents) > term_size.lines else len(dir_contents)

        elif key_pressed == readchar.key.LEFT and cd != '/':
            cdback()
            cursor = 0
            first_file = 0
            last_file = term_size.lines - 5 if len(dir_contents) > term_size.lines else len(dir_contents)


        # enter pressed on anything other than a dir
        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT and not isfifo(dir_contents[cursor]):
            file_options(dir_contents[cursor])
            dir_contents = []
            cursor = 0
            list_files()
            first_file = 0
            last_file = term_size.lines - 5 if len(dir_contents) > term_size.lines else len(dir_contents)


def help_menu():
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
            )


if __name__ == "__main__":
    if len(argv) > 1:
        if argv[1] == "--help" or argv[1] == "-h":
            help_menu()
            quit()

        elif argv[1] == "..":
            cd = cd.split('/')
            cd = cd[:-2]
            cd = '/'.join(cd)
            cd += '/'

        elif len(argv[1]) > 2 and argv[:2] == "..":
            if argv[1][0] == '.' and argv[1][1] == '.' and argv[1][2] == '/':
                cd = cd.split('/')
                cd = cd[:-2]

                tmp_argv = argv[1].split("/")

                for segment in tmp_argv[1:]:
                    cd.append(segment)

                cd = '/'.join(cd)
                cd += '/'

        elif argv[1] == "~" or argv[:2] == "~/":
            cd = os.path.expanduser(argv[1])
            print(argv[1])

        else:
            cd = argv[1] + '/'

    

    screen = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    # screen.keypad(True)

    try:
        scroll()
    except KeyboardInterrupt:
        pass

    # screen.keypad(False)
    curses.nocbreak()
    curses.echo()
    curses.curs_set(1)
    curses.endwin()

