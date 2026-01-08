#
# ~/.zprofile
#

if test -f "$HOME/.zshrc"; then
    source "$HOME/.zshrc"
fi

if test -d "$HOME/.profile"; then
    for f in "$(ls $HOME/.profile/*)"; do
        source "$f";
    done
fi
