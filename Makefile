.PHONY: makemessages
makemessages:
	@$(exec) django-admin makemessages -l es --no-obsolete --no-location
.PHONY: compilemessages
compilemessages:
	@$(exec) django-admin compilemessages -l es
.PHONY: style
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
