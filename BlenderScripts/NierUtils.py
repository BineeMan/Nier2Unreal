import bpy


def generateNewNierUVLightmaps(bRewriteLightmaps: bool) -> None:  
    selected_objects = bpy.context.selected_objects
    objs = [o for o in selected_objects]
    bpy.ops.object.select_all(action='DESELECT')

    LightmapUVName = 'Lightmap'

    for obj in objs:
        bpy.context.view_layer.objects.active = obj
        print(obj)
        #removing original Nier lightmaps
        isLightmapFound = False
        for i in range(len(bpy.context.object.data.uv_layers)-1, 0, -1):
            if bRewriteLightmaps and LightmapUVName in bpy.context.object.data.uv_layers[i].name:
                bpy.context.object.data.uv_layers.remove(bpy.context.object.data.uv_layers[bpy.context.object.data.uv_layers[i].name])
            elif LightmapUVName in bpy.context.object.data.uv_layers[i].name and not bRewriteLightmaps:
                print("Custom Lightmap found, skipping object")
                isLightmapFound = True
                break
            elif "UVMap" in bpy.context.object.data.uv_layers[i].name:
                bpy.context.object.data.uv_layers.remove(bpy.context.object.data.uv_layers[bpy.context.object.data.uv_layers[i].name])
        
        if isLightmapFound:
            continue

        #making new UV channel for the new lightmap
        bpy.context.object.data.uv_layers.new(name=LightmapUVName)     
        bpy.context.object.data.uv_layers[LightmapUVName].active = True 
        
            
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        #Unwrapping
        #bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        bpy.ops.uv.smart_project(island_margin=0.001)

        bpy.ops.object.mode_set(mode='OBJECT')
        

def mergeNierMeshGroups(bAppleMergeVetrices: bool) -> None:
    selected_objects = bpy.context.selected_objects
    objs = [o for o in selected_objects]
    bpy.ops.object.select_all(action='DESELECT')
    
    objNameMask = objs[0].name.split('-')[1]
    objGroupList = []
    
    distanceThreshold = 0.0001
    for obj in objs:
        if obj.name.split('-')[1] != objNameMask:
            bpy.ops.object.join()
            if bAppleMergeVetrices:                        
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=distanceThreshold, use_sharp_edge_from_normals=False)
                bpy.ops.object.mode_set(mode='OBJECT')        
            objNameMask = obj.name.split('-')[1]
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)            
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
                
    bpy.ops.object.join()
    if bAppleMergeVetrices:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=distanceThreshold, use_sharp_edge_from_normals=True)
        bpy.ops.object.mode_set(mode='OBJECT')
      
                
mergeNierMeshGroups(False)
#generateNewNierUVLightmaps(True)