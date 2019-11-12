import unittest
from unittest import TestLoader, TestSuite, TextTestRunner


if __name__ == "__main__":
    TextTestRunner().run(TestSuite(TestLoader().discover(start_dir="test")))
