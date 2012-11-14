#!/bin/bash                                                                     
if [ `uname` == 'Darwin' ]
then
    if [ -f ~/.bash_profile ]
    then
        source ~/.bash_profile
    fi
fi
echo "Starting PDViPeR..."
python app.py