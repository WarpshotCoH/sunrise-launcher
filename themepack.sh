#!/bin/bash

CUR=$(pwd)
THEME=$(basename $1)
WRK=$(dirname $1)

cd $WRK

zip -r $THEME.zip $THEME

mv $THEME.zip $CUR/$THEME.sunrisetheme
