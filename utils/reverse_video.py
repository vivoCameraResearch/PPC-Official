import os
import torch
import numpy as np
import torchvision
from PIL import Image
import cv2
from pathlib import Path

def save_video(data, images_path, folder=None):
    """
    Save different types of image data as a video.

    Args:
        data: Can be a numpy array, torch tensor, a list of image paths,
              or a list of PIL Image objects.
        images_path: Output video file path.
        folder: Directory path when 'data' is a list of relative image paths.
    """
    if isinstance(data, np.ndarray):
        tensor_data = torch.from_numpy(data).to(torch.uint8)
    elif isinstance(data, torch.Tensor):
        tensor_data = data.detach().cpu().to(torch.uint8)
    elif isinstance(data, list):
        if all(isinstance(x, Image.Image) for x in data):
            images = [np.array(img) for img in data]
            stacked_images = np.stack(images, axis=0)
            tensor_data = torch.from_numpy(stacked_images).to(torch.uint8)
        else:
            folder = [folder] * len(data)
            images = [
                np.array(Image.open(os.path.join(folder_name, path)))
                for folder_name, path in zip(folder, data)
            ]
            stacked_images = np.stack(images, axis=0)
            tensor_data = torch.from_numpy(stacked_images).to(torch.uint8)

    if len(tensor_data.shape) == 4:
        if tensor_data.shape[-1] != 3:
            tensor_data = tensor_data.permute(0, 2, 3, 1)

    torchvision.io.write_video(
        images_path,
        tensor_data,
        fps=9,
        video_codec='h264',
        options={'crf': '10'}
    )

def process_videos(input_folder, output_folder):
    """
    Traverse all video files in a folder and re-save them.

    Args:
        input_folder: Path to the input folder containing videos.
        output_folder: Path to the output folder for saving processed videos.
    """
    os.makedirs(output_folder, exist_ok=True)

    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')

    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(video_extensions):
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, input_folder)
                output_dir = os.path.join(output_folder, relative_path)
                os.makedirs(output_dir, exist_ok=True)

                # Add "reverse_" prefix to the output filename
                output_path = os.path.join(output_dir, f"reverse_{file}")

                try:
                    cap = cv2.VideoCapture(input_path)
                    frames = []

                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        # Resize to 480x720
                        frame = cv2.resize(frame, (720, 480))
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame)

                    cap.release()

                    if frames:
                        # Keep only the first 13 frames
                        frames = frames[:13]
                        # Reverse the frame order
                        frames.reverse()
                        # If fewer than 9 frames, repeat the last frame
                        while len(frames) < 9:
                            frames.append(frames[-1])

                        frames_array = np.stack(frames, axis=0)
                        save_video(frames_array, output_path)
                        print(f"Processed: {input_path} -> {output_path}")
                    else:
                        print(f"Warning: Unable to read frames from {input_path}")

                except Exception as e:
                    print(f"Error processing video {input_path}: {str(e)}")

if __name__ == "__main__":
    input_folder = "view_output/select/right/wst"
    output_folder = "vis/select/wst/right"
    process_videos(input_folder, output_folder)
