import unittest
import unicornmanipulator
import os


class testUnicornFile(unittest.TestCase):

    def setUp(self):
        in_files = self.getFiles()
        self.unicorn_file = unicornmanipulator.UnicornFile(in_files[0])

    def getFiles(self):
        input_folder = os.path.dirname(os.path.dirname(__file__)) + "\\unicorn-manipulator-data\\input"
        input_files = os.listdir(input_folder)
        return [input_folder + "\\" + i for i in input_files]

    def testLoad(self):
        self.unicorn_file.getFileData()
        self.assertIsNotNone(self.unicorn_file.chrom_1_tree)

    def testGetLogbook(self):
        self.unicorn_file.load()
        self.unicorn_file.getLogbook()
        self.assertIsInstance(self.unicorn_file.logbook, list)

    def testGetBlocks(self):
        self.unicorn_file.load()
        self.unicorn_file.getBlocks()
        self.assertIsNotNone(self.unicorn_file.blocks)

    def testGettingCurves(self):
        self.unicorn_file.load()
        self.unicorn_file.getAvailableCurves()
        self.assertIsNotNone(self.unicorn_file.curves_and_files)


if __name__ == '__main__':
    unittest.main()
