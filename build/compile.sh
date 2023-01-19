#!/bin/bash
# Dunno Why you would compile this, but good for you ig
# This stuff is being compiled using Pyinstaller. You can uninstall it at any time using pip uninstall pyinstaller
# Do whatever with this
# But run this over "make build"

if ! command -v pip > /dev/null
then
	echo "Pip not found..."
	if ! command -v python3 > /dev/null
		then
			echo "Python3 Executable not found, giving up"
			exit
	else
			python3 -m pip install pyinstaller
	fi
else
	pip install pyinstaller
fi
pyinstaller --onefile ./app.py
mv ./dist/app ./compiled.out
chmod 777 ./compiled.out
rm -rfv ./build/app