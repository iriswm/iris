.PHONY: style
makemessages:
	@$(exec) django-admin makemessages -l es --no-obsolete --no-location
compilemessages:
	@$(exec) django-admin compilemessages -l es
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
