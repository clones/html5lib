require 'html5lib/treebuilders/simpletree'
require 'html5lib/treebuilders/rexml'

module HTML5lib
module TreeBuilders

def TreeBuilders.getTreeBuilder name
  return SimpleTree::TreeBuilder if name.downcase == 'simpletree'
  return REXMLTree::TreeBuilder if name.downcase == 'rexml'
end

end
end
