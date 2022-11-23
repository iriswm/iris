.PHONY: style
makemessages:
	@$(exec) ./manage.py makemessages --all -x en --no-obsolete
compilemessages:
	@$(exec) ./manage.py compilemessages -x en
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
