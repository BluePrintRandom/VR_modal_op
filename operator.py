#coded by Jacob Merrill and  Victor Mukayev 11/6/2020

import bpy
from bpy.props import IntProperty, FloatProperty
from mathutils import Matrix,Vector




class ModalOperator(bpy.types.Operator):
    """Move an object with the VR controller, example"""
    bl_idname = "object.vr_modal_operator"
    bl_label = "Vr Modal Operator"
    _timer = None
    init_mw = None
    target = None
    
    def modal(self, context, event):
        wm = bpy.context.window_manager
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            print('Cancelled')
            return {'CANCELLED'}

        if event.type == 'TIMER':
            #self.report({'INFO'}, "running") 
            if wm.xr_session_state and self.target!=None: 
                value = wm.xr_session_state.get_action_state(bpy.context, "vive", "click_left", "/user/hand/left")
                if value <.3:
                    self.cancel(context)
                    print('Finished')
                    return {'FINISHED'}
                else:
                    loc = wm.xr_session_state.controller_pose0_location # Left controller.
                    rot = wm.xr_session_state.controller_pose0_rotation
                    rotmat = Matrix.Identity(3)
                    rotmat.rotate(rot)
                    rotmat.resize_4x4()
                    transmat = Matrix.Translation(loc)
                    scalemat = Matrix.Scale(1, 4) # Scalemat only needed if desired scale is not 1.0. 
                    mat =  transmat @ rotmat @ scalemat
                    #print(self.init_rot_offset)
                    #self.target.location = mat @ self.init_offset
                    #self.target.rotation_quaternion = (rot.to_matrix() @ self.init_rot_offset).to_quaternion()
                    self.target.matrix_world = mat @ self.init_mw
                    return {'PASS_THROUGH'}
            else:
                self.cancel(context)
                print('Canceled')
                return {'CANCELLED'}
        return{'PASS_THROUGH'}

            

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        print("invoke")
        self.target = None
        deps = context.evaluated_depsgraph_get()
        if wm.xr_session_state:
            loc = wm.xr_session_state.controller_pose0_location # Left controller.
            rot = wm.xr_session_state.controller_pose0_rotation
            rotmat = Matrix.Identity(3)
            rotmat.rotate(rot)
            rotmat.resize_4x4()
            transmat = Matrix.Translation(loc)
            scalemat = Matrix.Scale(1, 4) # Scalemat only needed if desired scale is not 1.0. 
            mat =  transmat @ rotmat @ scalemat
            (result, location_target, normal, index, object, matrix) = bpy.data.scenes['Scene'].ray_cast(deps,loc, direction = rot.to_matrix().col[1],distance=500)
            if result ==True:
                print('hit')
                print(object)
                object.color[0] = 1
                self.target = object
                #self.init_offset = mat.inverted() @ object.location
                #self.init_rot_offset = rot.to_matrix().inverted() * object.rotation_euler.to_matrix()
                self.init_mw = mat.inverted() @ object.matrix_world
                self._timer = wm.event_timer_add(1/30, window=context.window)
                wm.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        print('No VR')
        return {'FINISHED'}
        
            
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        
           


def register():
    bpy.utils.register_class(ModalOperator)


def unregister():
    bpy.utils.unregister_class(ModalOperator)


if __name__ == "__main__":
    register()
    print('registered')
    # test call would probbaly be useless
    #bpy.ops.object.vr_modal_operator('INVOKE_DEFAULT')
