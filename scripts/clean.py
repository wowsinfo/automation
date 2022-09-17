import os, glob

for file in glob.glob('*.json'):
    if 'package' in file:
        continue
    os.remove(file)