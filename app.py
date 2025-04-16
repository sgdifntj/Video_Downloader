from flask import Flask, send_file, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from yt_dlp import YoutubeDL
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/downloads'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure download folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 1)
            percent = int(downloaded / total * 100)
            socketio.emit('progress', percent)

    # Updated ydl_opts with FFmpeg-based merging
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'merge_output_format': 'mp4',  # Ensure merging with FFmpeg
        'progress_hooks': [progress_hook],
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    video_path = f"/static/downloads/{filename}"
    return jsonify({'video_path': video_path})

# Serve static files
@app.route('/static/downloads/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    socketio.run(app, debug=True)