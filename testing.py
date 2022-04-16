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
