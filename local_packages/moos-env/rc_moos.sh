# Prompts
PS0=''
PS1='\[\e[0m\]$(EXIT_CODE="$?"; [ "$EXIT_CODE" -eq "0" ] || echo "\[\e[31;1m\]$EXIT_CODE\[\e[0m\]:")\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[94;1m\]\w\[\e[0m\]$ '
PS2='> '

# Shell settings
shopt -s dotglob

# Aliases
alias ls='ls --color=auto'
alias sl='ls --color=auto'
alias l='ls --color=auto -A'
alias ll='ls --color=auto -alF'
alias pamcan='pacman'
alias grep='grep --color=auto'
alias c='python -Bqic "from math import *"'
alias duck='du --all --max-depth=1 --human-readable 2>/dev/null | sort --human-numeric-sort'
alias cura='cura -platformtheme gtk3'
alias al='ffplay -vn -loop 0'
