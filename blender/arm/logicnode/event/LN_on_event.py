from arm.logicnode.arm_nodes import *

class OnEventNode(ArmLogicTreeNode):
    """On event node"""
    bl_idname = 'LNOnEventNode'
    bl_label = 'On Event'
    property0: StringProperty(name='', default='')

    def init(self, context):
        self.add_output('ArmNodeSocketAction', 'Out')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'property0')

add_node(OnEventNode, category=PKG_AS_CATEGORY, section='custom')