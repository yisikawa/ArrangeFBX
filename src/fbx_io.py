import bpy

def clear_scene():
    """Blenderシーンを初期化"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in [bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images, bpy.data.actions]:
        for item in col:
            col.remove(item)

def import_fbx(filepath: str, use_custom_normals: bool = True):
    """FBXファイルをインポート
    
    注意: use_custom_normals のデフォルトは True（Blenderのデフォルト値）。
    False にするとカスタム法線が無視され、メッシュの見た目が変わる場合があります。
    """
    bpy.ops.import_scene.fbx(filepath=filepath, use_custom_normals=use_custom_normals)

def find_armature():
    """シーン内のアーマチュアオブジェクトを検索"""
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None

def export_fbx(filepath: str, settings: dict):
    """FBXファイルをエクスポート"""
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=False,
        global_scale=settings.get("global_scale", 1.0),
        apply_scale_options=settings.get("scale_options", "FBX_SCALE_ALL"),
        axis_forward=settings.get("axis_forward", "-Z"),
        axis_up=settings.get("axis_up", "Y"),
        bake_anim=settings.get("bake_anim", True),
        bake_anim_use_all_bones=settings.get("bake_anim", True),
        add_leaf_bones=settings.get("add_leaf_bones", False),
        mesh_smooth_type=settings.get("mesh_smooth_type", "FACE"),
    )
