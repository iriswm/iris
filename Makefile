.PHONY: style
makemessages:
	@$(exec) ./manage.py makemessages -l es --no-obsolete --no-location
compilemessages:
	@$(exec) ./manage.py compilemessages -l es
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
