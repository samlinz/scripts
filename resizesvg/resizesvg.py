import argparse
import xml.etree.ElementTree as ET
import logging
import sys
from datetime import datetime
from os import path

if not __name__ == "__main__":
    sys.stderr.write("File must be run as the main module")

# Logging
FORMAT = '%(asctime)s %(levelname)s %(message)s'
log = logging.getLogger()
log.setLevel(logging.DEBUG)

sh = logging.StreamHandler(stream=sys.stdout)
sf = logging.Formatter(fmt=FORMAT)
sh.setFormatter(sf)
log.addHandler(sh)

# Arguments
parser = argparse.ArgumentParser(prog="SVG resizer")
parser.add_argument("file", help="SVG file")
parser.add_argument("w", help="New width")
parser.add_argument("h", help="New height")
parser.add_argument("-o", "--output", help="Output file name")
parser.add_argument("-r", "--round", help="max digits to round to",
                    action="store", default=2, type=int)
parser.add_argument("-s", "--stroke", help="force new stroke width",
                    action="store", default=None, type=int)
args = parser.parse_args()

FILE = args.file
OUTFILE = args.output
W = int(args.w)
H = int(args.h)
ROUND = args.round
STROKE = args.stroke

log.debug("Starting")

if not path.exists(FILE):
    log.error("File does not exists")
    exit(1)

outfile = OUTFILE if OUTFILE is not None else "{}_resized.svg".format(
    path.splitext(FILE)[0])

if path.exists(outfile):
    log.error("Outfile exists already")
    exit(1)

tree = ET.parse(FILE)
root = tree.getroot()

if "svg" not in root.tag or "width" not in root.attrib or "height" not in root.attrib:
    log.error("Invalid SVG")
    exit(1)

ROOT_WIDTH = int(root.attrib["width"])
ROOT_HEIGHT = int(root.attrib["height"])

# Calculate scaling ratio
RATIO_WIDTH = W / ROOT_WIDTH
RATIO_HEIGHT = H / ROOT_HEIGHT

log.debug("W ratio {}".format(RATIO_WIDTH))
log.debug("H ratio {}".format(RATIO_HEIGHT))


def _set_new(elem, attr_name, ratio):
    old_val_str = elem.attrib[attr_name]
    old_val = float(old_val_str)
    new_val = old_val * ratio
    if '.' in old_val_str or ',' in old_val_str:
        new_val = "{0:.2f}".format(round(new_val, 2))
    else:
        new_val = round(new_val)
    elem.set(attr_name,  str(new_val))
    log.debug("Resizing '{}' from '{}' to '{}'".format(
        attr_name, old_val, new_val))


def _resize_element(elem):
    if elem is None:
        return
    tag_name = elem.tag
    log.info("Processing element {}".format(tag_name))
    if "x" in elem.attrib:              _set_new(elem, "x",         RATIO_WIDTH)
    if "cx" in elem.attrib:             _set_new(elem, "cx",        RATIO_WIDTH)
    if "x1" in elem.attrib:             _set_new(elem, "x1",        RATIO_WIDTH)
    if "x2" in elem.attrib:             _set_new(elem, "x2",        RATIO_WIDTH)
    if "y" in elem.attrib:              _set_new(elem, "y",         RATIO_HEIGHT)
    if "cy" in elem.attrib:             _set_new(elem, "cy",        RATIO_HEIGHT)
    if "y1" in elem.attrib:             _set_new(elem, "y1",        RATIO_HEIGHT)
    if "y2" in elem.attrib:             _set_new(elem, "y2",        RATIO_HEIGHT)
    if "width" in elem.attrib:          _set_new(elem, "width",     RATIO_WIDTH)
    if "height" in elem.attrib:         _set_new(elem, "height",    RATIO_HEIGHT)
    if "stroke-width" in elem.attrib:   _set_new(elem, "stroke-width",  RATIO_WIDTH)
    if "r" in elem.attrib:              _set_new(elem, "r", RATIO_WIDTH)
    # Recurse
    for child in elem:
        _resize_element(child)


_resize_element(root)
log.info("Done resizing")

# Flush to a new file
log.info("Writing into {}".format(outfile))
tree.write(outfile)
with open(outfile, "r+") as f:
    text = f.read()
    f.seek(0)
    f.write(text.replace("ns0:", "").replace(":ns0", ""))
    f.truncate()
log.info("All done")
