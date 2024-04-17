import bpy
import os
import re
from datetime import datetime

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


def processMeshes(assetName: str, outputSavePath: str):
    bpy.ops.object.select_all(action='DESELECT')
    collection = bpy.data.collections[assetName]

    # Will collect meshes from delete objects
    meshes = set()

    #Get not LOD0 objects in the collection
    for obj in [o for o in collection.objects if o.type == 'MESH' and (not o.name.endswith("-0")) ]:
        meshes.add( obj.data )
        bpy.data.objects.remove( obj )

    #Look at meshes that are orphean after objects removal
    for mesh in [m for m in meshes if m.users == 0]:
        bpy.data.meshes.remove( mesh )
    
    bpy.ops.object.select_all(action='DESELECT')
    #selecting LOD0 meshes        
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
            
    mergeNierMeshGroups(bAppleMergeVetrices = False)
    
    bpy.ops.object.select_all(action='DESELECT')
    #selecting LOD0 meshes        
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
            
    generateNewNierUVLightmaps(bRewriteLightmaps = True)
    
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
    bpy.ops.export_scene.fbx(filepath = os.path.join(outputSavePath, assetName + ".fbx"), use_selection=True)


def doesCollectionExists(colName: str) -> bool:
    return colName in bpy.data.collections


def printToLog(text: str) -> None:
    with open(logFilePath, 'a') as file:
        file.write(text + "\n")

def processCollision(assetName: str, outputSavePath: str):
    def objToKey(obj):
        return str({
            'name': re.sub(r'^\d+-', '', obj.name),
            'collisionType': obj.collisionType,
            'surfaceType': obj.surfaceType,
            'slidable': obj.slidable,
            "unknownByte": obj["unknownByte"],
        })      
    groupedObjects = {}
    
    path = os.path.join(outputSavePath, assetName +"-Col" + ".fbx")
    
    if not doesCollectionExists("COL"):
        printToLog("Collision not found, skipping " + assetName)
        return
    
    for obj in bpy.data.collections["COL"].objects:
        if obj.type != "MESH":
            continue
        
        key = objToKey(obj)
        if key not in groupedObjects:
            groupedObjects[key] = []
        groupedObjects[key].append(obj)


    for key, objects in groupedObjects.items():
        if len(objects) == 1:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
    
    collection = bpy.data.collections["COL"]
    
    savePath = os.path.join(outputSavePath, "Collision")
    
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    
    #standalone col objects
    bpy.ops.object.select_all(action='DESELECT')
    bFoundAny = False
    for obj in [o for o in collection.objects if o.type == 'MESH' and ("before" not in o.name.lower()) and ("after" not in o.name.lower())]:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bFoundAny = True       
    if bFoundAny:
        bpy.ops.export_scene.fbx(filepath = os.path.join(savePath, assetName +"-Col_S" + ".fbx"), use_selection=True)
    
    #before col objects
    bFoundAny = False
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [o for o in collection.objects if o.type == 'MESH' and ("before" in o.name.lower())]:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)     
        bFoundAny = True
        
    if bFoundAny:       
        bpy.ops.export_scene.fbx(filepath = os.path.join(savePath, assetName +"-Col_B" + ".fbx"), use_selection=True)
    
    #after col objects
    bFoundAny = False
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [o for o in collection.objects if o.type == 'MESH' and ("after" in o.name.lower())]:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)  
        bFoundAny = True
    if bFoundAny:          
        bpy.ops.export_scene.fbx(filepath = os.path.join(savePath, assetName +"-Col_A" + ".fbx"), use_selection=True)
    
    
    
def processLay(assetName: str, outputSavePath: str):
    collection = bpy.data.collections["lay_layAssets"]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [o for o in collection.objects if o.type == 'EMPTY']:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
    collection = bpy.data.collections["lay_layInstances"]
    for obj in [o for o in collection.objects if o.type == 'EMPTY']:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath = os.path.join(outputSavePath, assetName +"-Lay" + ".fbx"), use_selection=True)
        
           
def processAsset(assetPath: str, bSkipExisting: bool):
    assetName = os.path.basename(assetPath).replace(".dtt", "") 
    outputSavePath = os.path.join(fbxSavePath, assetName)
    
    #import dtt
    

    if not os.path.exists(outputSavePath):
        os.mkdir(outputSavePath)
    
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)

    bpy.ops.import_scene.dtt_data(filepath = assetPath, reset_blend = True)
    
    #processMeshes(assetName, outputSavePath)  
    processCollision(assetName, outputSavePath)  
    #try:
    #    processLay(assetName, outputSavePath)
    #except:
    #    printToLog(assetName + " Lay Error")
        
        
def convertToBlend(assetPath: str, outputFolder: str) -> None:
    assetName = os.path.basename(assetPath).replace(".dtt", "")
    
    if os.path.exists(os.path.join(outputFolder, assetName + ".blend")):
        return
    
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)
        
    bpy.ops.import_scene.dtt_data(filepath = assetPath, reset_blend = True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outputFolder, assetName + ".blend"))


print("---------------------------------")

targetFiles = []
assetDir = "G:\\NierModding\\NierDataMerged\\MergedWd1_003-004,013-014"
fbxSavePath = "E:\\3Dprogramms\\NierModding\\NierOverworld\\auto"

blendDir = "E:\\3Dprogramms\\NierModding\\NierOverworld\\blend"

clustersFile = 'E:\\3Dprogramms\\NierModding\\clusters.txt'
with open(clustersFile) as file:
    targetFiles = [line.rstrip() for line in file]
   
print(targetFiles)

#targetFiles = ['g11320']

bSkipExistingWmb = True
bSkipExistingCollisionFiles = True
bSkipExistingLayFiles = True

# datetime object containing current date and time
now = datetime.now()
# dd/mm/YY H:M:S
dateTimeNow = now.strftime("%d.%m.%Y %H.%M")
logFilePath = os.path.join("E:\\3Dprogramms\\NierModding\\NierOverworld\\logs", dateTimeNow + ".txt")


for file in targetFiles:
    path = os.path.join(assetDir, file + ".dtt")
    if os.path.exists(path): 
        processAsset(assetPath=path, bSkipExisting=True)

    else:
        printToLog("Error: file " + path + " does not exist.")
                        