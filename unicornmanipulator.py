import os
import pycorn
import xml.etree.ElementTree as ET
import collections
import numpy

'''
TODO:

'''


class UnicornFile():
    """docstring for UnicornFile"""

    def __init__(self, zip_file_path):
        self.zip_file_path = zip_file_path
        self.filename = zip_file_path.split("\\")[-1][:-4] # to remove .zip
        self.loaded = False
        self.pycorn_file = None
        self.chrom_1_xml = None
        self.logbook = None
        self.blocks = None
        self.curve_data = None
        self.col_xml = None
        self.col_bh = None
        self.col_id = None
        self.col_cv = None

    def load(self):
        if not self.loaded:
            self.getFileData()
            self.getLogbook()
            self.getBlocks()
            self.getAvailableCurves()
            self.getColumnData()
            self.loaded = True
        return self

    def getFileData(self):
        # uses pycorn to extract the Chrom.1.Xml data
        self.pycorn_file = pycorn.pc_uni6(self.zip_file_path)
        self.pycorn_file.load()
        self.chrom_1_xml = ET.fromstring(self.pycorn_file["Chrom.1.Xml"])

    def getColumnData(self):
        # gets data regarding the column dimension. Be careful, not sure if
        # the binary decoding will always work.
        column_binary = self.pycorn_file["ColumnTypeData"]["Xml"]
        column_data = column_binary.decode("utf-8", "ignore").strip()
        column_data = column_data[column_data.index("<"):]
        self.col_xml = ET.fromstring(column_data)

        self.col_bh = float(self.col_xml.find("ColumnType/BedHeight").text)
        self.col_id = float(self.col_xml.find("ColumnType/Hardware/Diameter").text)
        self.col_cv = float(self.chrom_1_xml.find("Curves/Curve/ColumnVolume").text)
        # print(self.col_bh, self.col_id, self.col_cv)

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
        self.logbook = self.chrom_1_xml.findall("EventCurves/EventCurve[@EventCurveType='Logbook']/Events/Event")

    def getAvailableCurves(self):
        # gets a list of all the available curves that can be extracted
        # stores as a dict with the first component of the array storing the file of the curve
        # and the second storing the curve Element object
        # {curvename: [filename, curve_element, [x-data, y-data]]}
        curves = self.chrom_1_xml.findall("Curves/Curve")
        curve_dict = {}
        for curve in curves:
            curve_dict[curve.find("Name").text] = [curve.find("CurvePoints/CurvePoint/BinaryCurvePointsFileName").text, curve, []]
        self.curve_data = curve_dict
        return self.curve_data

    def getCurveData(self, curve_name, x_unit='mL', resize=None):
        # {curvename: [filename, curve_element, [x-data, y-data]]}
        # resturns the [x-data, y-data] and also stores it in the self.curve_data dict

        if self.curve_data is None:
            self.getAvailableCurves()
        elif curve_name not in self.curve_data:
            print(curve_name + " is not a valid curve. please choose from:")
            for name in self.curve_data:
                print("\t" + name)
            return None

        if x_unit not in ['mL', 'CV', 'min']:
            print('not the correct x_unit')
            x_unit = 'mL'

        if x_unit == 'mL':
            x_values = self.pycorn_file[self.curve_data[curve_name][0]]["CoordinateData.Volumes"]

        elif x_unit == 'CV':
            temp = self.pycorn_file[self.curve_data[curve_name][0]]["CoordinateData.Volumes"]
            x_values = [x / self.col_cv for x in temp]

        elif x_unit == "min":
            print(self.pycorn_file[self.curve_data[curve_name][0]].keys())
            x_values = self.pycorn_file[self.curve_data[curve_name][0]]["CoordinateData.Times"]

        else:
            print('This should never happen')
            raise SystemError

        y_values = self.pycorn_file[self.curve_data[curve_name][0]]["CoordinateData.Amplitudes"]

        if resize is None:
            self.curve_data[curve_name][2] = [x_values, y_values]
            return self.curve_data[curve_name][2]
        else:
            resize = int(resize)
            y_values = resizeArr(y_values, resize)
            x_values = numpy.linspace(x_values[0], x_values[-1], resize)
            self.curve_data[curve_name][2] = [x_values, y_values]
            return self.curve_data[curve_name][2]

    def exportCurves(self, curve_list, output_file, resize=None, x_unit='mL'):
        # takes the list of curves to export, name of export file, the risizing amount, and the units to have
        # the x data in, and exports it to the output file, aligned to the x_axis
        curve_data = []
        header_string = ""
        for curve_name in curve_list:
            x_values, y_values = self.getCurveData(curve_name, resize=resize, x_unit=x_unit)

            if curve_data == []:
                header_string += "x-values(%s)" % x_unit
                curve_data.append(x_values)
            elif len(x_values) < len(curve_data[0]) and resize is None:
                # check to see if the newly added data has fewer points. If yes, set that as the new x-axis
                # and downsize all the y-data for the various curves
                curve_data[0] = x_values
                for i in range(1, len(curve_data)):
                    curve_data[i] = resizeArr(curve_data[i], len(x_values))

            header_string += "," + curve_name
            curve_data.append(y_values)

        # print(header_string)
        numpy.savetxt(  output_file,
                        numpy.transpose(curve_data),
                        delimiter=",",
                        header=header_string,
                        comments="",
                        fmt='%.4f')

    def getBlockCurveData(self, block, curve_name, x_unit='mL', resize=None):
        xdata, ydata = self.getCurveData(curve_name, x_unit)
        block_start = float(self.blocks[block][0].find("EventVolume").text)
        block_end = float(self.blocks[block][1].find("EventVolume").text)
        print(block_start, block_end)

        # Might be able to speed up since x-axis is evenly distributed.
        # divide the difference between the last and first value by the number of points
        # and use that to determine indicies where the start and end value would be located
        block_indices = [None, None]
        for i in range(len(xdata)):
            if xdata[i] >= block_start and block_indices[0] is None:
                block_indices[0] = i
            elif xdata[i] >= block_end:
                block_indices[1] = i
                break
        xdata = xdata[block_indices[0]:block_indices[1]]
        ydata = ydata[block_indices[0]:block_indices[1]]
        if resize is not None:
            xdata = resizeArr(xdata, resize)
            ydata = resizeArr(ydata, resize)
        return xdata, ydata

    def exportBlockCurves(self, block, curve_list, output_file, resize=None, x_unit='mL'):
        # takes the list of curves to export, name of export file, the risizing amount, and the units to have
        # the x data in, and exports it to the output file, aligned to the x_axis
        curve_data = []
        header_string = ""
        for curve_name in curve_list:
            x_values, y_values = self.getBlockCurveData(block, curve_name, resize=resize, x_unit=x_unit)

            if curve_data == []:
                header_string += "x-values(%s)" % x_unit
                curve_data.append(x_values)
            elif len(x_values) < len(curve_data[0]) and resize is None:
                # check to see if the newly added data has fewer points. If yes, set that as the new x-axis
                # and downsize all the y-data for the various curves
                curve_data[0] = x_values
                for i in range(1, len(curve_data)):
                    curve_data[i] = resizeArr(curve_data[i], len(x_values))

            header_string += "," + curve_name
            curve_data.append(y_values)

        # print(header_string)
        numpy.savetxt(  output_file,
                        numpy.transpose(curve_data),
                        delimiter=",",
                        header=header_string,
                        comments="",
                        fmt='%.4f')


class CurveManager(dict):
    """docstring for CurveManager"""

    def __init__(self):
        pass

    def add(self, unicorn_file):
        self[unicorn_file.filename] = unicorn_file

    def remove(self, unicorn_file):
        if type(unicorn_file) == str:
            return self.pop(unicorn_file)
        elif type(unicorn_file) == UnicornFile:
            return self.pop(unicorn_file.filename)

####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################


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


def getInputFiles():
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


def resizeArr(arr, size):
    # Downsamples the array by choosing an even number of points accross the range
    new_arr = []
    size = int(size)
    step = (len(arr) - 1) / float((size - 1))
    return [arr[int(i * step)] for i in range(size)]


def main():
    input_files = getInputFiles()
    # print(input_files)
    unicorn_file1 = UnicornFile(input_files[0])
    unicorn_file2 = UnicornFile(input_files[1])
    manager = CurveManager()
    manager.add(unicorn_file1)
    manager.add(unicorn_file2)
    print(manager)
    manager.remove("20200713 Cycle 006 Kiji TD13507 KanCapA Resin Reuse")
    print(manager)

    # unicorn_file.load()
    # unicorn_file.getColumnData()
    # # print(unicorn_file.pycorn_file['Chrom.1_1_True'])
    # keys = unicorn_file.pycorn_file['Chrom.1_1_True'].keys()
    # print(keys)
    # x_data = unicorn_file.pycorn_file['Chrom.1_1_True']['CoordinateData.Volumes']
    # y_data = unicorn_file.pycorn_file['Chrom.1_1_True']['CoordinateData.Amplitudes']

    # unicorn_file.getBlockCurveData('Elution', "UV 1_280")


if __name__ == '__main__':
    main()
    # guiTest()
