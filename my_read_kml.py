import xml.etree.ElementTree as et
import tempfile
import zipfile
import pathlib

import argparse

def main(
        input_kml: str = "postoffices_mod.kmz",
) -> None:

    if input_kml.endswith(".zip") or input_kml.endswith(".kmz"):
        with tempfile.TemporaryDirectory() as td:
            tmp_dir_name = pathlib.Path(td)
            with zipfile.ZipFile(input_kml) as zf:
                files = zf.namelist()
                if len(files)>1:
                    print("more than 1 files in given zip")
                    print(files)
                    return
                zf.extract(files[0], str(tmp_dir_name))
                tree = et.parse(tmp_dir_name/files[0])
    else:
        tree = et.parse(input_kml)
    root = tree.getroot()

    coordinates = {}
    for folder in root[0]:
        if "Folder" not in folder.tag:
            continue
        for placemark in folder:
            if "Placemark" in placemark.tag:
                for point in placemark:
                    if "Point" in point.tag:
                        placename = placemark[0].text.strip()
                        x, y, z = point[0].text.split(",")
                        x = float(x)
                        y = float(y)
                        coordinates[placename] = (x, y)
                        #print(placename, x, y)
                        
    return coordinates

if __name__=="__main__":

    main()
