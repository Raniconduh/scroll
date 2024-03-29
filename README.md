# Scroll

A small and simple console file manager

![Scroll](https://imgur.com/fij9ZNR.png)

## Use

    scroll [OPTION...] [DIRECTORY]

Open scroll in the specified directory (if no directory is specified, scroll opens the current directory)

Using scroll is very simple as it has few commands and actually interacts with the user. It is best run using a 256 bit color terminal although it does also work in an 8 bit color terminal. (Monochrome terminals have not been tested).


### Options

* `-h`, `--help`              Print the help menu and exit 
* `-p`, `--print`             When scroll exists, print the directory it was last in
* `-v`, `--version`           Print the version and exit

### Commands

* Up Arrow or `k`: move the cursor up
* Down Arrow or `j`: move the cursor down
* Enter Key, Right Arrow, or `l`: if the cursor is on a directory, it will enter that directory. If it is a file, the file options menu will be opened
* Left Arrow or `h`: Move into the previous directory. E.g if the current directory is `/path/to/dir`, then the directory `/path/to` will be entered
* `.` (Period): Hide or show dotfiles (toggle).
* `!` (Exclamation Mark): Run a shell command
* `g`: Go to the top of the directory
* `G`: Go to the bottom of the directory


## Installation
scroll depends solely on python3. As a lone file, it can be easily copied to a directory on the `PATH` environment variable for quick access.

### Recommends
To use scroll to its full potential, it is recommended to have a file viewer installed (default is `less`) and a text editor (default is `editor`).

### Todo:

- add more options to file options menu
- bug fixed / optimizations
- clean up code

