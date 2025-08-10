#
# ~/.bash_profile
#

[[ -f ~/.bashrc ]] && . ~/.bashrc

# Start the X server on login
if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" = 1 ]; then
    startx
fi
