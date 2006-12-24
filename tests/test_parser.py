import sys
import os
import glob
import StringIO
import unittest
import new

def parseTestcase(testString):
    testString = testString.split("\n")
    try:
        if testString[0] != "#data":
            print testString
        assert testString[0] == "#data"
    except:
        raise
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        if line and not (line.startswith("#errors") or
          line.startswith("#document") or line.startswith("#data")):
            if currentList is output:
                if line.startswith("|"):
                    currentList.append(line[2:])
                else:
                    currentList.append(line)
            else:
                currentList.append(line)
        elif line == "#errors":
            currentList = errors
        elif line == "#document":
            currentList = output
    return "\n".join(input), "\n".join(output), errors

def convertTreeDump(treedump):
    """convert the output of str(document) to the format used in the testcases"""
    treedump = treedump.split("\n")[1:]
    rv = []
    for line in treedump:
        if line.startswith("|"):
            rv.append(line[3:])
        else:
            rv.append(line)
    return "\n".join(rv)

class TestCase(unittest.TestCase):
    def runParserTest(self, input, output, errors):
        import parser
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        p = parser.HTMLParser()
        document = p.parse(StringIO.StringIO(input))
        errorMsg = "\n".join(["\n\nExpected:", output, "\nRecieved:",
          convertTreeDump(document.printTree())])
        self.assertEquals(output, convertTreeDump(document.printTree()),
          errorMsg)

def test_parser():
    for filename in glob.glob('tree-construction/*.dat'):
        f = open(filename)
        test = []
        documentSeen = False
        for line in f:
            # XXX This algorithm would need to be changed if we want to get rid
            # of the double newline requirement at the end of test files.
            if line.startswith("#document"):
                documentSeen = True
            if not line == "\n":
                test.append(line[:-1])
            elif line == "\n" and not documentSeen:
                test.append(line[:-1])
            else:
                input, output, errors = parseTestcase("\n".join(test))
                yield TestCase.runParserTest, input, output, errors
                test = []
                documentSeen = False

def buildTestSuite():
    tests = 0
    for func, input, output, errors in test_parser():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, input=input, output=output, \
            errors=errors: method(self, input, output, errors)
        testFunc.__doc__ = 'Parser %s: %s' % (testName, input)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    #Allow us to import the parent module
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

    main()
