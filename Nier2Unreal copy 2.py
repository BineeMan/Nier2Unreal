#Glory. To mankind.

import unreal
import os
import enum
import json
from math import *
from typing import Tuple
import re
import time

#Modify this section according to your desires
UnrealNierBaseMaterialDirectory = '/Game/NieRAutomata/BaseMaterials/' #your game folder
UnrealMaterialsDirectory = '/Game/NieRAutomata/Maps/Materials/'
UnrealTexturesDirectory = '/Game/NieRAutomata/Maps/Textures/'

NierTextureDirectoryJpg = "G:\\NierModding\\tex_jpg_mergedAll" #dds import not supported by unreal, only jpg or png
NierTextureDirectoryPng = "G:\\NierModding\\tex_png_mergedAll" #dds import not supported by unreal, only jpg or png
MaterialsJsonPaths = ["G:\\Repositories\\Nier2Unreal\\materials.json",
                      "G:\\NierModding\\NierDataMerged\\MergedWd1_003-004\\materials.json",
                      "G:\\NierModding\\NierDataMerged\\MergedWd1_013-014\\materials.json",
                        ]

#MaterialsJsonPaths = ["G:\\NierModding\\materials.json"]

#Nier material names. Better not to change
NierBaseSimpleMaterialName = "MAT_NierBaseSimple"
NierBaseComplexMaterialName = "MAT_NierBaseComplex"
NierBaseComplex2MaterialName = "MAT_NierBaseComplex2"
NierBaseAlbedoOnlyMaterialName = "MAT_NierBaseAlbedoOnly"
NierBaseGrassMaterialName = "MAT_NierGrass"
NierBaseLeavesMaterialName = "MAT_NierTreeLeaves"

#Base Materials
NierBaseSimpleMaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseSimpleMaterialName]))
NierBaseComplexMaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseComplexMaterialName]))
NierBaseComplex2MaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseComplex2MaterialName]))
NierBaseAlbedoOnlyMaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseAlbedoOnlyMaterialName]))
NierBaseGrassMaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseGrassMaterialName]))
NierBaseLeavesMaterialAsset = unreal.EditorAssetLibrary.find_asset_data(unreal.Paths.combine([UnrealNierBaseMaterialDirectory, NierBaseLeavesMaterialName]))

#Unreal's libraries
AssetTools = unreal.AssetToolsHelpers.get_asset_tools()
MaterialEditingLibrary = unreal.MaterialEditingLibrary
EditorAssetLibrary = unreal.EditorAssetLibrary


class NierMaterialType(enum.Enum):
    simple = 1
    complex = 2
    albedoOnly = 3
    grass = 4
    leaves = 5
    complex2 = 6    

def setMaterialInstanceTextureParameter(materialInstanceAsset, parameterName, texturePath):
    if not unreal.EditorAssetLibrary.does_asset_exist(texturePath):
        unreal.log_warning("Can't find texture: " + texturePath)
        
        return False
    textureAsset = unreal.EditorAssetLibrary.find_asset_data( texturePath ).get_asset()
    return unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(materialInstanceAsset, parameterName, textureAsset)

#importing textures into UE into output path. NierMaterialType and isDecal variables are for defining if given material needs transparent textures. It was made to save disk space.
def importTextures(fileNames: list[str], outputDirectory: str, materialType: NierMaterialType, isDecal: bool, pngOnly: bool) -> None:
    texturePaths = []
    
    if pngOnly:
        for fileName in fileNames:
            filePath = os.path.join(NierTextureDirectoryPng, fileName + ".png" )
            if os.path.exists(filePath):
                texturePaths.append(filePath)
    elif materialType is NierMaterialType.albedoOnly:
        texturePaths.append(os.path.join(NierTextureDirectoryPng, fileNames[0] + ".jpg" ))
    elif materialType is NierMaterialType.complex:
        for i in range(0, 3):
            texturePaths.append(os.path.join(NierTextureDirectoryPng, fileNames[i] + ".png" ))
        for i in range(3, len(fileNames)):
            texturePaths.append(os.path.join(NierTextureDirectoryJpg, fileNames[i] + ".jpg" ))
    elif materialType is NierMaterialType.simple and isDecal is False:
        for fileName in fileNames:
            texturePaths.append(os.path.join(NierTextureDirectoryJpg, fileName + ".jpg" ))
    elif materialType is NierMaterialType.simple and isDecal is True:
        texturePaths.append(os.path.join(NierTextureDirectoryPng, fileNames[0] + ".png" ))
        for i in range(1, len(fileNames)):
            texturePaths.append(os.path.join(NierTextureDirectoryJpg, fileNames[i] + ".jpg" ))

    assetImportData = unreal.AutomatedAssetImportData()
    # set assetImportData attributes
    assetImportData.destination_path = outputDirectory
    assetImportData.filenames = texturePaths
    assetImportData.replace_existing = False
    AssetTools.import_assets_automated(assetImportData)


def getMaterialSlotNames(staticMesh) -> list[str]:
    staticMeshComponent = unreal.StaticMeshComponent()
    staticMeshComponent.set_static_mesh(staticMesh)
    return unreal.StaticMeshComponent.get_material_slot_names(staticMeshComponent)


def getNierMaterialType(material: dict[str], materialName: str) -> NierMaterialType:
    if "weed" in materialName:
        return NierMaterialType.grass
    elif "tree" in materialName:
        return NierMaterialType.leaves
    elif material.get("g_AlbedoMap") is not None and material.get("g_MaskMap") is None and material.get("g_NormalMap") is None:
        return NierMaterialType.albedoOnly
    elif material.get("g_AlbedoMap") is not None and material.get("g_MaskMap") is not None and material.get("g_NormalMap") is not None:
        return NierMaterialType.simple
    elif (material.get("g_AlbedoMap1") is not None) and (material.get("g_AlbedoMap2") is not None) and (material.get("g_AlbedoMap3") is not None):
        return NierMaterialType.complex
    elif (material.get("g_AlbedoMap1") is not None) and (material.get("g_AlbedoMap2") is not None) and (material.get("g_AlbedoMap3") is None):
        return NierMaterialType.complex2


def swapToOriginalMaterials() -> None:
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    
    for selectedAsset in selectedAssets:
        for matIndex in range(0, selectedAsset.get_num_sections(0)):
            if selectedAsset.get_class().get_name() != "StaticMesh":
                continue

            selectedAssetMaterialName = str(selectedAsset.get_material(matIndex).get_name())
            assetFolder = unreal.Paths.get_path(selectedAsset.get_path_name()) 
            originalMaterial = EditorAssetLibrary.find_asset_data(unreal.Paths.combine([assetFolder, selectedAssetMaterialName[:-5]])).get_asset()
            selectedAsset.set_material(matIndex, originalMaterial)        

def getNierMaterialDict(materialName: str) -> dict:
    for MaterialsJsonPath in MaterialsJsonPaths:
        with open(MaterialsJsonPath, 'r') as file:
            materialsDict = json.load(file)
            if materialsDict.get(materialName) is not None:
                return materialsDict[materialName]

            for dict in materialsDict:
                strDict = str(dict)
                if strDict.find(':') != -1:
                    if strDict[strDict.find(':') + 1:] == materialName:
                        return dict
    return None

def getUniqueMats():
    mats = []
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for selectedAsset in selectedAssets:
        for matIndex in range(0, selectedAsset.get_num_sections(0)):
            if selectedAsset.get_material(matIndex).get_name() not in mats:
                mats.append(selectedAsset.get_material(matIndex).get_name())
    print(len(mats))
    print(mats)

def syncNierMaterials(pngOnly: bool) -> None:
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    postfix = "_Inst"
    #with open(MaterialsJsonPaths, 'r') as file:
    #    materialsDict = json.load(file)

    materialsFolder = UnrealMaterialsDirectory

    texturesFolder = UnrealTexturesDirectory

    if not unreal.EditorAssetLibrary.does_directory_exist(materialsFolder):
        unreal.EditorAssetLibrary.make_directory(materialsFolder)

    if not unreal.EditorAssetLibrary.does_directory_exist(texturesFolder):
        unreal.EditorAssetLibrary.make_directory(texturesFolder)        

    for selectedAsset in selectedAssets:
        if selectedAsset.get_class().get_name() != "StaticMesh":
            continue
       
        if selectedAsset.get_material(0) is None:
            continue
        
        for matIndex in range(0, selectedAsset.get_num_sections(0)):
            selectedAssetMaterialName = str(selectedAsset.get_material(matIndex).get_name())
            if "_ncl" in selectedAssetMaterialName:
                selectedAssetMaterialName = selectedAssetMaterialName[0 : selectedAssetMaterialName.find("_ncl")]
            if postfix in selectedAssetMaterialName:
                print("Nier material is already assigned, skipping Material in " + selectedAsset.get_name())
                continue
            else:
                if unreal.EditorAssetLibrary.does_asset_exist(unreal.Paths.combine([materialsFolder, selectedAssetMaterialName + postfix])): #check, if Nier _Inst asset exist 
                    if EditorAssetLibrary.find_asset_data(unreal.Paths.combine([materialsFolder, selectedAssetMaterialName + postfix])).get_class().get_name() == "ObjectRedirector":
                        print("Redirector asset found instead of material, skipping " + selectedAsset.get_name())
                        continue
                    print("Existing Nier material Inst found, assigning " + selectedAssetMaterialName + postfix + " to " + selectedAsset.get_name())
                    newMaterial = EditorAssetLibrary.find_asset_data(unreal.Paths.combine([materialsFolder, selectedAssetMaterialName + postfix])).get_asset()
                    
                    selectedAsset.set_material(matIndex, newMaterial)
                else: #if Nier material doesn't exist, create it and import textures, then assign 
                    if getNierMaterialDict(selectedAssetMaterialName) is None:
                        unreal.log_warning(selectedAssetMaterialName +" not found in materials.json, skipping asset")
                        continue
                    material = getNierMaterialDict(selectedAssetMaterialName)
                    textures = material['Textures']
                    
                    newMaterial = AssetTools.create_asset(selectedAssetMaterialName + postfix, materialsFolder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                    materialType = getNierMaterialType(textures, selectedAssetMaterialName)
                    
                    if materialType == NierMaterialType.simple or materialType == NierMaterialType.grass or materialType == NierMaterialType.leaves:
                        variables = material['Variables']
                        isDecal = bool(variables['g_Decal']) or "decal" in selectedAssetMaterialName

                        importTextures( [ textures["g_AlbedoMap"], textures["g_MaskMap"], textures["g_NormalMap"], textures["g_DetailNormalMap"] ], texturesFolder, NierMaterialType.simple, isDecal, pngOnly)
                        
                        
                        if materialType == NierMaterialType.simple:
                            parentMaterialAsset = NierBaseSimpleMaterialAsset.get_asset()
                        elif materialType == NierMaterialType.grass:
                            parentMaterialAsset = NierBaseGrassMaterialAsset.get_asset()
                        elif materialType == NierMaterialType.leaves:
                            parentMaterialAsset = NierBaseLeavesMaterialAsset.get_asset()  

                        MaterialEditingLibrary.set_material_instance_parent( newMaterial, parentMaterialAsset )  # set parent material
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_MaskMap", unreal.Paths.combine( [ texturesFolder, textures["g_MaskMap"]] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap"] ] ) ) 
                        
                        if (EditorAssetLibrary.does_asset_exist(unreal.Paths.combine( [ texturesFolder, textures["g_DetailNormalMap"] ] ) )):
                            MaterialEditingLibrary.set_material_instance_scalar_parameter_value( newMaterial, "bUseDetailMap", 1)
                            setMaterialInstanceTextureParameter(newMaterial, "g_DetailNormalMap", unreal.Paths.combine( [ texturesFolder, textures["g_DetailNormalMap"] ] ) )             
                    elif materialType == NierMaterialType.complex:
                        if "testsea" in selectedAssetMaterialName:
                            continue
                        importTextures( [ textures["g_AlbedoMap1"], textures["g_AlbedoMap2"], textures["g_AlbedoMap3"], textures["g_MaskMap"], textures["g_NormalMap1"], textures["g_NormalMap2"], textures["g_NormalMap3"] ], texturesFolder, NierMaterialType.complex, False, pngOnly)
                        MaterialEditingLibrary.set_material_instance_parent( newMaterial, NierBaseComplexMaterialAsset.get_asset() )  # set parent material
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap1", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap1"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap2", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap2"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap3", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap3"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_MaskMap", unreal.Paths.combine( [ texturesFolder, textures["g_MaskMap"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap1", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap1"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap2", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap2"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap3", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap3"] ] ) )
                    elif materialType == NierMaterialType.albedoOnly:
                        importTextures( [ textures["g_AlbedoMap"] ], texturesFolder, NierMaterialType.albedoOnly, False, pngOnly)
                        MaterialEditingLibrary.set_material_instance_parent( newMaterial, NierBaseAlbedoOnlyMaterialAsset.get_asset() )  # set parent material
                        if EditorAssetLibrary.does_asset_exist(unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap"] ] ) ):
                            setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap"] ] ) )
                        else:
                            print("No textures found for " + newMaterial.get_name())
                            continue
                    elif materialType == NierMaterialType.complex2:
                        importTextures( [ textures["g_AlbedoMap1"], textures["g_AlbedoMap2"], textures["g_MaskMap"], textures["g_NormalMap1"], textures["g_NormalMap2"] ], texturesFolder, NierMaterialType.complex2, False, pngOnly)
                        MaterialEditingLibrary.set_material_instance_parent( newMaterial, NierBaseComplex2MaterialAsset.get_asset() )  # set parent material
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap1", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap1"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_AlbedoMap2", unreal.Paths.combine( [ texturesFolder, textures["g_AlbedoMap2"] ] ) )       
                        setMaterialInstanceTextureParameter(newMaterial, "g_MaskMap", unreal.Paths.combine( [ texturesFolder, textures["g_MaskMap"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap1", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap1"] ] ) )
                        setMaterialInstanceTextureParameter(newMaterial, "g_NormalMap2", unreal.Paths.combine( [ texturesFolder, textures["g_NormalMap2"] ] ) )

                    selectedAsset.set_material(matIndex, newMaterial)
    print("Nier Materials syncing end")


def setMobilityForSelectedActors(mobilityType: unreal.ComponentMobility):
    actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    for actor in actors:
        if (actor.get_class().get_name() == "StaticMeshActor"):
            actor.set_mobility(mobilityType)

def test():
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in selectedAssets:
        if asset.get_class().get_name() == "Material" and "_Inst" not in asset.get_name():
            asset.rename(asset.get_name()+"_Inst")

def test2():
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for selectedAsset in selectedAssets:
        if selectedAsset.get_class().get_name() != "StaticMesh":
                continue
        
        for matIndex in range(0, selectedAsset.get_num_sections(0)):
            selectedAssetMaterialName = str(selectedAsset.get_material(matIndex).get_name())
            assetFolder = unreal.Paths.get_path(selectedAsset.get_path_name()) 
            originalMaterial = EditorAssetLibrary.find_asset_data(unreal.Paths.combine([assetFolder, selectedAssetMaterialName[:-5]])).get_asset()

            currentMaterial = selectedAsset.get_material(matIndex)
            
            if currentMaterial.get_class().get_name() == "MaterialInstanceConstant":
                if currentMaterial.parent is None:
                    selectedAsset.set_material(matIndex, originalMaterial)        

            
        #    asset.rename(asset.get_name()+"_Inst")

#Original Blender script by RaiderB
def fixNierMapPosition():
    centerX = 11
    centerY = 10
    hexRadius = 100
    hexCenterToEdge = 50 * sqrt(3)

    def getCoords(x, y) -> Tuple[float, float]:
        x -= 1
        y -= 1
        yOff = floor((23 - x) / 2)
        x -= centerX
        y -= centerY + yOff
        return x * hexRadius*1.5, (-y + x%2/2) * hexCenterToEdge * 2

    def getCoordsFromName(name: str) -> Tuple[int, int]:
        x = int(name[2:4])
        y = int(name[4:6])
        return x, y

    def fixObjPos(obj):   
        if obj.get_actor_label()[:2] == "g5":
            obj.set_actor_transform(new_transform=unreal.Transform(location=[0, 0, 0], rotation=[0, 0, 0], scale=[1, 1, 1]), sweep = False, teleport = False)
            return
        nX, nY = getCoordsFromName(obj.get_actor_label())
        oX, oY = getCoords(nX, nY)
        obj.set_actor_transform(new_transform=unreal.Transform(location=[oX*100, -(oY*100), 0], rotation=[0, 0, 0], scale=[1, 1, 1]), sweep = False, teleport = False )
        print(oX*100, oY*100)

    selectedAssets = unreal.EditorLevelLibrary.get_selected_level_actors()
    
    for obj in selectedAssets:
        print(obj.get_actor_label())
        if not re.match(r"^g\d{5}", obj.get_actor_label()):
            continue
        fixObjPos(obj)
    print("Fixing Nier map position end")
    
    
def generateSimpleCollision():
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    step = 100
    for i in range(0, len(selectedAssets), step):
        print(i)
        time.sleep(3)
        unreal.EditorStaticMeshLibrary.bulk_set_convex_decomposition_collisions(selectedAssets[i:i + step], 20, 20, 400000)
        unreal.EditorAssetLibrary.save_loaded_assets(selectedAssets[i:i + step], False)

def fixBadConvexCollisionForNierStaticMeshes(pathToLogFile: str, searchMask: str):
    pathList = []
    with open(pathToLogFile, "r") as log_file:
        err_gen = (st for st in log_file if searchMask in st)
        for item in err_gen:
            index = item.find(searchMask)
            indexEnd = item.find(".", index)
            path = item[index:indexEnd]
            if path not in pathList:
                print(path)
                pathList.append(path)
    assets = []
    for path in pathList:           
        asset = unreal.EditorAssetLibrary.find_asset_data(path).get_asset()
        assets.append(asset)
        unreal.EditorStaticMeshLibrary.remove_collisions(asset)
        body_setup = asset.get_editor_property('body_setup')
        collision_trace_flag = unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        body_setup.set_editor_property('collision_trace_flag', collision_trace_flag)
        asset.set_editor_property('body_setup', body_setup)
    print("Fixed Collisions for " + len(pathList) + " objects")


def test3():
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in selectedAssets:

        unreal.EditorStaticMeshLibrary.remove_collisions(asset)

def multipleAttenuationRadiusForSelectedLights():
    actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    for actor in actors:
        print(actor.get_class().get_name())
        if actor.get_class().get_name() == "PointLight":
            actor.point_light_component.attenuation_radius = 1


def removeLods() -> None:
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in selectedAssets:
        if asset.get_class().get_name() == "StaticMesh":
            unreal.EditorStaticMeshLibrary.remove_lods(asset)

class NierLight:
    m_flag = 0
    m_pos = [0, 0, 0, 0]
    m_color = [1, 1, 1, 1]
    m_DirAng = [0, 0, 0]
    
#blender X Y Z = Nier X -Z Y

nierLights = []
lightTypes = ['POINT', 'SPOT']
    
def isUniqueSpot(targetNierLight: NierLight):
    for nierLight in nierLights:
        if nierLight.m_pos == targetNierLight.m_pos:
            return False
    return True

def createLights(gadFilesDirectory: str, bImportPointLights: bool, bImportSpotLights: bool, bSkipDuplicatedLights: bool) -> None:
            
    def spawnLight(nierLight: NierLight) -> None:
        if nierLight.m_flag > 2:
            print("Unknown light type found, ID = " + str(nierLight.m_flag))
        nierLight.m_flag = 0
                
        if nierLight.m_flag == 0:    
            nierLightLocation = unreal.Vector( nierLight.m_pos[0] * 100, nierLight.m_pos[2] * 100, nierLight.m_pos[1] * 100 )
            nierLightRotation = [ 0, 0, 0 ]
            lightObj = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, nierLightLocation, nierLightRotation)
            lightObj.set_actor_label("NierLight")
            lightObj.point_light_component.set_light_color(unreal.LinearColor(r=nierLight.m_color[0], g=nierLight.m_color[1], b=nierLight.m_color[2], a=0.0))
            lightObj.point_light_component.set_intensity(nierLight.m_color[3] * 10)
            lightObj.point_light_component.set_cast_shadows(False)

        elif nierLight.m_flag == 1:
            nierLightLocation = unreal.Vector( nierLight.m_pos[0] * 100, nierLight.m_pos[2] * 100, nierLight.m_pos[1] * 100 )
            #nierLightRotation = [ nierLight.m_DirAng[0], nierLight.m_DirAng[2], nierLight.m_DirAng[1] ]
            nierLightRotation = [ 0, 0, 0 ]
            lightObj = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SpotLight, nierLightLocation, nierLightRotation)
            lightObj.set_actor_label("NierLight")
            lightObj.spot_light_component.set_light_color(unreal.LinearColor(r=nierLight.m_color[0], g=nierLight.m_color[1], b=nierLight.m_color[2], a=0.0))
            lightObj.spot_light_component.set_intensity(nierLight.m_color[3] * 10)
            lightObj.spot_light_component.set_cast_shadows(False)
            #lightObj.add_actor_world_rotation(delta_rotation=[-90, 0, 0], sweep=False, teleport=True)
            

        
    import xml.etree.ElementTree as ET
    print("begin")
    files = os.listdir(gadFilesDirectory)
    for file in files:
        if file.endswith(".gad.xml"):
            tree = ET.parse(os.path.join(gadFilesDirectory, file))
            work = tree.find("Work")    
            light = work.find("light")  
            props = light.findall("prop")
            for prop in props:
                if prop.attrib["name"] == "m_RoomLightWork":
                    values = prop.findall("value")
                    for value in values:
                        lightProps = value.findall("prop")
                        nierLight = NierLight()
                        for lightProp in lightProps:
                            if lightProp.attrib["name"] == "m_flag":       
                                nierLight.m_flag = int(lightProp.text)
                            elif lightProp.attrib["name"] == "m_pos":
                                nierLight.m_pos = [float(num) for num in lightProp.text.split(' ')]
                            elif lightProp.attrib["name"] == "m_color":
                                nierLight.m_color = [float(num) for num in lightProp.text.split(' ')]
                            elif lightProp.attrib["name"] == "m_DirAng":
                                nierLight.m_DirAng = [float(num) for num in lightProp.text.split(' ')]
                        if nierLight.m_pos != [0, 0, 0, 1]: #default light position (?) skip
                            if not isUniqueSpot(nierLight) and bSkipDuplicatedLights:
                                continue
                            if nierLight.m_flag == 0 and bImportPointLights:
                               spawnLight(nierLight)
                            if nierLight.m_flag == 1 and bImportSpotLights:
                               spawnLight(nierLight)
                            if bSkipDuplicatedLights:    
                                nierLights.append(nierLight)
                            

def cosolidate():
    print("1")
    assetsDirForReplace = "/AmusementPark/LayAssetsReplace"
    assetsDirOriginal = "/AmusementPark/LayAssetsNew"
    folders = ["g11517_MainArea", "g11617_MainCorridor", "g11716_Theatre", "g11717_TankArea", "g31418_CityRuins1"]
    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for folder in folders:
        assetsForReplace = asset_reg.get_assets_by_path(unreal.Paths.combine([assetsDirForReplace, folder]))

        for asset in assetsForReplace:
            assetToReplace = asset.get_asset()
            assetOriginal = EditorAssetLibrary.find_asset_data(unreal.Paths.combine([assetsDirOriginal, folder, assetToReplace.get_name()])).get_asset()
            
            #print(unreal.Paths.combine([assetsDirForReplace,folder, assetToReplace.get_name()]))
            #print(unreal.Paths.combine([assetsDirForReplace,folder, assetToReplace.get_name()]))
            #print(unreal.Paths.combine([assetsDirOriginal, folder, assetToReplace.get_name()]))
            print(assetOriginal.get_name())
    
            EditorAssetLibrary.consolidate_assets(assetToReplace, [assetOriginal])

def removeSimpleCollision():
    selectedAssets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in selectedAssets:
        unreal.EditorStaticMeshLibrary.remove_collisions(asset)


def exp():
    actorsList = unreal.EditorLevelLibrary.get_all_level_actors()
    actors = []
    for actor in actorsList:
        actorLabel = actor.get_actor_label()
        actorPos = actor.get_actor_location()
        if actorLabel == 'Actor' or actorLabel == 'Actor2':
            actors.append(actor)

    actors[1].attach_to_actor(actors[0],
                            "NAME_None",
                                unreal.AttachmentRule.KEEP_WORLD,
                                unreal.AttachmentRule.KEEP_WORLD,
                                unreal.AttachmentRule.KEEP_WORLD,
                                False)


UnrealMapAssetsFolder = "/Game/NieRAutomata/Maps/MapAssets"
UnrealMapLayFolder = "/Game/NieRAutomata/Maps/LayAssets"

def importNierClusters(baseDirPath: str, fileNamesToImport: list, levelToLoad: str) -> None:
    #we receive file path to folder with meshes and lay assets files
    def importNierCluster(targetFilePath: str) -> bool:
        #we receive fbx file to import
        def importMeshes(filePath: str, destinationAssetPath: str, bCreateSingleBlueprint: bool) -> bool:
            assetName = os.path.basename(filePath).replace(".fbx", '')
            if unreal.EditorAssetLibrary.does_directory_exist(destinationAssetPath):
                print("Found destination path: " + destinationAssetPath + ", skipping file")
                return False
            else:
                unreal.EditorAssetLibrary.make_directory(destinationAssetPath)

            # create asset import data object        
            assetImportData = unreal.AutomatedAssetImportData()
            # set assetImportData attributes
            assetImportData.destination_path = destinationAssetPath
            assetImportData.filenames = [filePath]
                        
            sceneImportFactory = unreal.FbxSceneImportFactory()
            assetImportData.factory = sceneImportFactory
            assetImportData.level_to_load = levelToLoad
            assetImportData.group_name = assetName
            fbxImportDataOptions = unreal.FbxSceneImportOptions()
            sceneImportFactory.scene_import_options = fbxImportDataOptions  

            if bCreateSingleBlueprint:            
                fbxImportDataOptions.set_editor_property('hierarchy_type', unreal.FBXSceneOptionsCreateHierarchyType.FBXSOCHT_CREATE_BLUEPRINT)
            else:
                fbxImportDataOptions.set_editor_property('hierarchy_type', unreal.FBXSceneOptionsCreateHierarchyType.FBXSOCHT_CREATE_LEVEL_ACTORS)   
      
            AssetTools.import_assets_automated(assetImportData)
            return True
        res = True
        assetName = os.path.basename(targetFilePath)
        
        filePath = os.path.join(targetFilePath, assetName + ".fbx")
        if os.path.exists(filePath):
            destinationAssetPath = unreal.Paths.combine([UnrealMapAssetsFolder, assetName])
            res = importMeshes(filePath=filePath, destinationAssetPath=destinationAssetPath, bCreateSingleBlueprint=False)
            #importedAssets.append(assets)
        else:
            print(filePath + " does not exist")
            return False

        filePath = os.path.join(targetFilePath, assetName + "-Lay.fbx")
        if os.path.exists(filePath):
            destinationAssetPath = unreal.Paths.combine([UnrealMapLayFolder, assetName])
            importMeshes(filePath=filePath, destinationAssetPath=destinationAssetPath, bCreateSingleBlueprint=True)
            #importedAssets.extend(assets)
        else:
            print(filePath + " does not exist")

        return res
    
    print("importNierClusters begin")
    for fileName in fileNamesToImport:
        targetPath = os.path.join(baseDirPath, fileName)
        result = importNierCluster(targetFilePath = targetPath)
        if not result:
            continue
        mapClusterParentActorClass = EditorAssetLibrary.find_asset_data("/Game/NieRAutomata/Blueprints/BP_ParentMapClusterActor").get_asset()
        parent = unreal.EditorLevelLibrary.spawn_actor_from_object(mapClusterParentActorClass, unreal.Vector(0, 0, 0), [ 0, 0, 0 ])
        parent.set_actor_label(fileName)
        #root_component 
        actorsList = unreal.EditorLevelLibrary.get_all_level_actors()
        for actor in actorsList:
            #actorLabel = actor.get_actor_label()
            actorLocation = actor.get_actor_location() 
            if actorLocation.x == 0 and actorLocation.y == 0 and actorLocation.z == 0:

                if "Lay" in actor.get_class().get_name():
                    actor.root_component.set_mobility(unreal.ComponentMobility.STATIC)             
                actor.attach_to_actor(parent,
                        "NAME_None",
                            unreal.AttachmentRule.KEEP_WORLD,
                            unreal.AttachmentRule.KEEP_WORLD,
                            unreal.AttachmentRule.KEEP_WORLD,
                            False)
        unreal.EditorLevelLibrary.set_selected_level_actors([parent])
        fixNierMapPosition()


def getClusterNames(filePath: str) -> list:
    fileNames = []
    with open(filePath, 'r') as file:
        for line in file.readlines():
            fileNames.append(line.replace(' ', '').replace('\n', ''))
    return fileNames

#filePath = "G:\\Repositories\\Nier2Unreal\\clustersCityRuinsMain.txt"

#filePath = "G:\\Repositories\\Nier2Unreal\\ClustersCityRuinsOnlyA.txt"

#filePath = "G:\\Repositories\\Nier2Unreal\\ClustersCityRuinsOnlyB.txt"

#clusterNames = getClusterNames(filePath)            
#clusterNames = ['g11021']

#gFilesPath = os.path.join("E:\\3Dprogramms\\NierModding\\NierOverworld\\auto")
#levelName = "NierOverworld"
#levelName = "NierOverworldBeforePart"
#levelName = "NierOverworldAfterPart"
#importNierClusters(gFilesPath, clusterNames, levelName)

#dirPath = "G:\\NierModding\\NierDataNew\\data012.cpk_unpacked\\st1\\nier2blender_extracted\\r130.dat"
#createLights(dirPath, True, True, True)
#createLights("G:\\NierModding\\NierDataNew\\data012.cpk_unpacked\\st1\\nier2blender_extracted\\r130.dat")
#removeLods()
#multipleAttenuationRadiusForSelectedLights()
#swapToOriginalMaterials()
#setMobilityForSelectedActors(unreal.ComponentMobility.MOVABLE)
#swapToOriginalMaterials()


#generateSimpleCollision()

#getUniqueMats()
#test3()
#removeSimpleCollision()

#fixNierMapPosition()
syncNierMaterials(pngOnly=True)
