import os
import argparse
from pytube import YouTube, Playlist
from moviepy.editor import AudioFileClip
import openai


def download_and_extract_audio(video_url):
    # Download video and extract audio
    yt = YouTube(video_url)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path="temp_audio")
    # Save the audio file
    new_file = out_file.split(".webm")[0] + ".mp3"
    os.rename(out_file, new_file)

    return new_file


def transcribe_audio(file_path):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("The OpenAI API Key is not set in the environment variables.")

    openai.api_key = api_key

    # Load and transcribe the audio file
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            "whisper-1", audio_file, response_format="verbose_json"
        )

    return transcript.get("text")


def transcribe_youtube_video(video_url, output_dir):
    audio_file_path = download_and_extract_audio(video_url)
    text = transcribe_audio(audio_file_path)

    # Clean up the temporary audio file
    os.remove(audio_file_path)

    # Determine a filename based on the video title or URL
    yt = YouTube(video_url)
    file_title = yt.title if yt.title else "transcript"
    filename = f"{file_title}.txt".replace(
        "/", "-"
    )  # Replace / with - to avoid issues with file paths

    # Ensure the output directory exists
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Save the transcript to a file in the specified directory
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as file_out:
        file_out.write(text)

    print(f"Transcript saved to {file_path}")


def get_id_from_url(url):
    # Extracts video or playlist ID from the URL
    if "playlist" in url:
        return url.split("list=")[1]
    else:
        return url.split("v=")[1].split("&")[0]


def main():
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos/playlists.")
    parser.add_argument(
        "url", type=str, help="URL of the YouTube video or playlist to transcribe"
    )
    args = parser.parse_args()

    # Extract ID and create a directory name based on it
    resource_id = get_id_from_url(args.url)
    output_dir = f"transcripts_{resource_id}"

    # Check if it's a playlist
    if "playlist" in args.url:
        playlist = Playlist(args.url)
        for video_url in playlist.video_urls:
            transcribe_youtube_video(video_url, output_dir)
    else:
        transcribe_youtube_video(args.url, output_dir)


if __name__ == "__main__":
    main()
