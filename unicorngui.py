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
    resize = app.getEntry("resample_size")
    x_unit = app.getRadioButton("x unit")
    unicorn_file.exportCurves(curve_list, out_file_name, resize, x_unit)
    # print(unicorn_file.file_name)


def buttonMakeAllCSV():
    # curve_list = app.getAllListBoxes()["curve_list"]
    for file in app.getListBox("file_list"):
        print(file)
        exportFileCSV(unicornfile_list[file].load())


def makeFileBox():
    app.setStretch("both")
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


def makePhaseFrame():
    app.setStretch("column")
    app.addButton("Update Phases", displayPhases)

    app.setStretch("column")
    app.setInPadding([0, 10])
    app.addLabel("PL1", "Phases in all methods:")
    app.addListBox("similar phases")
    app.addLabel("PL2", "Phases not in all methods:")
    app.addListBox("different phases")


def getUnicornFiles():
    unicornfile_list = {}
    for file in input_files:
        unicorn_file = unicornmanipulator.UnicornFile(file)
        unicornfile_list[unicorn_file.file_name] = unicorn_file
        # print(file, unicorn_file.file_name)

    return unicornfile_list


def curveOverlay():
    # app.addLabel("test")
    pass


def displayPhases():
    # phase_list = {}
    sim_phase_set = set()
    dif_phase_set = set()
    ordered_blocks = []
    for file in app.getListBox("file_list"):
        unicornfile_list[file].load()
        temp_set = set(unicornfile_list[file].blocks)
        if len(sim_phase_set) == 0:
            sim_phase_set = temp_set
            ordered_blocks = unicornfile_list[file].blocks
        else:
            dif_phase_set |= (sim_phase_set ^ temp_set )
            sim_phase_set &= temp_set
        # for block in unicornfile_list[file].blocks:
        #     phase_list[block] = None
        #     print(block)

    app.updateListBox("similar phases", [x for x in ordered_blocks if x in sim_phase_set])
    app.updateListBox("different phases", dif_phase_set)
    # app.updateListBox("similar phases", phase_list.keys())


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

    app.startFrame("phases", row=0, column=1)
    makePhaseFrame()
    app.stopFrame()

    app.startFrame("curves", row=0, column=2)
    makeCurveCheckboxes(next(iter(unicornfile_list.values())))
    app.stopFrame()

    app.startFrame("data_export", row=0, column=3)
    app.setStretch("COLUMN")

    app.addLabel("L1", "Select number of points\nto resample to:")
    app.addNumericEntry("resample_size")
    app.addLabel("L2", "Select x-value:")
    app.addRadioButton("x unit", "mL")
    app.addRadioButton("x unit", "CV")
    # app.addRadioButton("x unit", "min")
    app.addButton("Export all csv's", buttonMakeAllCSV)
    app.addButton("Overlay Curves", curveOverlay)
    app.stopFrame()

    app.go()


if __name__ == '__main__':
    main()
