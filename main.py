import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox, QTextEdit, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import subprocess

class FFmpegWorker(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, input_file, output_file, video_bitrate_kbps, audio_bitrate_kbps, use_hardware_acceleration=False):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.video_bitrate_kbps = video_bitrate_kbps
        self.audio_bitrate_kbps = audio_bitrate_kbps
        self.use_hardware_acceleration = use_hardware_acceleration

    def run(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg.exe')
        ffprobe_path = os.path.join(script_dir, 'ffprobe.exe')

        command = [ffmpeg_path, '-y']  # -y to overwrite the output file if it exists

        if self.use_hardware_acceleration:
            command.extend(['-hwaccel', 'cuvid', '-c:v', 'h264_cuvid', '-hwaccel_output_format', 'cuda'])

        command.extend([
            '-i', self.input_file,
            '-c:a', 'aac',
            '-b:a', f'{self.audio_bitrate_kbps}k',
            '-c:v', 'h264_nvenc' if self.use_hardware_acceleration else 'libx264',
            '-b:v', f'{self.video_bitrate_kbps}k',
            self.output_file
        ])

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')

        for line in process.stdout:
            self.log_signal.emit(line.strip())
        
        if process.wait() == 0:
            self.finished.emit(True)
        else:
            self.finished.emit(False)

class VideoBitrateAdjuster(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel('请选择一个或多个MP4文件:', self)
        layout.addWidget(self.label)

        self.select_button = QPushButton('选择文件', self)
        self.select_button.clicked.connect(self.selectFiles)
        layout.addWidget(self.select_button)

        self.target_size_label = QLabel('请输入目标视频大小 (MB):', self)
        layout.addWidget(self.target_size_label)

        self.target_size_input = QLineEdit(self)
        layout.addWidget(self.target_size_input)

        self.start_button = QPushButton('开始任务', self)
        self.start_button.clicked.connect(self.startTasks)
        layout.addWidget(self.start_button)

        self.cancel_button = QPushButton('取消任务', self)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancelTasks)
        layout.addWidget(self.cancel_button)

        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_textedit = QTextEdit(self)
        self.log_textedit.setReadOnly(True)
        self.log_textedit.document().setMaximumBlockCount(100)  # Limit to 100 lines
        layout.addWidget(self.log_textedit)

        self.setLayout(layout)
        self.setWindowTitle('视频码率调整工具')
        self.setGeometry(300, 300, 600, 400)

        self.tasks = []
        self.current_task_index = 0
        self.canceled = False
        self.use_hardware_acceleration = False

    def selectFiles(self):
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "QFileDialog.getOpenFileNames()", "", "MP4 Files (*.mp4);;All Files (*)", options=options)
        if file_paths:
            self.input_files = file_paths
            self.status_label.setText(f'已选择 {len(file_paths)} 个文件')

    def startTasks(self):
        if not hasattr(self, 'input_files') or len(self.input_files) == 0:
            QMessageBox.warning(self, '输入错误', '请先选择一个或多个视频文件。')
            return

        target_size_mb = self.target_size_input.text().strip()

        if not target_size_mb.isdigit():
            QMessageBox.warning(self, '输入错误', '请输入有效的数字作为目标视频大小。')
            return

        target_size_mb = float(target_size_mb)

        original_sizes_mb = [os.path.getsize(file) / (1024 * 1024) for file in self.input_files]

        if any(size <= target_size_mb for size in original_sizes_mb):
            QMessageBox.warning(self, '输入错误', '目标视频大小应小于原始视频大小。')
            return

        self.target_size_bytes = int(target_size_mb * 1024 * 1024)
        self.total_tasks = len(self.input_files)
        self.current_task_index = 0
        self.canceled = False
        self.progress_bar.setValue(0)
        self.checkHardwareAcceleration()
        self.startNextTask()

    def checkHardwareAcceleration(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ffprobe_path = os.path.join(script_dir, 'ffprobe.exe')
            result = subprocess.run([ffprobe_path], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'NVIDIA-SMI' in result.stdout:
                self.use_hardware_acceleration = True
            else:
                self.use_hardware_acceleration = False
        except Exception as e:
            self.use_hardware_acceleration = False

    def cancelTasks(self):
        self.canceled = True
        for task in self.tasks:
            task.terminate()
        self.status_label.setText('任务已取消')
        self.cancel_button.setEnabled(False)

    def startNextTask(self):
        if self.canceled or self.current_task_index >= self.total_tasks:
            self.status_label.setText('所有任务已完成')
            output_dir = os.path.dirname(self.input_files[0])
            QMessageBox.information(self, '任务完成', f'所有的任务已经完成，输出的路径是 {output_dir}')
            self.cancel_button.setEnabled(False)
            return

        input_file = self.input_files[self.current_task_index]
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffprobe_path = os.path.join(script_dir, 'ffprobe.exe')
        try:
            video_duration_seconds = float(subprocess.check_output(
                [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_file]).strip())
            original_video_bitrate_bps = float(subprocess.check_output(
                [ffprobe_path, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=bit_rate', '-of', 'default=noprint_wrappers=1:nokey=1', input_file]).strip())
            audio_bitrate_kbps = float(subprocess.check_output(
                [ffprobe_path, '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=bit_rate', '-of', 'default=noprint_wrappers=1:nokey=1', input_file]).strip()) / 1000
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法获取视频信息: {str(e)}')
            self.current_task_index += 1
            self.startNextTask()
            return

        original_video_bitrate_kbps = original_video_bitrate_bps / 1000
        original_size_bytes = os.path.getsize(input_file)

        size_ratio = self.target_size_bytes / original_size_bytes
        target_video_bitrate_kbps = int(original_video_bitrate_kbps * size_ratio - audio_bitrate_kbps)

        if target_video_bitrate_kbps < 800:
            QMessageBox.warning(self, '警告', f'计算出的目标码率过低 ({target_video_bitrate_kbps} kbps)，请重新设置目标大小。文件 {self.current_task_index + 1}/{self.total_tasks}')
            self.current_task_index += 1
            self.startNextTask()
            return

        output_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_out.mp4")

        self.status_label.setText(f'正在处理... 文件 {self.current_task_index + 1}/{self.total_tasks}')
        self.log_textedit.clear()

        # Single pass encoding with calculated bitrate
        self.ffworker_single_pass = FFmpegWorker(
            self.input_files[self.current_task_index],
            output_file,
            target_video_bitrate_kbps,
            audio_bitrate_kbps,
            self.use_hardware_acceleration
        )
        self.ffworker_single_pass.log_signal.connect(self.updateLog)
        self.ffworker_single_pass.finished.connect(lambda success: self.checkOutputSize(success, target_video_bitrate_kbps, audio_bitrate_kbps, output_file))
        self.ffworker_single_pass.start()
        self.tasks.append(self.ffworker_single_pass)

    def checkOutputSize(self, success, video_bitrate_kbps, audio_bitrate_kbps, output_file):
        if not success:
            QMessageBox.critical(self, '错误', f'编码失败，请检查日志。文件 {self.current_task_index + 1}/{self.total_tasks}')
            self.current_task_index += 1
            self.startNextTask()
            return

        if not os.path.exists(output_file):
            QMessageBox.critical(self, '错误', f'生成文件失败，请检查日志。文件 {self.current_task_index + 1}/{self.total_tasks}')
            self.current_task_index += 1
            self.startNextTask()
            return

        output_size_bytes = os.path.getsize(output_file)

        if output_size_bytes <= self.target_size_bytes:
            self.current_task_index += 1
            self.progress_bar.setValue(int((self.current_task_index / self.total_tasks) * 100))  # Convert to int
            self.startNextTask()
            return

        # Adjust bitrate based on output size
        if output_size_bytes > self.target_size_bytes:
            video_bitrate_kbps *= 0.9
        elif output_size_bytes < self.target_size_bytes:
            video_bitrate_kbps *= 1.05

        video_bitrate_kbps = max(800, min(video_bitrate_kbps, 6000))

        # Retry single pass encoding with adjusted bitrate
        self.startNextTask()

    def updateLog(self, message):
        self.log_textedit.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoBitrateAdjuster()
    ex.show()
    sys.exit(app.exec_())