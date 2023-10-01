from datetime import datetime
import sys, os, unittest
from time import sleep
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Archive import Archive


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.archive = Archive("test_archive", 0.1)

    def tearDown(self):
        self.archive = None
        sleep(1)
        os.remove("archive/test_archive.bak")
        os.remove("archive/test_archive.dat")
        os.remove("archive/test_archive.dir")
        
    def test_store(self):
        data = [1,2,3,4,5]
        sleep(0.5)
        self.archive.store(data)
        self.assertEqual(self.archive.retrieve(), data)

    def test_retrieve(self):
        data = [1,2,3,4,5]
        sleep(0.5)
        self.archive.store(data)
        self.assertEqual(self.archive.retrieve(), data)

    def test_retrieve_all(self):
        data = [1,2,3,4,5]
        sleep(0.5)
        self.archive.store(data)
        data2 = [6,7,8,9,10]
        sleep(0.5)

        self.archive.store(data2)
        archive = self.archive.retrieve_all()
        print(archive)
        self.assertEqual(archive[0][1], data)
        self.assertEqual(archive[1][1], data2)