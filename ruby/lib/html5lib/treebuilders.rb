require 'html5lib/treebuilders/simpletree'
require 'html5lib/treebuilders/rexml'
require 'html5lib/treebuilders/hpricot'

module HTML5lib
module TreeBuilders

  def self.getTreeBuilder(name)
    case name.to_s.downcase
        when 'simpletree' then SimpleTree::TreeBuilder
        when 'rexml' then REXMLTree::TreeBuilder
        when 'hpricot' then Hpricot::TreeBuilder
        else
            raise "Unknown TreeBuilder #{name}"
    end
  end

end
end
