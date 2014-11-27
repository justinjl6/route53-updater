#!/bin/bash

SUBMODULES='
boto
'

SELF=$( readlink -e "${0}" )
DIRNAME=$( dirname "${SELF}" )

echo -e "Syncing submodules...\n"
cd "${DIRNAME}"
git submodule init
git submodule update
git submodule status

for SUBMODULE in ${SUBMODULES}; do
    cd "${DIRNAME}/${SUBMODULE}"
    git checkout master
    git pull
done

echo

