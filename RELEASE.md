# How to release a new version

## System Setup
Create a virtualenv and install the requirements
available at requirements/requirements-packaging.txt

```
pip install -r requirements/requirements-packaging.txt
```

Then, you'll need to configure your PyPI user account in your system, as described
[here](https://packaging.python.org/distributing/#uploading-your-project-to-pypi).

## Release procedure

After you have successfully made and tested changes for this project, do the following:

1. Update the necessary release information in `setup.py` such as: version number and
download link.
2. Commit all changes and create a tag `git tag -a '0.1.2' -m 'Small documentation adjustments'`.
3. Push to origin `git push --tags`.
4. Create distribution `python setup.py sdist bdist_wheel`.
5. Upload distribution `twine upload dist/*`.
