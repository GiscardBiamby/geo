import json
import pickle
import sys
from argparse import ArgumentParser, Namespace
from collections import Counter, OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, cast

import cv2
import numpy as np
import pandas as pd
import PIL.Image as pil_img
from tqdm.auto import tqdm
from tqdm.contrib.bells import tqdm, trange


def sample_frames(args, video_id: str):
    """
    Sample a frame every `args.sample_every_seconds` seconds from the specified video, saving the
    frames to args.out_dir/<video_id>/.
    """
    video_path = (args.video_dir / video_id).with_suffix(".mp4")
    assert video_path.exists(), str(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("could not open :", video_path)
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"num_frames: {num_frames:,}")
    seconds = round(0, 2)
    count = 0
    success = True
    print(video_path)
    while success:
        cap.set(cv2.CAP_PROP_POS_MSEC, (seconds * 1000))
        success, image = cap.read()
        if success:
            frame_out_path = args.out_dir / f"{video_path.stem}/frame_{count:08}-{seconds}s.jpg"
            frame_out_path.parent.mkdir(exist_ok=True, parents=True)
            cv2.imwrite(str(frame_out_path), image)
        seconds = round(seconds + args.sample_every_seconds, 2)
        count += 1
    cap.release()
    print("total frames captured: ", count, ", seconds: ", seconds)


def add_task(tasks, path: Path):
    image = str(path).replace("/shared/gbiamby/geo/screenshots/", "")
    tasks.append(
        {
            "data": {
                "image": f"/data/local-files/?d={image}",
            },
        }
    )


def sample_frames_specific(args, video_id: str, desired_frames=[59.50]):
    """
    Sample a frame every `args.sample_every_seconds` seconds from the specified video, saving the
    frames to args.out_dir/<video_id>/.
    """
    video_path = (args.video_dir / video_id).with_suffix(".mp4")
    assert video_path.exists(), str(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("could not open :", video_path)
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"num_frames: {num_frames:,}")
    desired_frames = [round(t, 2) for t in np.arange(0.0, 118.25, 2.0).tolist()]
    count = 0
    print(video_path)
    tasks_json = []
    for seconds in tqdm(desired_frames, total=len(desired_frames)):
        cap.set(cv2.CAP_PROP_POS_MSEC, (seconds * 1000))
        success, image = cap.read()
        if success:
            frame_out_path = args.out_dir / f"{video_path.stem}/frame_{count:08}-{seconds:08}s.jpg"
            frame_out_path.parent.mkdir(exist_ok=True, parents=True)
            add_task(tasks_json, frame_out_path)
            cv2.imwrite(str(frame_out_path), image)
        count += 1
    cap.release()
    print("total frames captured: ", count)
    json.dump(tasks_json, open(args.out_dir / "tasks.json", "w"))


def main(args: Namespace) -> None:
    assert args.video_dir.exists(), str(args.video_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.video_id:
        # sample_frames(args, args.video_id)
        sample_frames_specific(args, args.video_id)
    else:
        raise NotImplementedError("This code path not fully implemented yet.")
        """
        TODO:
            - Implement some mechanism for choosing which video_id's to sample from. Could just be
            adding command line arg parser support for a list of video_id's or a path to a file with
            video_ids, etc.
        """
        videos = sorted(args.video_dir.glob("**/*.mp4"))
        print("total video files found: ", len(videos))

        for i, video_path in enumerate(videos):
            # if i > 10:
            #     break
            sample_frames(args, video_path.stem)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument(
        "--video_dir",
        type=Path,
        default=Path("/shared/g-luo/geoguessr/videos"),
        help="Path to raw input videos.",
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=Path("/shared/gbiamby/geo/screenshots/test/"),
        help="Where to save the extracted frames.",
    )
    parser.add_argument(
        "--sample_every_seconds",
        type=float,
        default=5.0,
        help="Number of seconds between each sampled frame.",
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=10,
        help="Used to split the work across multiple processes. "
        "This process will only run on videos where: video_idx MOD num_processes == device",
    )
    parser.add_argument(
        "--max_videos",
        type=int,
        default=100,
        help="Max number of videos to process for a given geoguessr train/val/test split",
    )
    parser.add_argument(
        "--fast_debug",
        dest="fast_debug",
        action="store_true",
        help="Only perform detection for a small number of frames in the video.",
    )
    parser.add_argument(
        "--video_id",
        type=str,
        required=True,
        help="video_id to process",
    )

    args = parser.parse_args()
    main(args)
