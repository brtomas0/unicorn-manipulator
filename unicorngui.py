import unicornmanipulator
import appJar
import os

app = appJar.gui("Unicorn Curve Exporter")
# app = appJar.gui("Unicorn Curve Exporter", "1000x500")


def getInputFiles():
    input_folder = app.getEntry("input_directory")
    if input_folder is None:
        return []
    return [input_folder + "\\" + i for i in os.listdir(input_folder)]

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
    app.addListBox("file_list")
    app.setListBoxWidth("file_list", 50)
    app.setListBoxMulti("file_list", True)
    app.setListBoxOverFunction("file_list", [None, displayPhases])


def makePhaseFrame():
    app.setStretch("column")
    app.setPadding([15, 5])
    # app.addButton("Update Phases", displayPhases)
    app.setStretch("column")
    # app.addLabel("PL1", "Phases in all methods:")
    app.addProperties("Phases in all methods")
    # app.addLabel("PL2", "Phases not in all methods:")
    app.addProperties("Phases not in all methods")
    app.addButton("Select all Phases", selectPhases)
    app.addButton("Deselect all Phases", deselectPhases)


def makeCurveFrame():
    app.addProperties("Curves")
    if app.getListBox("file_list") == []:
        return
    displayCurves()


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
    sim_phase_set -= set(["Method", "Method Settings"])
    clearPhases()
    for block in ordered_blocks:
        if block in sim_phase_set:
            app.setProperty("Phases in all methods", block, True)
    # app.setProperties("Phases not in all methods", {x: True for x in dif_phase_set})


def displayCurves():
    file = app.getListBox("file_list")[0]
    unicornfile_list[file].load()

    for curve_name in unicornfile_list[file].curve_data:
        app.setProperty("Curves", curve_name)
    # app.addListBox("curve_list", unicorn_file.curves)
    # app.setListBoxMulti("curve_list", True)


def getUnicornFiles():
    unicornfile_list = {}
    for file in input_files:
        if file[-4:] == ".zip":
            unicorn_file = unicornmanipulator.UnicornFile(file)
            unicornfile_list[unicorn_file.filename] = unicorn_file
        # print(file, unicorn_file.filename)

    return unicornfile_list


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
    out_filename = output_folder + "\\" + unicorn_file.filename + ".csv"
    resize = app.getEntry("resample_size")
    x_unit = app.getRadioButton("x unit")
    selected_phases = [x for x in app.properties("Phases in all methods") if app.properties("Phases in all methods")[x]]

    if len(selected_phases) == len(app.properties("Phases in all methods")):
        unicorn_file.exportCurves(curve_list, out_filename, x_unit, resize)
    elif len(selected_phases) == 1:
        unicorn_file.exportBlockCurves(selected_phases[0], curve_list, out_filename, x_unit, resize)
    else:
        print("Function not supported")
    # print(unicorn_file.filename)


def buttonMakeAllCSV():
    # curve_list = app.getAllListBoxes()["curve_list"]
    for file in app.getListBox("file_list"):
        print(file)
        exportFileCSV(unicornfile_list[file].load())


def buttonCurveComparison():
    manager = unicornmanipulator.CurveManager()
    for file in app.getListBox("file_list"):
        print(file)
        manager.add(unicornfile_list[file])
    manager.loadAllCurves()

    out_filename = app.saveBox(title="Save Data Summary", fileName="Data Summary", fileExt=".csv")

    block_list = [x for x in app.getProperties("Phases in all methods") if app.getProperties("Phases in all methods")[x]]
    curve_list = [x for x in app.getProperties("Curves") if app.getProperties("Curves")[x]]
    # out_filename = output_folder + "\\Data Summary.csv"
    x_unit = app.getRadioButton("x unit")
    resize = app.getEntry("resample_size")

    manager.exportBlocks(block_list, curve_list, out_filename, x_unit, resize)


def updateMainBody():
    global unicornfile_list
    global input_files
    input_files = getInputFiles()
    unicornfile_list = getUnicornFiles()
    app.updateListBox("file_list", [unicornfile_list[x].filename for x in unicornfile_list])
    app.selectListItemAtPos("file_list", 0)
    displayPhases()
    displayCurves()


def main():
    global output_folder
    output_folder = getOutputFolder("out test")
    # [print(x.zip_file_path) for x in unicornfile_list]

    app.startFrame("io_file_input", row=0, column=0, colspan=4)
    app.setInPadding([10, 5])
    app.setStretch("none")
    app.addLabel("io1", "Input Folder:", row=0, column=0)
    app.setLabelAlign("io1", "right")

    app.setStretch("both")
    app.addDirectoryEntry("input_directory", row=0, column=1)
    app.setEntryChangeFunction("input_directory", updateMainBody)
    app.stopFrame()

    app.startFrame("files", row=1, column=0)
    makeFileBox()
    app.stopFrame()

    app.startFrame("phases", row=1, column=1)
    makePhaseFrame()
    # app.addButton("clear properties box", clearPhases)
    app.stopFrame()

    app.startFrame("curves", row=1, column=2)
    # app.setStretch("both")
    # app.startScrollPane("curve_scroller")
    makeCurveFrame()
    # app.stopScrollPane()
    app.stopFrame()

    app.startFrame("data_export", row=1, column=3)
    app.setStretch("COLUMN")

    app.addLabel("L1", "Select number of points\nto resample to:")
    app.addNumericEntry("resample_size")
    app.addLabel("L2", "Select x-value:")
    app.addRadioButton("x unit", "mL")
    app.addRadioButton("x unit", "CV")
    # app.addRadioButton("x unit", "min")
    # app.addButton("Export all csv's", buttonMakeAllCSV)
    app.addButton("Export Data Summary", buttonCurveComparison)
    app.stopFrame()
    # app.raiseFrame("io_file_input")

    app.go()


if __name__ == '__main__':
    main()
