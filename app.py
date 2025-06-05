import os
import shutil
import tempfile
from flask import Flask, render_template, request, send_file
from pytubefix import YouTube, Playlist
from moviepy import AudioFileClip
from uuid import uuid4

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_audio(video_url, folder):
    yt = YouTube(video_url)
    title = yt.title
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path=folder)
    base, _ = os.path.splitext(out_file)
    mp3_file = f"{base}.mp3"

    # Convert to MP3
    audio_clip = AudioFileClip(out_file)
    audio_clip.write_audiofile(mp3_file)
    audio_clip.close()

    os.remove(out_file)
    return mp3_file, title


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        is_playlist = "playlist" in url.lower()

        temp_dir = tempfile.mkdtemp()
        files = []
        titles = []

        try:
            if is_playlist:
                pl = Playlist(url)
                for video_url in pl.video_urls:
                    mp3_file, title = download_audio(video_url, temp_dir)
                    files.append(mp3_file)
                    titles.append(title)

                zip_filename = f"{uuid4().hex}.zip"
                zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)
                shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
                return send_file(zip_path, as_attachment=True)
            else:
                mp3_file, title = download_audio(url, temp_dir)
                return send_file(mp3_file, as_attachment=True, download_name=f"{title}.mp3")

        except Exception as e:
            return f"An error occurred: {str(e)}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return render_template("index.html")
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # For Render deployment
    app.run(host="0.0.0.0", port=port)
