#
# ~/.zshrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

if test -d "~/.rc"; then
    for f in "~/.rc/*"; do
        source "$f";
    done
fi
