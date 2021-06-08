default:
	python setup.py sdist bdist_wheel

clean:
	rm -rf __pycache__ *.py[oc] build *.egg-info dist MANIFEST

test:
	pytest test.py
