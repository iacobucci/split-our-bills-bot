refresh:
	ssh -p 2222 valerio@valerioiacobucci.com git -C '~/source/py/split-our-bills-bot' pull
	ssh -p 2222 valerio@valerioiacobucci.com systemctl --user status split-our-bills-bot
