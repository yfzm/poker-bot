import unittest

# TODO: run specific test giving arguments
if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(
            unittest.TestLoader().discover(start_dir="test", top_level_dir=".")))
