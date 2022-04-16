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

exclude = set(['.git'])
for root, dirs, files in os.walk('.', topdown=True):
    dirs[:] = [d for d in dirs if d not in exclude]
    print(root)
    print(dirs)
    print(files)
