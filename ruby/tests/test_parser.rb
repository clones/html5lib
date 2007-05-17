require 'test/unit'
require 'html5lib/treebuilders'
require 'html5lib/html5parser'
require 'stringio'

# add back in simpletree when errors => 0
treeTypes = {
  # "simpletree" => HTML5lib::TreeBuilders.getTreeBuilder("simpletree"),
  "rexml" => HTML5lib::TreeBuilders.getTreeBuilder("rexml")
}

puts 'Testing trees '+ treeTypes.keys.join(' ')

#Run the parse error checks
checkParseErrors = false

def parseTestcase(testString)
    testString = testString.split("\n")
    innerHTML = false
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        def line.startswith string; self[0...string.length] == string; end
        if line and not (line.startswith("#errors") or
          line.startswith("#document") or line.startswith("#data") or
          line.startswith("#document-fragment")):
            if currentList == output:
                if line.startswith("|"):
                    currentList.push(line[2..-1])
                else
                    currentList.push(line)
                end
            else
                currentList.push(line)
            end
        elsif line == "#errors"
            currentList = errors
        elsif line == "#document" or line.startswith("#document-fragment")
            if line.startswith("#document-fragment")
                innerHTML = line[19..-1]
                raise AssertionError unless innerHTML
            end
            currentList = output
        end
    end
    return innerHTML, input.join("\n"), output.join("\n"), errors
end

# convert the output of str(document) to the format used in the testcases
def convertTreeDump(treedump)
    treedump.split("\n")[1..-1].map {|line|
       (line.length>2 and line[0] == ?|) ? line[3..-1] : line
    }.join("\n")
end

class HTML5ParserTestCase < Test::Unit::TestCase; end

tests = 0
base = File.dirname(File.dirname(File.dirname(File.expand_path(__FILE__))))
testpath = File.join(File.join(base, 'tests'),'tree-construction')

for name, cls in treeTypes
    for filename in Dir[File.join(testpath,'*.dat')]
        f = File.open(filename)
        f.read().split("#data\n").each {|test|
            next if test == ""
            tests += 1
           
            innerHTML, input, expected, errors = parseTestcase(test)
            HTML5ParserTestCase.send :define_method, ('test_%d' % tests) do
                p = HTML5lib::HTMLParser.new(:tree => cls)
                if innerHTML
                    p.parseFragment(StringIO.new(input), innerHTML)
                else
                    p.parse(StringIO.new(input))
                end
                output = convertTreeDump(p.tree.testSerializer(p.tree.document))
                errorMsg = ["\nInput:", input,
                            "\nExpected:", expected,
                            "\nRecieved:", output].join("\n")
                assert_equal expected, output, errorMsg
                errStr = p.errors.map {|linecol,message|
                    line,col=linecol; "Line: %i Col: %i %s"%[line, col, message]}
                if checkParseErrors
                    errorMsg2 = ["\n\nInput errors:\n" + errors.join("\n"),
                        "Actual errors:\n" + errStr.join("\n")].join("\n")
                    assert_equal p.errors.length, errors.length, errorMsg2
                end
            end
        }
    end
end
