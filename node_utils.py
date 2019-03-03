# Copyright (C) 2019 h0bB1T
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
#
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import bpy

class NodeUtils:
    """
    Contains various utils to create node elements and links.
    """

    def __init__(self):
        self.baseX = 0
        self.baseY = 0
        self.gridSizeX = 200
        self.gridSizeY = 200


    def create_math_node(self, tree, op, clamp = False, def0 = 0.5, def1 = 0.5):
        """
        Create math node and set all parameters as given by the arguments.
        """
        node = tree.nodes.new("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        node.inputs[0].default_value = def0
        node.inputs[1].default_value = def1
        return node


    def at(self, node, x, y):
        """
        Set node grid based, self.base? defines the grid origin. 200 is the grid dimension in X/Y.
        """
        node.location.x = self.baseX + x * self.gridSizeX
        node.location.y = self.baseY + y * self.gridSizeY
        return node


    def create_image_node(self, tree, fileName, nonColor = True, clip = False):
        """
        Create image node with the given file.
        """
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(fileName)
        if nonColor:
            node.color_space = "NONE"
        if clip:
            node.extension = "CLIP"
        return node


    def create_group_input(self, group, input, type, name, defValue = None):
        """
        Create a input group output and returns it.
        """
        node = group.node_tree.inputs.new("NodeSocket" + type, name)
        index = len(group.node_tree.inputs) - 1
        if defValue:
            node.default_value = defValue
            if getattr(group, "inputs", None):
                group.inputs[index].default_value = defValue
        return input.outputs[index]


    def create_group_output(self, group, output, type, name):
        """
        Create a output group input and returns it.
        """
        group.node_tree.outputs.new("NodeSocket" + type, name)
        index = len(group.node_tree.outputs) - 1
        return output.inputs[index]         


    def create_group(self, tree, name, outputX):
        """
        Create group with the supplied name, create input and output as well.
        Returns the created group and both input and output.
        """
        group = tree.nodes.new("ShaderNodeGroup")
        group.node_tree = bpy.data.node_groups.new(name, "ShaderNodeTree")
        input = group.node_tree.nodes.new("NodeGroupInput")
        output = self.at(group.node_tree.nodes.new("NodeGroupOutput"), outputX, 0)

        return (group, input, output)


    def create_group_tree(self, name, outputX):
        """
        Create the group, but do not create an instance ..
        Returns the created tree and both input and output.
        """
        tree = bpy.data.node_groups.new(name, "ShaderNodeTree")
        input = tree.nodes.new("NodeGroupInput")
        output = self.at(tree.nodes.new("NodeGroupOutput"), outputX, 0)

        return (tree, input, output)


    def create_range_selector(self, group, input, gridX, gridY, control, 
        defMin = 0.2, defMax = 0.4, defScale = 1.0, defOffset = 0.0):
        """
        Create a setup to extract the range lower-upper from input and map it to 0..1.
        In addition, this value can be scaled and get an offset. Control values are
        linked to the group input.
        """
        tree = group.node_tree
        sub = self.at(self.create_math_node(tree, "SUBTRACT"), gridX, gridY)
        dist = self.at(self.create_math_node(tree, "SUBTRACT"), gridX + 1, gridY - 0.5)
        div = self.at(self.create_math_node(tree, "DIVIDE", True), gridX + 2, gridY - 1)
        scale = self.at(self.create_math_node(tree, "MULTIPLY"), gridX + 3, gridY - 1.5)
        offset = self.at(self.create_math_node(tree, "ADD"), gridX + 4, gridY - 2)

        minValue = self.create_group_input(group, input, "Float", "Lower " + control, defMin)
        tree.links.new(minValue, sub.inputs[1])
        tree.links.new(minValue, dist.inputs[1])
        tree.links.new(self.create_group_input(group, input, "Float", "Upper " + control, defMax), dist.inputs[0])
        tree.links.new(self.create_group_input(group, input, "Float", "Scale " + control, defScale), scale.inputs[1])
        tree.links.new(self.create_group_input(group, input, "Float", "Offset " + control, defOffset), offset.inputs[1])
        tree.links.new(sub.outputs["Value"], div.inputs[0])
        tree.links.new(dist.outputs["Value"], div.inputs[1])
        tree.links.new(div.outputs["Value"], scale.inputs[0])
        tree.links.new(scale.outputs["Value"], offset.inputs[0])

        return (sub.inputs[0], offset.outputs["Value"])


    def get_selected_nodes(self, tree):
        """
        Return all selected nodes.
        """
        return [ n for n in tree.nodes if n.select ]


    def get_selected_nodes_with_output(self, tree, output):
        """
        Return selected nodes that have an output named as specified.
        """
        return [ n for n in tree.nodes if n.select and 
            n.outputs.find(output) != -1 ]
            

    def remap_output_links(self, tree, oldNode, oldOutput, newNode, newOutput):
        """
        Remap all links from olds node output to new node output.
        """
        for l in oldNode.outputs[oldOutput].links:
            tree.links.new(newNode.outputs[newOutput], l.to_socket)
