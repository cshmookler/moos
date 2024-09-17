#!/usr/bin/bash

if test "$USER" = 'root'; then
    echo "Error: Running this script as $USER is prohibited"
    exit 1
fi

if ! rsync --archive --ignore-existing "--chown=$USER:$USER" "/etc/user_env/" "$HOME"; then
    echo "Error: Failed to update the environment for $USER"
    exit 1
fi

echo "Successfully updated the environment for $USER"
