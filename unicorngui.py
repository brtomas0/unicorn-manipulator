import unicornmanipulator
import appJar
import os

app = appJar.gui("Unicorn Curve Exporter")



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


def exportFileCSV(unicorn_file):
    curve_list = [x for x in app.getAllCheckBoxes() if app.getAllCheckBoxes()[x] is True]
    out_file_name = output_folder + "\\" + unicorn_file.file_name + ".csv"
    unicorn_file.exportCurves(curve_list, out_file_name, app.getEntry("resample_size"))
    # print(unicorn_file.file_name)


def buttonMakeAllCSV():
    # curve_list = app.getAllListBoxes()["curve_list"]
    for file in app.getListBox("file_list"):
        print(file)
        exportFileCSV(unicornfile_list[file].load())


def makeFileBox():
    app.setStretch("COLUMN")
    app.addListBox("file_list", [unicornfile_list[x].file_name for x in unicornfile_list])
    # app.setFrameWidth("files",300)
    app.setListBoxWidth("file_list", 50)
    app.setListBoxMulti("file_list", True)


def makeCurveCheckboxes(sample_file):
    sample_file.load()
    for curve_name in sample_file.curve_names:
        app.addCheckBox(curve_name)
    # app.addListBox("curve_list", unicorn_file.curves)
    # app.setListBoxMulti("curve_list", True)


def getUnicornFiles():
    unicornfile_list = {}
    for file in input_files:
        unicorn_file = unicornmanipulator.UnicornFile(file)
        unicornfile_list[unicorn_file.file_name] = unicorn_file
        # print(file, unicorn_file.file_name)

    return unicornfile_list


def main():
    global unicornfile_list
    global input_files
    global output_folder

    input_files = getInputFiles()
    output_folder = getOutputFolder("out test")
    unicornfile_list = getUnicornFiles()
    # [print(x.zip_file_path) for x in unicornfile_list]

    app.startFrame("files", row=0, column=0)
    makeFileBox()
    app.stopFrame()

    app.startFrame("curves", row=0, column=1)
    makeCurveCheckboxes(next(iter(unicornfile_list.values())))
    app.stopFrame()

    app.startFrame("data_export", row=0, column=2)
    app.setStretch("COLUMN")

    app.addMessage("M1", "Select number of points to downsample to:")
    app.addNumericEntry("resample_size")
    app.addButton("Export all csv's", buttonMakeAllCSV)
    app.stopFrame()

    app.go()


if __name__ == '__main__':
    main()
