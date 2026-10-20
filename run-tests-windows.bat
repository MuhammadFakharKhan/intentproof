@echo off
python -m unittest discover -s tests -v
set PYTHONPATH=src
python -m intentproof run examples\failed-ack-scenario.json
