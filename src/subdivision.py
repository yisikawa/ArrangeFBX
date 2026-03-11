import bpy

def merge_by_distance(threshold: float = 0.0001):
    """全メッシュの近傍頂点を統合（サブディビジョン前に実行推奨）
    
    閾値以内の距離にある頂点を結合し、重複頂点やメッシュの縮退を防ぐ。
    """
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        
        # 対象メッシュを選択・アクティブに
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # 編集モードで全頂点を選択して統合
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Blender 2.82+ は merge_by_distance、それ以前は remove_doubles
        # bpy.ops は遅延バインディングのため hasattr が使えない
        try:
            bpy.ops.mesh.merge_by_distance(threshold=threshold)
        except (AttributeError, RuntimeError):
            bpy.ops.mesh.remove_doubles(threshold=threshold)
        
        bpy.ops.object.mode_set(mode='OBJECT')

def apply_subdivision(level: int, apply_to_all: bool = True):
    """メッシュにサブディビジョンモディファイアを適用"""
    if level <= 0:
        return
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
            subsurf.levels = level
            subsurf.render_levels = level
            if not apply_to_all:
                break  # 最初のメッシュのみ

