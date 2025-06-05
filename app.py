from flask import Flask, render_template, request, send_file
from pytubefix import YouTube, Playlist
from moviepy import AudioFileClip
import os
import shutil
import zipfile
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        link = request.form.get("link")
        is_playlist = "playlist?list=" in link

        try:
            if is_playlist:
                playlist = Playlist(link)
                folder_id = str(uuid.uuid4())  # Unique folder per session
                folder_path = os.path.join(DOWNLOAD_FOLDER, folder_id)
                os.makedirs(folder_path)

                for video in playlist.videos:
                    download_audio(video, folder_path)

                zip_filename = folder_id + ".zip"
                zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)

                # Create zip of all mp3s
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, arcname=file)

                shutil.rmtree(folder_path)  # Clean up mp3 files after zipping

                return render_template("index.html", zip_filename=zip_filename)

            else:
                yt = YouTube(link)
                mp3_path = download_audio(yt, DOWNLOAD_FOLDER)
                return render_template("index.html", title=yt.title, thumbnail=yt.thumbnail_url, filename=os.path.basename(mp3_path))

        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")

def download_audio(yt, output_path):
    stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
    audio_path = stream.download(output_path=output_path)
    base, _ = os.path.splitext(audio_path)
    mp3_path = base + ".mp3"

    clip = AudioFileClip(audio_path)
    clip.write_audiofile(mp3_path)
    clip.close()
    os.remove(audio_path)

    return mp3_path

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
