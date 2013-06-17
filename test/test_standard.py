import io
import os
import sys
import unittest
import tempfile


sys.path.append('../')


from unstdlib.standard.collections_ import RecentlyUsedContainer
from unstdlib.standard.contextlib_ import open_atomic


class TestRecentlyUsedContainer(unittest.TestCase):
    def test_maxsize(self):
        d = RecentlyUsedContainer(5)

        for i in xrange(5):
            d[i] = str(i)

        self.assertEqual(len(d), 5)

        for i in xrange(5):
            self.assertEqual(d[i], str(i))

        d[i+1] = str(i+1)

        self.assertEqual(len(d), 5)
        self.assertFalse(0 in d)
        self.assertTrue(i+1 in d)


class TestOpenAtomic(unittest.TestCase):
    class ExpectedException(Exception):
        pass

    def setUp(self):
        self.testfile = os.path.join(tempfile.gettempdir(),
                                     "unstdlib-atmoicopen-test")
        self.rmtestfile()

    def tearDown(self):
        self.rmtestfile()

    def rmtestfile(self):
        try:
            os.remove(self.testfile)
        except OSError:
            pass

    def test_context_manager_success(self):
        with open_atomic(self.testfile) as f:
            f.write("Hello, world!")
            self.assertFalse(os.path.exists(self.testfile))
            self.assertEqual(os.path.dirname(self.testfile),
                             os.path.dirname(f.temp_name))
        self.assertTrue(os.path.exists(self.testfile))
        self.assertEqual(open(self.testfile).read(), "Hello, world!")

    def test_context_manager_fail(self):
        temp_name = None
        try:
            with open_atomic(self.testfile) as f:
                f.write("Hello, world!")
                temp_name = f.temp_name
                self.assertTrue(os.path.exists(temp_name))
                raise self.ExpectedException
        except self.ExpectedException:
            pass
        self.assertFalse(os.path.exists(self.testfile))
        self.assertFalse(os.path.exists(temp_name))

    def test_abort(self):
        with open_atomic(self.testfile) as f:
            self.assertTrue(os.path.exists(f.temp_name))
            f.abort()
            self.assertEqual(f.abort_error, None)
            self.assertTrue(f.aborted)
            self.assertTrue(f.closed)
            self.assertFalse(os.path.exists(self.testfile))
            self.assertFalse(os.path.exists(f.temp_name))

    def test_abort_fails(self):
        with open_atomic(self.testfile) as f:
            os.remove(f.temp_name)
            f.abort()
            self.assertIn("No such file or directory", str(f.abort_error))
            self.assertTrue(f.aborted)
            self.assertTrue(f.closed)

    def test_close(self):
        with open_atomic(self.testfile) as f:
            f.write("Hello, world!")
            self.assertEqual(f.name, f.temp_name)
            f.close()
            self.assertEqual(f.name, f.target_name)
            self.assertFalse(f.aborted)
            self.assertTrue(f.closed)

    def test_close_fails(self):
        with open_atomic(self.testfile) as f:
            os.remove(f.temp_name)
            try:
                f.close()
            except OSError as e:
                self.assertIn("No such file or directory", str(e))
            self.assertIn("No such file or directory", str(f.abort_error))
            self.assertTrue(f.aborted)
            self.assertTrue(f.closed)

    def test_file_operations(self):
        with open_atomic(self.testfile, opener=io.open,
                        encoding="utf-8", mode="w+") as f:
            f.write(u"\u1234")
            f.seek(0)
            self.assertEqual(f.tell(), 0)
            x = f.read()
            self.assertEqual(x, u"\u1234")

if __name__ == '__main__':
    unittest.main()
