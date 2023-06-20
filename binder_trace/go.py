import os 

dir_path = os.path.dirname(os.path.realpath(__file__))


with open(os.path.join(dir_path, "..", "README.md"), "rb") as f:
    long_description = f.read()

print(long_description)