import unittest


if __name__ == "__main__":
    unittest.TextTestRunner().run(unittest.TestSuite(unittest.TestLoader().discover(start_dir="test")))
