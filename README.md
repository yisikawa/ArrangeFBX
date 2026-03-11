# ArrangeFBX (Blender Modifier Prototype)

提供されたFBXモデル（例: `testFBX/female.fbx`）をロードし、以下の自動調整を行ってUnreal Engine向けに出力するBlender用Pythonスクリプトです。

### 主な機能
1. **スケール変換**：Blenderのエクスポート機能を用いて、Unreal Engine標準のセンチメートル単位へのスケール適用を行います。
2. **ノード階層分析とボーン名の置換**：FBX内の全ボーン階層を解析します。自動推論システムにより、数字のみのボーン名などをUE標準のマネキンボーン名（pelvis, spine_01 等）に自動でマッピング・変換します。また、必要に応じて `presets/ue5_mannequin.json` 等で定義した手動マッピングで上書き可能です。解析結果は `testFBX/bone_analysis.txt` にリスト化されます。
3. **メッシュの細分化 (Subdivision)**: `config.json` の設定に基づき、エクスポート前にメッシュを自動で細分化し、より滑らかなモデルを生成できます。
4. **出力**：ボーンのリネームやメッシュの細分化を行った結果を指定されたFBXとして出力します。

### 実行準備 (Blenderのインストール)
※実行には **Blender 3.x または 4.x** がインストールされている必要があります。
Blenderの実行ファイル（`blender.exe`）にパスが通っているか、あるいはフルパスを指定して実行してください。

### ディレクトリ構成
```
ArrangeFBX/
├── blender_run.py           # Blender用実行スクリプト（メイン）
├── src/                     # Pythonモジュール（設定、ボーン処理、IO等）
├── config.json              # 基本設定ファイル
├── presets/                 # ボーンの手動マッピング辞書ファイル置き場
└── testFBX/                 # FBXデータ・解析結果
```

### 設定ファイル (`config.json`) の使い方
`config.json` を編集することで、入力・出力パスや各処理のパラメータを制御できます。
以下に全セクションの詳細を記載します。

#### `input` — 入力設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `fbx_path` | string | `""` | 入力FBXファイルのパス（スクリプトのディレクトリからの相対パス）。 |
| `use_custom_normals` | bool | `false` | `true` にすると、FBXに含まれるカスタム法線を読み込みます。通常は `false` で問題ありません。 |

#### `output` — 出力設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `fbx_path` | string | `""` | 出力FBXファイルのパス。 |
| `analysis_path` | string | `""` | ボーン解析結果テキストの出力先パス。 |
| `format` | string | `"fbx_binary"` | 出力フォーマット（現在は `fbx_binary` のみ対応）。 |

#### `bone_mapping` — ボーンマッピング設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `preset` | string | `""` | 手動マッピング用のJSONファイルパス（例: `presets/ue5_mannequin.json`）。自動推測結果を上書きします。 |
| `auto_guess_enabled` | bool | `true` | `true` でボーン名の自動推測を有効化。無効にすると手動プリセットのみ使用されます。 |
| `side_detection_threshold` | float | `0.05` | ボーンがセンターライン上にあるかを判定するX座標の閾値（メートル単位）。値を大きくすると、より広い範囲をセンターとみなします。 |

#### `subdivision` — メッシュ細分化設定
| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `level` | int | `0` | サブディビジョンレベル。`0` = 細分化なし、`1` = 1段階（推奨）、`2`以上 = さらに滑らかになるがファイルサイズが急増するため注意。 |
| `apply_to_all_meshes` | bool | `true` | `true` で全メッシュに適用。`false` で最初のメッシュのみに適用。 |

#### `export` — FBXエクスポート設定
Blenderの `bpy.ops.export_scene.fbx` に渡されるパラメータです。Unreal Engine向けのデフォルト値が設定されています。

| キー | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `global_scale` | float | `1.0` | グローバルスケール倍率。UEでは通常 `1.0` のまま、`scale_options` でスケールを制御します。 |
| `scale_options` | string | `"FBX_SCALE_ALL"` | スケール適用方法。`"FBX_SCALE_ALL"` = 全オブジェクトにスケールを適用（UE推奨）。その他: `"FBX_SCALE_NONE"`, `"FBX_SCALE_UNITS"`, `"FBX_SCALE_CUSTOM"`。 |
| `axis_forward` | string | `"-Z"` | FBXの前方軸。UE標準は `"-Z"`。選択肢: `"X"`, `"-X"`, `"Y"`, `"-Y"`, `"Z"`, `"-Z"`。 |
| `axis_up` | string | `"Y"` | FBXの上方軸。UE標準は `"Y"`。選択肢: `"X"`, `"-X"`, `"Y"`, `"-Y"`, `"Z"`, `"-Z"`。 |
| `bake_anim` | bool | `true` | `true` でアニメーションをベイクしてエクスポート。アニメーション不要の場合は `false` に設定するとファイルサイズが小さくなります。 |
| `add_leaf_bones` | bool | `false` | `true` でリーフボーン（末端の追加ボーン）を付加。UEでは通常 `false`（余分なボーンが追加されるのを防ぐため）。 |
| `mesh_smooth_type` | string | `"FACE"` | メッシュのスムージング情報の種類。`"FACE"` = フェースベース（UE推奨）、`"EDGE"` = エッジベース、`"OFF"` = スムージングなし。 |

**`config.json` の全体例:**
```json
{
    "input": {
        "fbx_path": "testFBX/female.fbx",
        "use_custom_normals": false
    },
    "output": {
        "fbx_path": "testFBX/female_ue.fbx",
        "analysis_path": "testFBX/bone_analysis.txt",
        "format": "fbx_binary"
    },
    "bone_mapping": {
        "preset": "presets/ue5_mannequin.json",
        "auto_guess_enabled": true,
        "side_detection_threshold": 0.05
    },
    "subdivision": {
        "level": 1,
        "apply_to_all_meshes": true
    },
    "export": {
        "global_scale": 1.0,
        "scale_options": "FBX_SCALE_ALL",
        "axis_forward": "-Z",
        "axis_up": "Y",
        "bake_anim": true,
        "add_leaf_bones": false,
        "mesh_smooth_type": "FACE"
    }
}
```

### 実行手順

1. コマンドプロンプトまたはPowerShellでこのフォルダに移動します。
2. Blenderをバックグラウンドで起動し、スクリプトを実行します（お使いの環境に合わせてBlenderのパスを指定してください）：

**基本実行:**
```powershell
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py
```

**CLI引数を用いた一時的な上書き実行:**
```powershell
# 入出力ファイルを指定
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py -- -i my_model.fbx -o my_model_ue.fbx

# 解析のみ（エクスポートなし）
& "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background --python blender_run.py -- --dry-run
```

3. スクリプトが完了すると、設定した出力パスにFBXが生成され、ボーン解析ログが出力されます。
