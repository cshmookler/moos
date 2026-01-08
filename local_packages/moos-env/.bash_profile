#
# ~/.bash_profile
#

if test -f "$HOME/.bashrc"; then
    source "$HOME/.bashrc"
fi

if test -d "$HOME/.profile"; then
    for f in "$(ls $HOME/.profile/*)"; do
        source "$f";
    done
fi
