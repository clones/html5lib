import codecs
import re

from constants import EOF

class HTMLInputStream(object):
    """Provides a unicode stream of characters to the HTMLTokenizer.

    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.

    """

    def __init__(self, source, encoding=None):
        """Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by the HTML5Lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)

        """
        # List of where new lines occur
        self.newLines = []

        # Encoding Information
        self.charEncoding = encoding

        # Raw Stream
        self.rawStream = self.openStream(source)

        # Try to detect the encoding of the stream by looking for a BOM
        detectedEncoding = self.detectEncoding()

        # If an encoding was specified or detected from the BOM don't allow
        # the encoding to be changed futher into the stream
        if self.charEncoding or detectedEncoding:
            self.allowEncodingOverride = False
        else:
            self.allowEncodingOverride = True

        # If an encoding wasn't specified, use the encoding detected from the
        # BOM, if present, otherwise use the default encoding
        if not self.charEncoding:
            self.charEncoding = detectedEncoding or "cp1252"

        # Read bytes from stream decoding them into Unicode
        uString = self.rawStream.read().decode(self.charEncoding, 'replace')

        # Normalize new lines and null characters
        uString = re.sub('\r\n?', '\n', uString)
        uString = re.sub('\x00', '\xFFFD', uString)

        # Convert the unicode string into a list to be used as the data stream
        self.dataStream = list(uString)

        self.queue = []

        # Reset position in the list to read from
        self.reset()

    def openStream(self, source):
        """Produces a file object from source.

        source can be either a file object, local filename or a string.

        """
        # Already a file object
        if hasattr(source, 'read'):
            stream = source
        else:
            # Try opening from file system
            try:
                return open(source)
            except: pass

            # Otherwise treat source as a string and convert to a file object
            import cStringIO
            stream = cStringIO.StringIO(str(source))
        return stream

    def detectEncoding(self):
        # Attempts to detect the character encoding of the stream. If
        # an encoding can be determined from the BOM return the name of the
        # encoding otherwise return None
        bomDict = {
            codecs.BOM_UTF8: 'utf-8',
            codecs.BOM_UTF16_LE: 'utf-16-le', codecs.BOM_UTF16_BE: 'utf-16-be',
            codecs.BOM_UTF32_LE: 'utf-32-le', codecs.BOM_UTF32_BE: 'utf-32-be'
        }

        # Go to beginning of file and read in 4 bytes
        self.rawStream.seek(0)
        string = self.rawStream.read(4)

        # Try detecting the BOM using bytes from the string
        encoding = bomDict.get(string[:3])       # UTF-8
        seek = 3
        if not encoding:
            encoding = bomDict.get(string[:2])   # UTF-16
            seek = 2
            if not encoding:
                encoding = bomDict.get(string)   # UTF-32
                seek = 4

        # Set the read position past the BOM if one was found, otherwise
        # set it to the start of the stream
        self.rawStream.seek(encoding and seek or 0)

        return encoding

    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element

        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.

        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, return True indicating
        parsing will have to begin again.

        """
        pass

    def determineNewLines(self):
        # Looks through the stream to find where new lines occur so
        # the position method can tell where it is.
        self.newLines.append(0)
        for i in xrange(len(self.dataStream)):
            if self.dataStream[i] == u"\n":
                self.newLines.append(i)

    def position(self):
        """Returns (line, col) of the current position in the stream."""
        # Generate list of new lines first time around
        if not self.newLines:
            self.determineNewLines()

        line = 0
        tell = self.tell
        for pos in self.newLines:
            if pos < tell:
                line += 1
            else:
                break
        col = tell - self.newLines[line-1] - 1
        return (line, col)

    def reset(self):
        """Resets the position in the stream back to the start."""
        self.tell = 0

    def char(self):
        """ Read one character from the stream or queue if available. Return
            EOF when EOF is reached.
        """
        if self.queue:
            return self.queue.pop(0)
        else:
            try:
                self.tell += 1
                return self.dataStream[self.tell - 1]
            except:
                return EOF

if __name__ == "__main__":
    try:
        stream = HTMLInputStream("tests/utf-8-bom.html")

        c = stream.readChar()
        while c:
            line, col = stream.position()
            if c == u"\n":
                print "Line %s, Column %s: Line Feed" % (line, col)
            else:
                print "Line %s, Column %s: %s" % (line, col, c.encode('utf-8'))
            c = stream.readChar()
        print "EOF"
    except IOError:
        print "The file does not exist."
