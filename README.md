# OpenSurgery - compiler for circuits to lattice surgery

For the moment is uses the SK compiler from https://github.com/cryptogoth/skc-python . I modified the code to work with python3

* Make a virtualenv in the root: virtualenv venv (or any other method that works)
* source venv/bin/activate
* pip install cirq openfermion openfermioncirq
* (maybe even) export PYTHONPATH=.
* mkdir -p pickles/su2 and Call python manage/generate_su2.py to generate necessary files for SKC in the folder pickles
* python main.py for OpenSurgery