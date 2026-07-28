import sys

from storage import record

if len(sys.argv) != 2:
    print('Usage:')
    print('python detect.py "European Robin"')
    quit()

species = sys.argv[1]

record(species)

print(f"Recorded: {species}")