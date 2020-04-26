from __future__ import print_function
import Leap
import hou

class HouLeap:
    def __init__(self, node):
        self.init_node = node
        self.frame_index = -1
        self.frame = None                
        self.controller = Leap.Controller()
        self.controller.set_policy(Leap.Controller.POLICY_ALLOW_PAUSE_RESUME)
        print("Leap Initialized")
        self.enable()

    def display_comment(self):
        comment = "Device : " + ("Enabled" if self.is_enabled() else "Disabled")
        set_node_comment(self.init_node, comment)

    def get_frame(self):
        cf = hou.frame()
        if cf != self.frame_index:
            self.frame_index = cf
            self.frame = self.controller.frame()
        return self.frame

    def enable(self):
        self.controller.set_paused(False)
        self.display_comment()
        print("Leap Enabled")
        
    def disable(self):
        self.controller.set_paused(True)
        self.display_comment()
        print("Leap Disabled")

    def is_enabled(self):
        return self.controller.is_connected


def init(init_node):
    hou.session.leap = HouLeap(init_node)
    hou.session.leap.display_comment()

def is_init():
    return hasattr(hou.session, "leap")

def raise_not_init(node):
    raise hou.NodeError("Leap not initialized")
    set_node_comment(node, "Leap not initialized")

def invoke(node, func):
    if is_init():
        f = getattr(hou.session.leap, func)
        f()
    else:
        raise_not_init(node)

def set_node_comment(node, msg):
    node.setComment(msg)
    node.setGenericFlag(hou.nodeFlag.DisplayComment, True)

def leap_to_hou(vec):
    return hou.Vector3(vec.x, vec.y, vec.z)

def track(node):
    leap = hou.session.leap
    if not leap.is_enabled():
        raise hou.NodeError("Leap Device not enabled")
    
    geo = node.geometry()
    frame = leap.get_frame()
    if not frame:
        raise hou.NodeError("Can't read frame")
    
    f_group = geo.findPointGroup("fingers")
    h_group = geo.findPointGroup("hands")
    a_group = geo.findPointGroup("arms")
    
    for i,h in enumerate(frame.hands, start=1):
        
        if node.parent().evalParm("hands"):
            
            hou_p = leap_to_hou(h.palm_position)
            hou_d = leap_to_hou(h.direction)
            hou_n = leap_to_hou(h.palm_normal)
            
            p = geo.createPoint()
            p.setPosition(hou_p)
            p.setAttribValue("dir", hou_d)
            p.setAttribValue("palm_N", hou_n)
            p.setAttribValue("hand", i)           
            h_group.add(p)        
    
        for j,f in enumerate(h.fingers):
        
            bones = [f.bone(Leap.Bone.TYPE_METACARPAL),
                     f.bone(Leap.Bone.TYPE_PROXIMAL),
                     f.bone(Leap.Bone.TYPE_INTERMEDIATE),
                     f.bone(Leap.Bone.TYPE_DISTAL)]
            prim = geo.createPolygon()
            prim.setIsClosed(False)
            
            for k,bone in enumerate(bones):
            
                leap_p = bone.center
                leap_d = bone.direction       
                hou_p = leap_to_hou(bone.center)
                hou_d = leap_to_hou(bone.direction)
                
                p = geo.createPoint()
                p.setPosition(hou_p)
                p.setAttribValue("finger", j)
                p.setAttribValue("bone", k)
                p.setAttribValue("hand", i)
                p.setAttribValue("dir", hou_d)
                f_group.add(p)
                prim.addVertex(p)    
                
        if node.parent().evalParm("arms"):
            
            hou_e_p = leap_to_hou(h.arm.elbow_position)
            hou_w_p = leap_to_hou(h.arm.wrist_position)
            hou_d = leap_to_hou(h.arm.direction)

            prim = geo.createPolygon()
            prim.setIsClosed(False)

            p = geo.createPoint()   # elbow
            p.setPosition(hou_e_p)
            p.setAttribValue("hand", i)
            p.setAttribValue("dir", hou_d)
            a_group.add(p)
            prim.addVertex(p)

            p = geo.createPoint()   # wrist
            p.setPosition(hou_w_p)
            p.setAttribValue("hand", i)
            a_group.add(p)
            prim.addVertex(p)