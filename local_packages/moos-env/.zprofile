#
# ~/.zprofile
#

if test -f "~/.zshrc"; then
    source "~/.zshrc"
fi

if test -d "~/.profile"; then
    for f in "~/.profile/*"; do
        source "$f";
    done
fi
