import subprocess

# contains the code to test the spidey.py file, currently unimplemented

# the test values for phase 1
testUrl = 'https://cse.hkust.edu.hk/'
testTarget = 10

# run the spidey.py file with the test values
subprocess.run(['python3', 'spidey.py', testUrl, testTarget])