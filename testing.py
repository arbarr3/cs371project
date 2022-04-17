import json
import os

list = {
    "rscris2": "foo",
    "aberra2": "bar"
}

path = os.getcwd()
path = os.path.join(path, "users.json")

with open(path, 'w') as fout:
    json.dump(list , fout)

with open(path, "r") as read_file:
    data = json.load(read_file)

passwordTest = "foo"
userTest = "aberra2"

for key, value in data.items():
    if key == userTest and value == passwordTest:
        print("User " + key + " with password " + value + " was found!")


data = ["MKDIR", "rscris2", "weeee"]
args =[]
for i in range (1, len(data)):
    args.append(data[i])

print(args)
print(args.pop())

dirList = []
exclude = set(['.git'])
for root, dirs, files in os.walk('.', topdown=True):
    dirs[:] = [d for d in dirs if d not in exclude]
    
    contains = []

    paths = root.split("\\")
    subFolder = paths[len(paths)-1] # This logic needs to be used to determine how deep to iterate through looking for subfolders
    print(subFolder)
    print(dirs)
    print(files)
    
    for d in dirs:
        subDir = {d}
        contains.append(subDir)

    for f in files:
        contains.append(f)

    dict = {root: contains}

    if subFolder == ".":
        dirList.append(dict)
    else:
        print("I need to traverse the dirList and make contains the values where the key is subFolder")

print(dirList)
