import subprocess
import os
def stylechecker(code):
    with open('output/code.cpp', 'w') as file:
        file.write(code)
    codefile = open('output/code.cpp', 'r')
    for x in codefile:
        code += x
    command = 'cpplint output/code.cpp'
    output = subprocess.getoutput(command)
    os.remove('output/code.cpp')
    return output