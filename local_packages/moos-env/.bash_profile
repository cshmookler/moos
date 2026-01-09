#
# ~/.bash_profile
#

if test -f "$HOME/.bashrc"; then
    source "$HOME/.bashrc"
fi

if test -d "$HOME/.bash_profile.d"; then
    for f in $(ls $HOME/.bash_profile.d/*); do
        source "$f";
    done
fi
