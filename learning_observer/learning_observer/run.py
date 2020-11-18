'''
Helper for console_scripts entry-point


'''
import sys
import os.path

def run():
    print("Running")
    print(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(__file__))
    print(sys.path)
    import main
    print("Imported")
