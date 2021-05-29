import os
import sys
import subprocess

path = 'tests/input/'
result_path = 'tests.txt'

print(os.getcwd() + '/' + path)

if os.path.exists(result_path):
    print('File tests.txt already exists, rewrite? (y or n)')
    inpt = input()
    answer = ''
    try:
        answer = str(inpt)
    except:
        print('Wrong input')
        sys.exit(2)
    if answer == 'y':
        file = open(result_path, 'w')
        file.close()


for filename in os.listdir(os.getcwd() + '/' + path):
    if filename.endswith(".txt"):
        call = "python3.9 tspmt.py -i " + path + filename + " -t"
        print(call)
        subprocess.call(call, shell=True)

file = open('tests.txt', 'r')
print("\nResults:")
for line in file:
    print(line.strip())
