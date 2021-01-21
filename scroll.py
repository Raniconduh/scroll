#!/usr/bin/env python3

import readchar
import os
import subprocess

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


#dir_contents = {"files": [], "dirs": [], "dotdirs": [], "dotfiles": []}
dir_contents = []

cd = os.getenv("PWD") + '/'
#home_dir = os.getenv("HOME")

PHOTO_EXTENSIONS = ["jpg", "jpeg", "png", "svg"]


def list_files():
    dir_contents.append("../")
    for item in os.scandir(cd):
        if item.is_dir():
            dir_contents.append(item.name + "/")

        elif item.is_symlink():
            dir_contents.append(item.name + "@")

        elif os.access(item.path, os.X_OK):
            dir_contents.append(item.name + "*")

        else:
            dir_contents.append(item.name)


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


def get_file_ext(item):
    item_split = item.split('.')
    if len(item_split) == 1:
        return None
    return item_split[-1]


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
    else:
        if highlight:
            print(HWHITE + BLACK + item + RESET, end=end)
        else:
            print(item, end=end)


def file_options(item):
    cursor = 0
    options = ["View File", "Edit File", "Delete File", "Rename File"]

    while True:
        print(CLEAR)
        print_file_name(item, end="\n\n")

        for option in options:
            if options.index(option) == cursor:
                print(HCYAN + option + RESET)
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

                print("Rename file '" + file_name + "' to what? : ", end = "")
                to_rename = input()
                
                print("Are you sure you want to rename '" + file_name + "' to '" + to_rename + "'?", end="\n[y/N]\n")
                user_assuredness = input()

                if user_assuredness.lower() == "y":
                    subprocess.run(["mv", cd + file_name, cd + to_rename])
                    return None

    return None


def scroll():
    list_files()

    cursor = 0;

    while True:
        print(CLEAR)
       
        global cd
        print(cd, end="\n\n")

        global dir_contents
        for item_index in range(len(dir_contents)):
            item_name = dir_contents[item_index]

            # print the name of the file with colors in accordance
            # to where the cursor is and what kind of file it is
            if cursor == item_index:
                print_file_name(dir_contents[item_index], highlight=True)
            else:
                print_file_name(dir_contents[item_index])
            
        key_pressed = readchar.readkey()

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
            quit()
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

            else:
                cd += dir_contents[cursor]

                dir_contents = []
                list_files()
                cursor = 0

        elif key_pressed == readchar.key.LEFT and cd != '/':
            cdback()

        # enter pressed on anything other than a dir
        elif key_pressed == readchar.key.ENTER or key_pressed == readchar.key.RIGHT:
            file_options(dir_contents[cursor])
            dir_contents = []
            cursor = 0
            list_files()


scroll()

