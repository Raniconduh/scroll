# Scroll

A small and simple console file manager


# Use
Using scroll is very simple as it has few commands and actuallt interacts with the user. It is best run using a 256 bit color terminal although it does also work in an 8 bit color terminal. (Monochrome terminals have not been tested)

scroll may be started as a single command: `scroll`, or with a path as the first (and only) argument. e.g. `scroll /path/to/dir` will start scroll in the directory `/path/to/dir`

The `--help` flag may be specified to scroll which will result in the help screen being showed.

## Commands

* Up Arrow: move the cursor up
* Down Arraw: move the cursor down
* `!` (Exclamation Mark): Run a shell command
* Enter Key or Right Arrow: if the cursor is on a dorectory, it will enter that directory. If it is a file, the file options menu will be opened
* Left Arrow: Move into the previous directory. e.g if the current directory is `/path/to/dir`, then the directory `/path/to` will be entered


# Installation
scroll depends on python3 and the module `readchar`. 

Installing scroll is not necessary as it can be run immediatly via `./scroll.py`, although you may install it to system somewhere in your path. e.g. `cp scroll.py <PATH>`, replacing `<PATH>` with any directory in your `PATH` environment variable.

## Todo:

- add ability to show and hide dotfiles
- add more options to file options menu

