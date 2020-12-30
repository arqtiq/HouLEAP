from __future__ import print_function
import Leap
import hou

# https://developer-archive.leapmotion.com/documentation/python/api/Leap_Classes.html

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
    set_node_comment(node, "Leap not initialized")
    raise hou.NodeError("Leap not initialized")

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
    t_group = geo.findPointGroup("tips")
    
    # hands
    for i,h in enumerate(frame.hands, start=1):  
        if node.parent().evalParm("hands"):
            p = geo.createPoint()
            p.setPosition(leap_to_hou(h.palm_position))
            p.setAttribValue("dir", leap_to_hou(h.direction))
            p.setAttribValue("palm_N", leap_to_hou(h.palm_normal))
            p.setAttribValue("palm_width", h.palm_width)
            p.setAttribValue("hand", i)
            h_group.add(p)
    
        # fingers
        for j,f in enumerate(h.fingers):
            bones = [
                     f.bone(Leap.Bone.TYPE_PROXIMAL),
                     f.bone(Leap.Bone.TYPE_INTERMEDIATE),
                     f.bone(Leap.Bone.TYPE_DISTAL)]
            # don't track metacarpal bone for thumbs
            if j > 0:
                bones.insert(0, f.bone(Leap.Bone.TYPE_METACARPAL))
            prim = geo.createPolygon()
            prim.setIsClosed(False)
            
            # bones
            for k,bone in enumerate(bones):
                hou_d = leap_to_hou(bone.direction)
                
                p = geo.createPoint()
                p.setPosition(leap_to_hou(bone.prev_joint))
                p.setAttribValue("finger", j)
                p.setAttribValue("bone", k)
                p.setAttribValue("hand", i)
                p.setAttribValue("dir", hou_d)
                f_group.add(p)
                prim.addVertex(p)

                if k == len(bones) - 1:
                    p = geo.createPoint()
                    p.setPosition(leap_to_hou(bone.next_joint))
                    p.setAttribValue("finger", j)
                    p.setAttribValue("bone", k)
                    p.setAttribValue("hand", i)
                    p.setAttribValue("dir", hou_d)
                    f_group.add(p)
                    t_group.add(p)
                    prim.addVertex(p)
                
        if node.parent().evalParm("arms"):           
            prim = geo.createPolygon()
            prim.setIsClosed(False)

            p = geo.createPoint()   # wrist
            p.setPosition(leap_to_hou(h.arm.wrist_position))
            p.setAttribValue("hand", i)
            p.setAttribValue("dir", leap_to_hou(h.arm.direction))
            p.setAttribValue("arm_width", h.arm.width )
            a_group.add(p)
            prim.addVertex(p)

            p = geo.createPoint()   # elbow
            p.setPosition(leap_to_hou(h.arm.elbow_position))
            p.setAttribValue("hand", i)
            p.setAttribValue("dir", leap_to_hou(h.arm.direction))
            a_group.add(p)
            prim.addVertex(p)