import os
import sys
import argparse
import base64
import json
import urllib.request
import urllib.error
import time

def upscale_image_api(image_path, factor, seamless):
    """
    指定された画像をAPIに送信してアップスケール（高解像度化）する処理。
    ※ Nano Banana Pro 等の実際の画像生成/編集APIエンドポイント仕様に合わせて調整してください。
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set. Skipping API call.")
        return False

    print(f"  [API] Upscaling {os.path.basename(image_path)} (Factor: {factor}x, Seamless: {seamless})")
    
    try:
        with open(image_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"  [API] Error reading image: {e}")
        return False

    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"

    # =========================================================================
    # ▼ TODO: Nano Banana Pro / 画像生成API の実際の仕様に合わせて以下を変更してください ▼
    # =========================================================================
    # 指定された Nano Banana Pro (gemini-3-pro-image-preview) エンドポイント
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={api_key}"
    
    prompt = f"Please upscale this texture image perfectly by {factor}x focusing on preserving fine details."
    if seamless:
        prompt += " Ensure the result is entirely seamless and tileable for 3D PBR materials."

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_string
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')

    # 出力ファイルパスの生成
    base_dir = os.path.dirname(image_path)
    base_name, file_ext = os.path.splitext(os.path.basename(image_path))
    new_image_path = os.path.join(base_dir, f"{base_name}_upscaled{file_ext}")

    max_retries = 3
    retry_delay_seconds = 45  # 429時のデフォルト待機秒数

    for attempt in range(max_retries):
        try:
            print(f"  [API] Sending request to Nano Banana Pro (Attempt {attempt + 1}/{max_retries})...")
            response = urllib.request.urlopen(req)
            response_data = json.loads(response.read().decode('utf-8'))
            
            # APIレスポンスから画像データを抽出
            candidates = response_data.get('candidates', [])
            if not candidates:
                print(f"  [API] Error: Unexpected API response format")
                return False
                
            parts = candidates[0].get('content', {}).get('parts', [])
            image_b64 = None
            
            for part in parts:
                if 'inlineData' in part and 'data' in part['inlineData']:
                    image_b64 = part['inlineData']['data']
                    break
                elif 'inline_data' in part and 'data' in part['inline_data']:
                    image_b64 = part['inline_data']['data']
                    break
                    
            if image_b64:
                # 取得したBase64文字列をデコードして保存
                image_data = base64.b64decode(image_b64)
                with open(new_image_path, 'wb') as f:
                    f.write(image_data)
                print(f"  [API] Success! Upscaled texture saved to {new_image_path}")
                return True
            else:
                print(f"  [API] Error: No image data found in response.")
                return False
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [API] HTTP 429 Too Many Requests: Rate limit exceeded.")
                if attempt < max_retries - 1:
                    print(f"  [API] Waiting {retry_delay_seconds} seconds before retrying...")
                    time.sleep(retry_delay_seconds)
                    continue
                else:
                    print(f"  [API] Max retries reached. Failed to upscale {os.path.basename(image_path)}")
                    return False
            else:
                print(f"  [API] HTTP Error: {e.code} - {e.reason}")
                if hasattr(e, 'read'):
                    print(f"  [API] Server responded with: {e.read().decode('utf-8')}")
                return False
                
        except urllib.error.URLError as e:
            print(f"  [API] Request Error: {e}")
            if hasattr(e, 'read'):
                print(f"  [API] Server responded with: {e.read().decode('utf-8')}")
            return False
            
        except Exception as e:
            print(f"  [API] Unexpected Error: {e}")
            return False

    return False

def main():
    parser = argparse.ArgumentParser(description="Standalone Texture Upscaler for ArrangeFBX")
    parser.add_argument("--input", type=str, required=True, help="Input FBX file path to process its directory")
    args = parser.parse_args()

    input_fbx = args.input
    fbx_dir = os.path.dirname(os.path.abspath(input_fbx))
    
    # config.jsonの読み込み
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.json")
    
    upscale_textures = False
    upscale_factor = 2
    upscale_seamless = True
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                upscale_textures = config_data.get("upscale_textures", False)
                upscale_factor = config_data.get("upscale_factor", 2)
                upscale_seamless = config_data.get("upscale_seamless", True)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}")
    
    if not upscale_textures:
        print("Upscale is disabled in config.json. Skipping.")
        return

    print("--- Starting Standalone Texture Upscaler ---")
    print(f"Target FBX File: {input_fbx}")
    print(f"Target Directory: {fbx_dir}")
    print(f"Settings: Factor={upscale_factor}x, Seamless={upscale_seamless}")

    # FBXディレクトリ内の画像を検索 (サブフォルダは検索しない)
    supported_exts = ['.png', '.jpg', '.jpeg', '.bmp', '.tga']
    image_files = []
    
    if os.path.isdir(fbx_dir):
        for f in os.listdir(fbx_dir):
            if any(f.lower().endswith(ext) for ext in supported_exts):
                # 既にアップスケール済みのものや、Normal/Roughnessマップを除外する
                fl = f.lower()
                if '_upscaled' in fl or 'norm' in fl or 'rough' in fl or 'metal' in fl:
                    continue
                image_files.append(os.path.join(fbx_dir, f))

    if not image_files:
        print("No eligible base color textures found to upscale.")
        return

    print(f"Found {len(image_files)} textures to process. Starting sequence...")
    
    for i, img_path in enumerate(image_files):
        print(f"\n[Texture {i+1}/{len(image_files)}] Processing: {os.path.basename(img_path)}")
        success = upscale_image_api(img_path, upscale_factor, upscale_seamless)
        
        # 成功した場合のみ、API制限対策として適度なウェイトを入れる
        if success and i < len(image_files) - 1:
            wait_seconds = 15
            print(f"  [System] Waiting {wait_seconds} seconds before next request to avoid rate limits...")
            time.sleep(wait_seconds)

    print("\n--- Texture Upscaler Finished ---")

if __name__ == "__main__":
    main()
