import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
from mathutils import Matrix,Vector

LEFT_ACTION_SET =  "vive"
LEFT_ACTION = "click_left"
LEFT_USER_PATH = "/user/hand/left"
RIGHT_ACTION_SET =  "vive"
RIGHT_ACTION = "click_right"
RIGHT_USER_PATH = "/user/hand/right"






# in function getXR_matrix

#loc = wm.xr_session_state.controller_pose0_location # Left controller for VIVE
#rot = wm.xr_session_state.controller_pose0_rotation

#loc = wm.xr_session_state.controller_pose_location0 # Left controller for Windows Mixed Reality SOMEHOW note the difference of the digit placement
#rot = wm.xr_session_state.controller_pose_rotation0
def getXR_matrix(wm,controller = 0):
	if controller == 0:
		loc = wm.xr_session_state.controller_pose0_location # Left controller.
		rot = wm.xr_session_state.controller_pose0_rotation
	else:
		loc = wm.xr_session_state.controller_pose1_location # Left controller.
		rot = wm.xr_session_state.controller_pose1_rotation
		
	rotmat = Matrix.Identity(3)
	rotmat.rotate(rot)
	rotmat.resize_4x4()
	transmat = Matrix.Translation(loc)
	scalemat = Matrix.Scale(1, 4) # Scalemat only needed if desired scale is not 1.0. 
	mat =  transmat @ rotmat @ scalemat
	return loc,rot,mat


class ModalOperator(bpy.types.Operator):
	"""Move an object with the VR controller, example"""
	bl_idname = "object.vr_modal_operator"
	bl_label = "Vr Modal Operator"
	left_controller: BoolProperty(default = True)
	_timer = None
	init_mw = None
	init_controll = None
	target = None
	world = False
	def modal(self, context, event):
		wm = bpy.context.window_manager
		if event.type in {'RIGHTMOUSE', 'ESC'}:
			self.cancel(context)
			print('Cancelled')
			return {'CANCELLED'}

		if event.type == 'TIMER':
			#self.report({'INFO'}, "running") 
			if wm.xr_session_state and self.target!=None:
				if self.left_controller: 
					value = wm.xr_session_state.get_action_state(bpy.context, LEFT_ACTION_SET, LEFT_ACTION, LEFT_USER_PATH)
				else:
					value = wm.xr_session_state.get_action_state(bpy.context, RIGHT_ACTION_SET, RIGHT_ACTION, RIGHT_USER_PATH)
				if value <.3:
					self.cancel(context)
					print('Finished')
					return {'FINISHED'}
				else:
					_, _, mat = getXR_matrix(wm,controller = 0 if self.left_controller else 1)
					if not self.world:						
						self.target.matrix_world = mat @ self.init_mw						
					else:
						diff = (self.target.matrix_world @ mat).to_translation() - self.init_controll.to_translation()
						self.target.location = self.init_mw.to_translation() - diff

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
			loc, rot, mat =  getXR_matrix(wm,controller = 0 if self.left_controller else 1)
			direction = rot.to_matrix().col[1]
			(result, location_target, normal, face_idx, object, matrix) = bpy.data.scenes['Scene'].ray_cast(deps,loc, direction = direction,distance=500)
			if result:
				print('hit')
				print(object)
				self.target = object
				self.world = False
				self.init_mw = mat.inverted() @ object.matrix_world
			else:
				self.world = True
				print('World')
				scn = bpy.context.scene
				self.target = scn.vr_landmarks[scn.vr_landmarks_active].base_pose_object
				self.init_mw = self.target.matrix_world
				self.init_controll = self.init_mw @ mat 
				
			self._timer = wm.event_timer_add(1/90, window=context.window)
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
