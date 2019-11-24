import unittest

# TODO: run specific test giving arguments
if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(
            unittest.TestLoader().discover(start_dir="test", top_level_dir=".")))
    if not result.wasSuccessful():
        exit(1)
