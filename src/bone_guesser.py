class BoneGuesser:
    """ヒューリスティックに基づくボーン名自動推測器（Blender bpy専用）"""
    
    def __init__(self, armature_obj, threshold_x=0.05):
        self.armature = armature_obj
        self.threshold_x = threshold_x
        self._mapping = {}
        self._assigned_targets = set()  # 重複防止: 既に割り当てたUEボーン名を記録
    
    def _assign(self, original_name: str, target_name: str) -> bool:
        """重複を防止しながらマッピングを登録。割り当て済みならFalseを返す"""
        if target_name in self._assigned_targets:
            return False
        self._mapping[original_name] = target_name
        self._assigned_targets.add(target_name)
        return True
    
    def guess(self) -> dict:
        """ボーンマッピングを推測して辞書を返す"""
        bones = self.armature.data.bones
        
        # ルートの特定
        root_bones = [b for b in bones if b.parent is None]
        if not root_bones:
            return {}
        
        root = root_bones[0]
        self._assign(root.name, "root")
        
        # 骨盤の特定
        if not root.children:
            return self._mapping.copy()
        
        pelvis = root.children[0]
        self._assign(pelvis.name, "pelvis")
        
        # 背骨チェーンの特定
        self._trace_spine_chain(pelvis)
        
        # 脚の特定（骨盤の左右の子）
        self._identify_legs(pelvis)
        
        # 腕の特定（胸/首付近からの左右の分岐）
        self._identify_arms()
        
        return self._mapping.copy()
    
    def _is_center(self, bone) -> bool:
        """ボーンがセンターライン上にあるか判定"""
        return abs(bone.head_local.x) < self.threshold_x
    
    def _get_side(self, bone) -> str:
        """ボーンの左右を判定"""
        return "_l" if bone.head_local.x > 0 else "_r"
    
    def _trace_spine_chain(self, pelvis):
        """骨盤から上方に背骨チェーンをたどる"""
        current = pelvis
        spine_index = 1
        
        while current.children:
            center_children = [c for c in current.children if self._is_center(c)]
            if not center_children:
                break
            
            next_bone = center_children[0]
            
            # 末端（子なし）= 頭
            if not next_bone.children:
                self._assign(next_bone.name, "head")
                # 現在のボーンが spine_XX ならneckに修正
                if current.name in self._mapping and self._mapping[current.name].startswith("spine"):
                    old_target = self._mapping[current.name]
                    self._assigned_targets.discard(old_target)
                    self._assign(current.name, "neck_01")
                break
            
            # センターの子が1つだけ → まだ背骨
            center_grandchildren = [c for c in next_bone.children if self._is_center(c)]
            side_children = [c for c in next_bone.children if not self._is_center(c)]
            
            if side_children:
                # 分岐がある → ここが首（腕の付け根の上）
                self._assign(next_bone.name, "neck_01")
                # 首の先にセンターの子があれば頭
                if center_grandchildren:
                    head_bone = center_grandchildren[0]
                    self._assign(head_bone.name, "head")
                break
            else:
                self._assign(next_bone.name, f"spine_{spine_index:02d}")
                spine_index += 1
            
            current = next_bone
    
    def _identify_legs(self, pelvis):
        """骨盤から左右に伸びる脚を特定"""
        for child in pelvis.children:
            if self._is_center(child):
                continue  # 背骨方向はスキップ
            
            side = self._get_side(child)
            self._assign(child.name, f"thigh{side}")
            
            # 膝
            if child.children:
                calf = child.children[0]
                self._assign(calf.name, f"calf{side}")
                # 足首
                if calf.children:
                    foot = calf.children[0]
                    self._assign(foot.name, f"foot{side}")
    
    def _identify_arms(self):
        """背骨/首からの左右の分岐を腕として特定"""
        for original_name, target_name in list(self._mapping.items()):
            if not (target_name.startswith("spine") or target_name == "neck_01"):
                continue
            
            # 元のボーンオブジェクトを取得
            bone = self.armature.data.bones.get(original_name)
            if bone is None:
                continue
            
            for child in bone.children:
                if child.name in self._mapping:
                    continue  # 既にマッピング済み
                if self._is_center(child):
                    continue  # センターラインはスキップ
                
                side = self._get_side(child)
                self._assign(child.name, f"clavicle{side}")
                
                # 上腕 → 前腕 → 手
                if child.children:
                    upperarm = child.children[0]
                    self._assign(upperarm.name, f"upperarm{side}")
                    if upperarm.children:
                        lowerarm = upperarm.children[0]
                        self._assign(lowerarm.name, f"lowerarm{side}")
                        if lowerarm.children:
                            hand = lowerarm.children[0]
                            self._assign(hand.name, f"hand{side}")
