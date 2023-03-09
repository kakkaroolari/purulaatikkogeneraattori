from pathlib import Path
import json
import numpy as np
from helpers import *


def load_varaukset(filename):
    # Opening JSON file
    f = open(filename)
    data = json.load(f)
    # Iterating through the json list
    for i in data:
        print(i)
    # Closing file
    f.close()
    return data


def main(name):
    varaukset = load_varaukset(name)
    #temp = np.array(varaukset[0]["Coordinates"])
    temp = Point3.FromArr(varaukset[0]["Coordinates"])
    print('Varaus: %s' % (temp))
    # basepoint 39d
    O = Point3(-1843.66, -2106.51, 0)
    X = Point3(0.777, 0.629, 0)
    Y = Point3(-0.629, 0.777, 0)
    # basepoint -39d
    O = Point3(-1843.66, -2106.51, 0)
    X = Point3(0.777, -0.629, 0)
    Y = Point3(0.629, 0.777, 0)
    # basepoint -39d, +compass
    O = Point3(1843.66, 2106.51, 0)
    X = Point3(0.777, -0.629, 0)
    Y = Point3(0.629, 0.777, 0)
    coordinate_system = TransformationPlane(O, X, Y)
    transform = Transformer(coordinate_system)
    #corner_local = transform.convertToLocal(corner_tri)
    in_world = transform.convertToGlobal([temp])
    print('in global: %s' % (in_world))

if __name__ == "__main__":
    #f = open("C:\\Users\\fivanl\\OneDrive - Sweco AB\\Documents\\20078_ele_basepoint\\ARK_Origo_Element_v2_varauslista (1).json")
    #path = Path("C:\\Users\\fivanl\\OneDrive - Sweco AB\\Documents\\20078_ele_basepoint\\ARK_Origo_Element_v2_varauslista (1).json")
    path = Path("ARK_Origo_Element_v2_varauslista (1).json")
    if not path.is_file():
        print("File not found: " + path)
        exit()
    main(path)