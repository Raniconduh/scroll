#!/usr/bin/env python3

import readchar
import os
import subprocess
import stat
from sys import argv
import curses

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


# dir_contents = {"files": [], "dirs": [], "dotdirs": [], "dotfiles": []}
dir_contents = []

cd = os.getenv("PWD") + '/'

PHOTO_EXTENSIONS = ["jpg", "jpeg", "png", "svg"]
ARCHIVE_EXTENSIONS = ["tar", "xz", "bz2", "gz", "zip", "rar"]


# list and store all the files in dir
def list_files():
    tmp_contents = {"dirs": [], "files": []}

    dir_contents.append("../")

    try:
        items = os.scandir(cd)

        for item in items:
            if not os.access(item, os.F_OK):
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


def exists(item):
    if item[-1] == '?':
        return False
    return True


# return the extension of the file
# e.g. 'file.txt' will return txt
# no extension e.g. 'file' will return None
def get_file_ext(item):
    item_split = item.split('.')
    if len(item_split) == 1:
        return None
    return item_split[-1].lower()


# print a file name based on what kind of file it is
def print_file_name(screen, row, item, highlight=False):
    if isdir(item):
        if highlight:
            screen.addstr(row, 0, item[:-1], curses.color_pair(2))
            screen.addstr(row, len(item[:-1]), item[-1])
        else:
            screen.addstr(row, 0, item[:-1], curses.color_pair(1))
            screen.addstr(row, len(item[:-1]), item[-1])

    elif issymlink(item):
        if highlight:
            screen.addstr(row, 0, item[:-1], curses.color_pair(4))
            screen.addstr(row, len(item[:-1]), item[-1])
        else:
            screen.addstr(row, 0, item[:-1], curses.color_pair(3))
            screen.addstr(row, len(item[:-1]), item[-1])

    elif isexec(item):
        if highlight:
            screen.addstr(row, 0, item[:-1], curses.color_pair(6))
            screen.addstr(row, len(item[:-1]), item[-1])
        else:
            screen.addstr(row, 0, item[:-1], curses.color_pair(5))
            screen.addstr(row, len(item[:-1]), item[-1])

    elif get_file_ext(item) in PHOTO_EXTENSIONS:
        if highlight:
            screen.addstr(row, 0, item, curses.color_pair(8))
        else:
            screen.addstr(row, 0, item, curses.color_pair(7))

    elif isfifo(item):
        if highlight:
            screen.addstr(row, 0, item[:-1], curses.color_pair(10))
            screen.addstr(row, len(item[:-1]), item[-1])
        else:
            screen.addstr(row, 0, item[:-1], curses.color_pair(9))
            screen.addstr(row, len(item[:-1]), item[-1])

    elif get_file_ext(item) in ARCHIVE_EXTENSIONS:
        if highlight:
            screen.addstr(row, 0, item, curses.color_pair(12))
        else:
            screen.addstr(row, 0, item, curses.color_pair(11))

    elif not exists(item):
        if highlight:
            screen.addstr(row, 0, item[:-1], curses.color_pair(12))
            screen.addstr(row, len(item[:-1]), item[-1])
        else:
            screen.addstr(row, 0, item[:-1], curses.color_pair(11))
            screen.addstr(row, len(item[:-1]), item[-1])

    else:
        if highlight:
            screen.addstr(row, 0, item, curses.color_pair(14))
        else:
            screen.addstr(row, 0, item, curses.color_pair(13))


def file_options(item, screen):
    curses.curs_set(0)
    curses.start_color()

    screen.clear()
    screen.refresh()

    cursor = 0
    options = ["View File", "Edit File", "Delete File", "Rename File", "Open File with Command"]

    while True:
        row = 0
        screen.erase()
        screen.addstr(row, 0, item)
        row += 2

        for option in options:
            if options.index(option) == cursor:
                print_file_name(screen, row, option, highlight=True)
                row += 1
            else:
                print_file_name(screen, row, option)
                row += 1

        screen.refresh()

        key_pressed = readchar.readkey()

        # up arrow pressed
        if key_pressed == readchar.key.UP and cursor > 0:
            cursor -= 1

        # down arrow pressed
        elif key_pressed == readchar.key.DOWN and cursor < len(options) - 1:
            cursor += 1

        # 'q' key or left arrow pressed exits the file menu
        elif key_pressed == readchar.key.LEFT or key_pressed == 'q':
            screen.clear()
            screen.refresh()
            break

        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT:
            if "View" in options[cursor]:
                if isascii(item):
                    subprocess.run(["less", "-N", cd + item])
                else:
                    subprocess.run(["less", "-N", cd + item[:-1]])

                screen.clear()
                screen.refresh()

            elif "Edit" in options[cursor]:
                if isascii(item):
                    subprocess.run(["editor", cd + item])
                else:
                    subprocess.run(["editor", cd + item[:-1]])

                screen.clear()
                screen.refresh()

            elif "Delete" in options[cursor]:
                screen.addstr(row, 0, "Are you sure you want to delete this file? [y/N]: ")
                row += 1
                screen.refresh()

                curses.echo()
                inp = screen.getstr(row, 0)
                curses.noecho()

                if inp.lower() == b'y':
                    if isascii(item):
                        subprocess.run(["rm", "-rf", cd + item])
                    else:
                        subprocess.run(["rm", "-rf", cd + item[:-1]])

                    screen.clear()
                    screen.refresh()

                    return None

            elif "Rename" in options[cursor]:
                if isascii(item):
                    file_name = item
                else:
                    file_name = item[:-1]

                screen.addstr(row, 0, "Rename file '" + file_name + "' to what? : ")
                row += 2
                screen.refresh()

                curses.echo()
                to_rename = screen.getstr(row, 0).decode("utf-8")
                row += 2
                curses.noecho()

                screen.addstr(row, 0, "Are you sure you want to rename '" + file_name + "' to '" + to_rename + "'?")
                row += 1
                screen.addstr("[y/N]")
                row += 2
                screen.refresh()

                curses.echo()
                user_assuredness = screen.getstr(row, 0)
                row += 1
                curses.noecho()

                if user_assuredness.lower() == b"y":
                    subprocess.run(["mv", cd + file_name, cd + to_rename])
                    screen.clear()
                    screen.refresh()
                    return None

            elif "Command" in options[cursor]:
                row += 1
                screen.addstr(row, 0, "cmd: ")

                curses.echo()
                curses.curs_set(1)
                command = screen.getstr(row, 6).decode("utf-8")
                curses.curs_set(0)
                curses.echo()
    
                # make sure command in not empty before continuing
                if command:
                    command = command.split(" ")

                    if isascii(item):
                        file_name = item
                    else:
                        file_name = item[:-1]

                    command.append(cd + file_name)

                    curses.endwin()
                    try:
                        subprocess.run(command)
                    except Exception as err:
                        print("Command failed with exception " + str(err))

                    print("\nPress enter to continue\n")
                    input()
                    screen = curses.initscr()

                    return

    return None


def scroll(screen):
    print(CLRLINE)
    print(CLEAR)

    curses.curs_set(0)

    list_files()

    cursor = 0

    global dir_contents
    global cd

    term_size = os.get_terminal_size()

    first_file = 0
    last_file = 1
    last_file = term_size.lines - 5 if len(dir_contents) > term_size.lines else len(dir_contents)

    while True:
        row = 0
        row += 1
        screen.erase()
        screen.addstr(row, 0, cd)
        row += 2

        for item in dir_contents[first_file:last_file]:
            if cursor == dir_contents.index(item):
                print_file_name(screen, row, item, highlight=True)
                row += 1
            else:
                print_file_name(screen, row, item)
                row += 1

        row += 1
        screen.addstr(row, 0, str(cursor + 1) + "/" + str(len(dir_contents)))
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
        elif (key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT) and isdir(dir_contents[cursor]):
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
        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT and not isfifo(dir_contents[cursor]) and exists(dir_contents[cursor]):
            options_screen = curses.newwin(25, 35, 3, 15)

            try:
                file_options(dir_contents[cursor], options_screen)
            except KeyboardInterrupt:
                return None

            dir_contents = []

            if cursor > len(dir_contents):
                cursor -= 1

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
                command = command.split(" ")

                curses.endwin()

                try:
                    subprocess.run(command, cwd=cd)
                except Exception as err:
                    print("Command failed with exception " + str(err))

                print("\nPress enter to continue")
                input()
                screen = curses.initscr()

                dir_contents = []
                list_files()


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

