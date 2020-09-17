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


def makeFileBox():
    app.setStretch("both")
    app.addListBox("file_list", [unicornfile_list[x].file_name for x in unicornfile_list])
    # app.setFrameWidth("files",300)
    app.setListBoxWidth("file_list", 50)
    app.setListBoxMulti("file_list", True)
    app.selectListItemAtPos("file_list", 0)


def makeCurveList():
    file = app.getListBox("file_list")[0]
    print(file)
    unicornfile_list[file].load()

    app.addProperties("Curves")
    for curve_name in unicornfile_list[file].curve_data:
        app.setProperty("Curves", curve_name)
    # app.addListBox("curve_list", unicorn_file.curves)
    # app.setListBoxMulti("curve_list", True)


def makePhaseFrame():
    app.setStretch("column")
    app.setPadding([15, 5])
    app.addButton("Update Phases", displayPhases)
    app.setStretch("column")
    # app.addLabel("PL1", "Phases in all methods:")
    app.addProperties("Phases in all methods")
    # app.addLabel("PL2", "Phases not in all methods:")
    app.addProperties("Phases not in all methods")
    app.setProperty("Phases not in all methods", "tempt")
    displayPhases()
    app.addButton("Select all Phases", selectPhases)
    app.addButton("Deselect all Phases", deselectPhases)


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
    clearPhases()
    app.setProperties("Phases in all methods", {x: True for x in ordered_blocks if x in sim_phase_set})
    app.setProperties("Phases not in all methods", {x: True for x in dif_phase_set})
    # app.updateListBox("Phases in all methods", phase_list.keys())


def clearPhases():
    for prop in app.getProperties("Phases in all methods"):
        app.deleteProperty("Phases in all methods", prop)
    for prop in app.getProperties("Phases not in all methods"):
        app.deleteProperty("Phases not in all methods", prop)


def selectPhases():
    app.resetProperties("Phases in all methods")
    app.resetProperties("Phases not in all methods")


def deselectPhases():
    app.clearProperties("Phases in all methods")
    app.clearProperties("Phases not in all methods")


def exportFileCSV(unicorn_file):
    # curve_list = [x for x in app.getAllCheckBoxes() if app.getAllCheckBoxes()[x] is True]
    curve_list = [x for x in app.getProperties("Curves") if app.getProperties("Curves")[x]]
    out_file_name = output_folder + "\\" + unicorn_file.file_name + ".csv"
    resize = app.getEntry("resample_size")
    x_unit = app.getRadioButton("x unit")
    selected_phases = [x for x in app.properties("Phases in all methods") if app.properties("Phases in all methods")[x]]
    if len(selected_phases) == len(app.properties("Phases in all methods")):
        unicorn_file.exportCurves(curve_list, out_file_name, resize, x_unit)
    elif len(selected_phases) == 1:
        unicorn_file.exportBlockCurves(selected_phases[0], curve_list, out_file_name, resize, x_unit)
    else:
        print("Function not supported")
    # print(unicorn_file.file_name)


def buttonMakeAllCSV():
    # curve_list = app.getAllListBoxes()["curve_list"]
    for file in app.getListBox("file_list"):
        print(file)
        exportFileCSV(unicornfile_list[file].load())


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
    # app.addButton("clear properties box", clearPhases)
    app.stopFrame()

    app.startFrame("curves", row=0, column=2)
    makeCurveList()
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
