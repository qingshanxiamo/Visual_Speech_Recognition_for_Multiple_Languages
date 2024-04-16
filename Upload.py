from flask import Flask, request, jsonify
import os
from plumbum import local
from flask_cors import CORS
import time  # 导入time模块用于生成时间戳

app = Flask(__name__)
CORS(app)


def find_latest_uploaded_mp4():
    uploads_dir = 'uploads'
    mp4_files = [file for file in os.listdir(uploads_dir) if file.endswith('.mp4')]
    latest_file = None
    latest_time = 0

    for file in mp4_files:
        file_path = os.path.join(uploads_dir, file)
        file_mtime = os.path.getmtime(file_path)
        if file_mtime > latest_time:
            latest_time = file_mtime
            latest_file = file_path

    return latest_file


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        # 生成唯一的文件名，这里使用时间戳
        timestamp = int(time.time() * 1000)
        original_filename = file.filename
        extension = original_filename.rsplit('.', 1)[1].lower()
        new_filename = f"{timestamp}.{extension}"

        # 保存文件到上传文件夹
        file.save(os.path.join(UPLOAD_FOLDER, new_filename))
        print("\"message\":\"文件上传成功\"")
        file_mp4_uploaded_new = find_latest_uploaded_mp4()
        print(f"传输文件已找到: {file_mp4_uploaded_new}")

        python = local["python"]
        script_name = "Visual_Speech_Recognition_for_Multiple_Languages/infer.py"
        config_filename = "Visual_Speech_Recognition_for_Multiple_Languages/configs/CMLR_V_WER8.0.ini"
        data_filename = file_mp4_uploaded_new
        detector = "mediapipe"

        cmd = python[
            script_name, f"config_filename={config_filename}", f"data_filename={data_filename}", f"detector={detector}"]
        exit_code, output, stderr = cmd.run(retcode=None)
        print("标准输出:", output)
        print("标准错误:", stderr)

        if exit_code == 0:
            print("生成成功")
            result = output
            print("result=" + result)
            return jsonify({"result": output})
        else:
            print("生成失败")
            return jsonify({"error": "命令执行失败", "stderr": stderr}), 400


if __name__ == '__main__':
    app.run(debug=True)