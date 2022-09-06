.PHONY: style
style:
	@$(exec) black manage.py iris
	@$(exec) isort manage.py iris
