#
# ~/.zshrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

if test -d "$HOME/.rc"; then
    for f in "$(ls $HOME/.rc/*)"; do
        source "$f";
    done
fi
