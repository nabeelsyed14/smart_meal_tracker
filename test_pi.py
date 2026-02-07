import os
import platform

print("Running on:", platform.node())
print("OS:", platform.system())
print("CPU info:")
os.system("uname -a")
