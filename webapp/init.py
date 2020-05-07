import os
import sys

if not os.path.exists("logs"):
    os.mkdir("logs")

if not os.path.exists("../creds.yaml"):
    print("""
    Copy creds.yaml.sample into the top-level directory:

    cp creds.yaml.sample ../creds.yaml

    Fill in the missing fields.
    """)
    sys.exit(-1)
