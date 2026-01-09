#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

if test -d "$HOME/.bashrc.d"; then
    for f in $(ls $HOME/.bashrc.d/*); do
        source "$f";
    done
fi
