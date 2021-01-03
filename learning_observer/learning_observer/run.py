'''Helper for console_scripts entry-point

In order to have this work as a command line utility installed with
pip, we need a way to run this which is a function, rather than a
script.
'''
import sys
import os.path

def run():
    print("Running")
    print(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(__file__))
    print(sys.path)
    import learning_observer.main
    print("Imported")
