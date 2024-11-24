# VideoSizeSet

## 概述
VideoSizeSet 是一个用于调整视频文件大小的工具。通过指定目标文件大小，程序会自动调整视频的比特率以达到预期的文件大小。

## 功能特点
- **指定目标文件大小**: 用户可以输入期望的视频文件大小（MB）。
- **自动调整比特率**: 根据目标文件大小自动计算并调整视频的比特率。
- **硬件加速支持**: 支持NVIDIA GPU硬件加速，提高编码速度。
- **多文件处理**: 可以同时处理多个视频文件。

## 安装与使用

### 下载可执行文件
您可以从 [Releases](https://github.com/yourusername/VideoSizeSet/releases) 页面下载预编译的可执行文件：
- `VideoSizeSet_amd64.exe`: 包含 FFmpeg 和 FFprobe 的版本。
- `VideoSizeSet_noffmpeg_amd64.exe`: 不包含 FFmpeg 和 FFprobe 的版本，需要手动安装 FFmpeg 并将其添加到系统 PATH 中。

### 手动编译
如果您希望手动编译源代码，请按照以下步骤操作：

1. **克隆仓库**
    ```sh
    git clone https://github.com/yourusername/VideoSizeSet.git
    cd VideoSizeSet
    ```

2. **安装依赖**
    确保您已经安装了 Python 和 PyQt5。可以通过以下命令安装 PyQt5：
    ```sh
    pip install PyQt5
    ```

3. **运行程序**
    直接运行主脚本：
    ```sh
    python main.py
    ```

4. **打包成可执行文件**
    使用 PyInstaller 打包：
    ```sh
    pyinstaller --onefile --windowed --icon=video.ico --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." --exclude-module PyQt5.uic --exclude-module PyQt5.QtDesigner --exclude-module PyQt5.QtHelp --exclude-module PyQt5.QtWebEngineWidgets --exclude-module PyQt5.QtWebChannel --exclude-module PyQt5.QtNetworkAuth --exclude-module PyQt5.QtSql --exclude-module PyQt5.QtTest --exclude-module PyQt5.QtWebKit --exclude-module PyQt5.QtWebKitWidgets --exclude-module PyQt5.QtXmlPatterns --hidden-import sip --upx-dir=D:\Develop\upx-4.2.4-win64 main.py
    ```

    对于不包含 FFmpeg 和 FFprobe 的版本：
    ```sh
    pyinstaller --onefile --windowed --icon=video.ico --exclude-module PyQt5.uic --exclude-module PyQt5.QtDesigner --exclude-module PyQt5.QtHelp --exclude-module PyQt5.QtWebEngineWidgets --exclude-module PyQt5.QtWebChannel --exclude-module PyQt5.QtNetworkAuth --exclude-module PyQt5.QtSql --exclude-module PyQt5.QtTest --exclude-module PyQt5.QtWebKit --exclude-module PyQt5.QtWebKitWidgets --exclude-module PyQt5.QtXmlPatterns --hidden-import sip --upx-dir=D:\Develop\upx-4.2.4-win64 main.py
    ```

## 依赖项
- **Python 3.x**
- **PyQt5**
- **FFmpeg** (如果选择包含 FFmpeg 的版本)

## 许可证
本项目采用 MIT 许可证。更多详情请参见 [LICENSE](LICENSE) 文件。