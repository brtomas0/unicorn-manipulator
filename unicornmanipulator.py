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
        self.blocks = None

    def load(self):
        self.getFileData()
        self.getLogbook()
        self.getBlocks()
        self.getAvailableCurves()

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

        blocks_dict = {}
        block_stack = collections.deque()

        for element in self.logbook:
            if element.attrib["EventSubType"] == "BlockStart":
                block_stack.append(element)
                # text = element.find("EventText").text
                # print(getFollowingWord(text, "Phase", "(Issued)").strip())
            elif element.attrib["EventSubType"] == "BlockEnd":
                start = block_stack.pop()
                phase_name = getFollowingWord(start.find("EventText").text, "Phase", "(Issued)").strip()
                if phase_name == "":
                    # for the start, where there is no phase in the text
                    phase_name = "Method"
                blocks_dict[phase_name] = (start, element)

        self.blocks = blocks_dict
        return blocks_dict

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
        self.curves_and_files = curve_dict
        return curve_dict


def getFollowingWord(string, keyword, end=" "):
    # returns the string following the keyword and ending at the end word
    # without the end parameter, will just get the word only
    if keyword not in string:
        return ""

    start_i = string.index(keyword) + len(keyword)
    end_i = len(string) - 1
    if end in string:
        end_i = string[start_i:].index(end) + start_i

    return string[start_i:end_i].replace(".", "")


def getFiles():
    input_folder = os.path.dirname(os.path.dirname(__file__)) + "\\unicorn-manipulator-data\\input"
    input_files = os.listdir(input_folder)
    return [input_folder + "\\" + i for i in input_files]


def main():
    input_files = getFiles()
    # print(input_files)
    unicorn_file = UnicornFile(input_files[0])
    unicorn_file.load()
    print(unicorn_file.blocks.keys())


if __name__ == '__main__':
    main()
