import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket
from arm.logicnode.arm_nodes import *

class GetVisibleNode(Node, ArmLogicTreeNode):
    """Get Visible node"""
    bl_idname = 'LNGetVisibleNode'
    bl_label = 'Get Visible'
    bl_icon = 'NONE'

    def init(self, context):
        self.inputs.new('ArmNodeSocketObject', 'Object')
        self.outputs.new('NodeSocketBool', 'Object')
        self.outputs.new('NodeSocketBool', 'Mesh')
        self.outputs.new('NodeSocketBool', 'Shadow')

add_node(GetVisibleNode, category='Value')
