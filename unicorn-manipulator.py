import os
import datetime
import pycorn
import xml.etree.ElementTree as ET
import collections


class UnicornFile():
    """docstring for UnicornFile"""

    def __init__(self, zip_file_path):
        self.zip_file_path = zip_file_path
        self.pycorn_file = None
        self.chrom_1_tree = None
        self.logbook = None

    def load(self):
        self.getFileData()

    def getFileData(self):
        # uses pycorn to extract the Chrom.1.Xml data
        self.pycorn_file = pycorn.pc_uni6(self.zip_file_path)
        self.pycorn_file.load()
        self.chrom_1_tree = ET.fromstring(self.pycorn_file["Chrom.1.Xml"])

    def getBlocks(self):
        # logbook entries is a list of xml.etree.ElementTree.Elements
        # matches up blocks appropriately. May need to implement a catch
        # for if there aren't enough block ends. But it shouldn't really happen...
        if self.logbook is None:
            self.getLogbook()

        block_pairs = []
        block_stack = collections.deque()

        for element in self.logbook:
            if element.attrib["EventSubType"] == "BlockStart":
                block_stack.append(element)
            elif element.attrib["EventSubType"] == "BlockEnd":
                block_pairs.append((block_stack.pop(), element))

        return block_pairs

    def getLogbook(self):
        self.logbook = self.chrom_1_tree.findall("EventCurves/EventCurve[@EventCurveType='Logbook']/Events/Event")

    def getAvailableCurves(self):
        # gets a list of all the available curves that can be extracted
        # stores as a dict with the first component of the array storing the file of the curve
        # and the second storing the curve Element object
        # {curvename: (filename, curve_element)}
        curves = self.chrom_1_tree.findall("Curves/Curve")
        curve_dict = {}
        for curve in curves:
            curve_dict[curve.find("Name").text] = (curve.find("CurvePoints/CurvePoint/BinaryCurvePointsFileName").text, curve)
        return curve_dict


def main():
    unicorn_file = UnicornFile(filepath)
    unicorn_file.load()
    unicorn_file.getLogbook()
    blocks = unicorn_file.getBlocks()
    # [print(x[0][0].text, x[1][0].text, x[0][2].text) for x in blocks]
    print(unicorn_file.getAvailableCurves())


if __name__ == '__main__':
    main()
