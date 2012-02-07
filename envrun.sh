#!/bin/sh
export HOME="/home/ezl/"
export PROJECT_DIR="$HOME/code/twittermarketing/"
. $HOME/.virtualenvs/twittermarketing/bin/activate
export PYTHONPATH=$PYTHONPATH:$HOME/code/
export DJANGO_SETTINGS_MODULE="settings"
cd $PROJECT_DIR
python manage.py $1

