#
# ~/.bash_profile
#

if test -f "~/.bashrc"; then
    source "~/.bashrc"
fi

if test -d "~/.profile"; then
    for f in "~/.profile/*"; do
        source "$f";
    done
fi
