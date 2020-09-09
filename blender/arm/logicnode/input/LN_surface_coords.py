from arm.logicnode.arm_nodes import *

class SurfaceCoordsNode(ArmLogicTreeNode):
    """Surface coords node"""
    bl_idname = 'LNSurfaceCoordsNode'
    bl_label = 'Surface Coords'

    def init(self, context):
        self.add_output('NodeSocketVector', 'Coords')
        self.add_output('NodeSocketVector', 'Movement')

add_node(SurfaceCoordsNode, category=PKG_AS_CATEGORY, section='surface')