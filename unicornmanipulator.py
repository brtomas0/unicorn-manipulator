import os
import datetime
import pycorn
import xml.etree.ElementTree as ET
import collections
from scipy import signal
import numpy
import appJar

'''
TODO:
    Figure out how to convert x-axis / extract data from the files
'''


class UnicornFile():
    """docstring for UnicornFile"""

    def __init__(self, zip_file_path):
        self.zip_file_path = zip_file_path
        self.file_name = zip_file_path.split("\\")[-1][:-4] # to remove .zip
        self.not_loaded = True
        self.pycorn_file = None
        self.chrom_1_tree = None
        self.logbook = None
        self.blocks = None
        self.curve_names = None

    def load(self):
        if self.not_loaded:
            self.getFileData()
            self.getLogbook()
            self.getBlocks()
            self.getAvailableCurves()
        return self

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
        # {curvename: [filename, curve_element, [x-data, y-data]]}
        curves = self.chrom_1_tree.findall("Curves/Curve")
        curve_dict = {}
        for curve in curves:
            curve_dict[curve.find("Name").text] = [curve.find("CurvePoints/CurvePoint/BinaryCurvePointsFileName").text, curve, []]
        self.curve_names = curve_dict
        return self.curve_names

    def getCurveData(self, curve_name, resample_size=None):
        if self.curve_names is None:
            self.getAvailableCurves()
        elif curve_name not in self.curve_names:
            print(curve_name + " is not a valid curve. please choose from:")
            for name in self.curve_names:
                print("\t" + name)
            return None

        x_values = self.pycorn_file[self.curve_names[curve_name][0]]["CoordinateData.Volumes"]
        y_values = self.pycorn_file[self.curve_names[curve_name][0]]["CoordinateData.Amplitudes"]
        # print(len(x_values))

        if resample_size is None:
            self.curve_names[curve_name][2] = [x_values, y_values]
            return self.curve_names[curve_name][2]
        else:
            resample_size = int(resample_size)
            y_values = signal.resample(y_values, resample_size)
            x_values = numpy.linspace(x_values[0], x_values[-1], resample_size)
            self.curve_names[curve_name][2] = [x_values, y_values]
            return self.curve_names[curve_name][2]

    def exportCurves(self, curve_list, output_file, resample_size=None):
        curve_data = []
        header_string = ""
        for curve_name in curve_list:
            vals = self.getCurveData(curve_name, resample_size)

            if curve_data == []:
                header_string += "x-values"
                curve_data.append(vals[0])
            elif len(vals[0]) < len(curve_data[0]) and resample_size is None:
                # check to see if the newly added data has fewer points. If yes, set that as the new x-axis
                # and downsize all the y-data for the various curves
                curve_data[0] = vals[0]
                for i in range(1, len(curve_data)):
                    curve_data[i] = signal.resample(curve_data[i], len(vals[0]))

            header_string += "," + curve_name
            curve_data.append(vals[1])

        # print(header_string)
        numpy.savetxt(  output_file,
                        numpy.transpose(curve_data),
                        delimiter=",",
                        header=header_string,
                        comments="",
                        fmt='%.4f')


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
    print(input_folder)
    input_files = os.listdir(input_folder)
    return [input_folder + "\\" + i for i in input_files]


def getOutputFolder(out_folder_name):
    root_dir = os.path.dirname(os.path.dirname(__file__))
    if "unicorn-manipulator-out" not in os.listdir(root_dir):
        os.mkdir(root_dir + "\\unicorn-manipulator-out")
    if out_folder_name not in os.listdir(root_dir + "\\unicorn-manipulator-out"):
        os.mkdir(root_dir + "\\unicorn-manipulator-out\\" + out_folder_name)
    return root_dir + "\\unicorn-manipulator-out\\" + out_folder_name


def buttonMakeCSV(unicorn_file):
    # curve_list = app.getAllListBoxes()["curve_list"]
    curve_list = [x for x in app.getAllCheckBoxes() if app.getAllCheckBoxes()[x] is True]
    unicorn_file.exportCurves(curve_list, output_folder + "\\curve_out.csv", app.getEntry("resample_size"))


def main():
    input_files = getFiles()
    # print(input_files)
    unicorn_file = UnicornFile(input_files[0])
    unicorn_file.load()
    global output_folder
    output_folder = getOutputFolder("out test")

    global app
    app = appJar.gui("Unicorn Curve Exporter")
    app.startFrame("files", row=0, column=0)
    app.setStretch("COLUMN")
    app.addListBox("file_list", [x.split('\\')[-1] for x in input_files])
    # app.setFrameWidth("files",300)
    app.setListBoxWidth("file_list", 50)
    app.setListBoxMulti("file_list", True)
    app.stopFrame()

    app.startFrame("curves", row=0, column=1)
    for curve in unicorn_file.curve_names:
        app.addCheckBox(curve)
    # app.addListBox("curve_list", unicorn_file.curve_names)
    # app.setListBoxMulti("curve_list", True)
    app.stopFrame()

    app.startFrame("data_export", row=0, column=2)
    app.setStretch("COLUMN")

    app.addMessage("M1", "Select number of points to downsample to:")
    app.addNumericEntry("resample_size")
    app.addNamedButton("Make csv", unicorn_file, buttonMakeCSV)
    app.stopFrame()

    app.go()

    # checked_curves = [x for x in app.getAllCheckBoxes() if app.getAllCheckBoxes()[x] == True]
    # print(unicorn_file.curve_names.keys())
    # unicorn_file.getCurveData("pH ", 2000)
    # unicorn_file.exportCurves(["UV 1_280", "UV 2_254", "Cond", "pH", "DeltaC pressure"], "curve_out.csv", 2000)
    # print([x.find("EventText").text for x in unicorn_file.blocks["CIP"]])


if __name__ == '__main__':
    main()
    # guiTest()
