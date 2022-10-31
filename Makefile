.PHONY: style
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
