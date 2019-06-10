# OpenSurgery - compiler for circuits to lattice surgery

<a href="https://docs.google.com/presentation/d/e/2PACX-1vQlTxLd73cyVqj9s2H7da_1lRfwQQmVVVxOEtrPmXSMwoFdwRayXYWexFPZyCMU1-gTsS1bOxJknmDZ/pub?start=true&loop=false&delayms=3000" target="-blank">A presentation about OpenSurgery</a>

For the moment is uses the SK compiler from https://github.com/cryptogoth/skc-python . I modified the code to work with python3

* Make a virtualenv in the root: virtualenv venv (or any other method that works)
* source venv/bin/activate
* pip install cirq openfermion openfermioncirq
* (maybe even) export PYTHONPATH=.
* mkdir -p pickles/su2 and Call python manage/generate_su2.py to generate necessary files for SKC in the folder pickles
* python main.py for OpenSurgery
