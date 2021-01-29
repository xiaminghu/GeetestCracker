rm -rf build/ dist/ geecracker.egg-info/
python setup.py sdist bdist_wheel
twine upload dist/*