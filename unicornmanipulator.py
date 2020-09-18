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

        if resize is not None:
            y_values = resizeArr(y_values, resize)
            x_values = resizeArr(x_values, resize)

        self.curve_data[curve_name][2] = [x_values, y_values]
        return x_values, y_values

    def combineCurves(self, curve_list, x_unit='mL', resize=None):
        # takes the list of curves to export, name of export file, the risizing amount, and the units to have
        # the x data in, and exports it to the output file, aligned to the x_axis
        curve_data = []
        for curve_name in curve_list:
            x_values, y_values = self.getCurveData(curve_name, x_unit, resize)

            if curve_data == []:
                curve_data.append(x_values)
            elif len(x_values) < len(curve_data[0]):
                # check to see if the newly added data has fewer points. If yes, set that as the new x-axis
                # and downsize all the y-data for the various curves
                curve_data[0] = x_values
                for i in range(1, len(curve_data)):
                    curve_data[i] = resizeArr(curve_data[i], len(x_values))

            # header_string += "," + curve_name
            curve_data.append(y_values)
            curve_data[0] = [x - curve_data[0][0] for x in curve_data[0]]

        return curve_data

    def combineBlockCurves(self, block, curve_list, x_unit='mL', resize=None):
        # curve data containes [x-axis, y-axis1, y-axis2, etc]
        curve_data = self.combineCurves(curve_list, x_unit)
        block_start = float(self.blocks[block][0].find("EventVolume").text)
        block_end = float(self.blocks[block][1].find("EventVolume").text)

        # Might be able to speed up since x-axis is evenly distributed.
        # divide the difference between the last and first value by the number of points
        # and use that to determine indicies where the start and end value would be located
        block_indices = [None, None]
        for i in range(len(curve_data[0])):
            if curve_data[0][i] >= block_start and block_indices[0] is None:
                block_indices[0] = i
            elif curve_data[0][i] >= block_end:
                block_indices[1] = i
                break

        for i, data in enumerate(curve_data):
            curve_data[i] = resizeArr(data[block_indices[0]:block_indices[1]], resize)

        curve_data[0] = [x - curve_data[0][0] for x in curve_data[0]]

        return curve_data

    def exportCurves(self, curve_list, output_file, x_unit='mL', resize=None):
        # takes the list of curves to export, name of export file, the risizing amount, and the units to have
        # the x data in, and exports it to the output file, aligned to the x_axis
        header_string = "x-values (%s)," % x_unit + ",".join(curve_list)
        curve_data = self.combineCurves(curve_list, x_unit, resize)

        # print(header_string)
        self.saveCurves(output_file, curve_data, header_string)

    def exportBlockCurves(self, block, curve_list, output_file, x_unit='mL', resize=None):
        # takes the list of curves to export, name of export file, the risizing amount, and the units to have
        # the x data in, and exports it to the output file, aligned to the x_axis
        curve_data = self.combineBlockCurves(block, curve_list, x_unit, resize)
        header_string = "x-values (%s)," % x_unit + ",".join(curve_list)
        self.saveCurves(output_file, curve_data, header_string)

    def saveCurves(self, output_file, curve_data, header_string):
        # saves data assuming curve_data format of [x-axis, y-axis1, y-axis2, etc]
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
        self[unicorn_file.filename]

    def remove(self, unicorn_file):
        if type(unicorn_file) == str:
            return self.pop(unicorn_file)
        elif type(unicorn_file) == UnicornFile:
            return self.pop(unicorn_file.filename)

    def loadAllCurves(self):
        for key in self:
            self[key].load()

    def alignCurves(self, curve_list, output_file):
        self.loadAllCurves()
        all_data = []
        final_data = []
        for key in self:
            curve_data = self[key].combineCurves(curve_list, x_unit='mL', resize=None)
            all_data += curve_data

        # Look for the x axis that goes for the longest, and use that to make a new x-axis
        max_x = max([all_data[i][-1] for i in range(0, len(all_data), len(curve_list) + 1)])
        max_len = max([len(all_data[i]) for i in range(0, len(all_data), len(curve_list) + 1)])
        print(max_x, max_len)
        x_data = [x * max_x / max_len for x in range(0, max_len)]
        final_data.append(x_data)

        old_xdata = None
        for i, data in enumerate(all_data):
            # print(i, (len(curve_list) + 1), i % (len(curve_list) + 1))
            if i % (len(curve_list) + 1) == 0:
                # will skip the x_data lists that was merged into the all_data
                old_xdata = data
                continue
            else:
                final_data.append(resizeYCoord(old_xdata, data, x_data))

        header_string = "x-values (mL)," + ",".join([f"{curve}\\{key}" for key in self for curve in curve_list])
        print(len(final_data), len(header_string))
        [print(len(x)) for x in final_data]

        numpy.savetxt(  output_file,
                        numpy.transpose(final_data),
                        delimiter=",",
                        header=header_string,
                        comments="",
                        fmt='%s')

    def alignBlockCurves(self, block, curve_list, output_file):
        self.loadAllCurves()
        all_data = []
        final_data = []
        for key in self:
            curve_data = self[key].combineBlockCurves(block, curve_list, x_unit='mL', resize=None)
            all_data += curve_data

        # Look for the x axis that goes for the longest, and use that to make a new x-axis
        max_x = max([all_data[i][-1] for i in range(0, len(all_data), len(curve_list) + 1)])
        max_len = max([len(all_data[i]) for i in range(0, len(all_data), len(curve_list) + 1)])
        print(max_x, max_len)
        x_data = [x * max_x / max_len for x in range(0, max_len)]
        final_data.append(x_data)

        old_xdata = None
        for i, data in enumerate(all_data):
            # print(i, (len(curve_list) + 1), i % (len(curve_list) + 1))
            if i % (len(curve_list) + 1) == 0:
                # will skip the x_data lists that was merged into the all_data
                old_xdata = data
                continue
            else:
                final_data.append(resizeYCoord(old_xdata, data, x_data))

        header_string = "x-values (mL)," + ",".join([f"{curve}\\{key}" for key in self for curve in curve_list])
        print(len(final_data), len(header_string))
        [print(len(x)) for x in final_data]

        numpy.savetxt(  output_file,
                        numpy.transpose(final_data),
                        delimiter=",",
                        header=header_string,
                        comments="",
                        fmt='%s')


####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################


def resizeYCoord(xdata1, ydata1, xdata2):
    # Will use linear interpolation to project data1 onto data2 x coordinate
    i2 = 0
    ydata2 = ["" for _ in range(len(xdata2))]
    for i1 in range(1, len(xdata1)):
        if xdata1[i1] == xdata2[i2]:
            ydata2[i2] = ydata1[i1]
            i2 += 1
        elif xdata1[i1] > xdata2[i2]:
            if (xdata1[i1] - xdata1[i1 - 1]) == 0:
                # if multiple y values are taken for the same x value, skip
                continue
            else:
                # Add multiple points using the same 2 points if sampling happens
                # wuick enough
                x0 = xdata1[i1 - 1]
                y0 = ydata1[i1 - 1]
                x1 = xdata1[i1]
                y1 = ydata1[i1]
                while xdata2[i2] < xdata1[i1]:
                    # print(xdata2[i2], xdata1[i1])
                    ydata2[i2] = y0 + (xdata2[i2] - x0) * (y1 - y0) / (x1 - x0)
                    i2 += 1
                    if i2 >= len(xdata2):
                        break

        # if data1 > data2, then it'll stop projecting
        if i2 >= len(xdata2):
            break
    return ydata2


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
    if type(size) is not int:
        try:
            size = int(size)
        except:
            return arr
    if len(arr) == size:
        return arr

    new_arr = []
    step = (len(arr) - 1) / float((size - 1))
    return [arr[int(i * step)] for i in range(size)]


def foo():
    return [1, 2, 3, 4]


def main():
    input_files = getInputFiles()
    # print(input_files)
    unicorn_file1 = UnicornFile(input_files[0])
    unicorn_file2 = UnicornFile(input_files[1])
    unicorn_file3 = UnicornFile(input_files[2])
    manager = CurveManager()
    manager.add(unicorn_file1)
    manager.add(unicorn_file2)
    manager.add(unicorn_file3)
    print(manager)
    manager.alignBlockCurves("Elution", ["UV 1_280", "pH"], getOutputFolder("test") + "\\test.csv")

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
