from flask import Flask, request, send_file, after_this_request
import os
import uuid
import time
import shutil
import base64
from flask import jsonify



app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'runs/detect'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        unique_name = str(uuid.uuid4())
        filename = f"{unique_name}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        os.system(f"python3 detect.py --weights weights/best.pt --img 640 --conf 0.1 --source {filepath} --save-txt")

        detect_folders = sorted(
            [os.path.join(RESULT_FOLDER, d) for d in os.listdir(RESULT_FOLDER)],
            key=os.path.getctime,
            reverse=True)

        result_files = os.listdir(detect_folders[0])
        image_files = [f for f in result_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            return "No image found in results", 500

        result_image = os.path.join(detect_folders[0], image_files[0])

        with open(result_image, "rb") as img_file:
          encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(detect_folders[0])
                os.remove(filepath)
            except Exception as e:
                print(f"Cleanup error: {e}")
            return response

        names = ['acne', 'acne-scar', 'pores', 'dark-circle', 'melasma', 'redness']
        annotations = []


        label_path = os.path.join(detect_folders[0], "labels", f"{unique_name}.txt")
        with open(label_path, "r") as f:
         for line in f:
           parts = line.strip().split()
           class_id = int(parts[0])
           label = names[class_id]
           annotations.append(label)


        response = {
        "issues": list(dict.fromkeys(annotations)),
        "image": encoded_string,
        }
        return jsonify(response)

    return '''
    <h1>YOLOv5 Flask Server</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" required>
      <input type="submit" value="Upload">
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
