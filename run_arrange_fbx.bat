@echo off
echo =============================================
echo  ArrangeFBX - FBX自動処理とアップスケールツール
echo =============================================
echo.

:: 1. PowerShellでファイル選択ダイアログを起動
echo [1/2] 処理対象のFBXファイルを選択してください...
set "INPUT_FBX="
for /f "usebackq tokens=*" %%i in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.OpenFileDialog; $f.Filter = 'FBX Files (*.fbx)|*.fbx|All Files (*.*)|*.*'; $f.Title = '処理対象のFBXファイルを選択してください'; if ($f.ShowDialog() -eq 'OK') { Write-Output $f.FileName }"`) do set "INPUT_FBX=%%i"

:: キャンセル判定
if "%INPUT_FBX%"=="" (
    echo.
    echo [キャンセル] ファイルが選択されませんでした。処理を終了します。
    echo.
    pause
    exit /b
)

echo.
echo 選択されたファイル: "%INPUT_FBX%"
echo.

:: 2. Blenderのパスを探す (デフォルトまたは一般的なインストール先)
set "BLENDER_PATH=blender"
if exist "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
if exist "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
if exist "C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"
if exist "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe" set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
if exist "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" set "BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

:: 3. Blenderスクリプトを実行
echo [2/2] BlenderでFBX細分化と統合処理を実行中...
"%BLENDER_PATH%" --background --python "%~dp0blender_fbx_modifier.py" -- --input="%INPUT_FBX%"

echo.
echo =============================================
echo 処理が完了しました！
echo =============================================
pause
