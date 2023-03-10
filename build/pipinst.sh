#!/bin/bash
pkgs="flask flask-login flask-sqlalchemy flask-sessionstore flask-session-captcha dhooks sqlalchemy python-dotenv zenora"

if ! command -v pip > /dev/null
then
	echo "Pip not found..."
	if ! command -v python3 > /dev/null
		then
			echo "Python3 Executable not found, giving up"
			exit
	else
			python3 -m pip install ${pkgs}
	fi
	exit
else
	pip install ${pkgs}
fi
