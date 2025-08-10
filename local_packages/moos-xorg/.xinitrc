TIMEOUT=300
xset s $TIMEOUT $TIMEOUT dpms $TIMEOUT $TIMEOUT $TIMEOUT
xset r rate 300 25
xrandr --dpi 100
nohup xss-lock slock </dev/null >/dev/null 2>&1 &
status_bar &
dwm &
