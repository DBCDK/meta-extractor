import os
import argparse
import random
from typing import List, Tuple
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def split_ids(ids: List[str], train_r: float, val_r: float, seed: int) -> Tuple[List[str], List[str], List[str]]:
    rnd = random.Random(seed)
    ids_shuffled = list(ids)
    rnd.shuffle(ids_shuffled)
    n = len(ids_shuffled)
    n_train = int(round(n * train_r))
    n_val = int(round(n * val_r))

    return (
        ids_shuffled[:n_train],
        ids_shuffled[n_train:n_train + n_val],
        ids_shuffled[n_train + n_val:]
    )


def ensure_subdirs(base: Path):
    subdirs = {}
    for split in ("train", "val", "test"):
        d = base / split
        d.mkdir(parents=True, exist_ok=True)
        subdirs[split] = d
    return subdirs


def copy_or_move(src: Path, dst: Path, do_move: bool):
    if do_move:
        shutil.move(str(src), str(dst))
    else:

        shutil.copy2(src, dst)


def main(text_directory: str, metadata_directory: str, train_ratio: float, val_ratio: float, test_ratio: float,
         seed: int, move: bool, do_not_split_text: bool):
    """
    divide the dataset into train, val, test sets
    :param text_directory: path to directory where text are stored.
    :param metadata_directory: path to directory where metadata json files are stored.
    :param train_ratio: Train ratio (default: 0.8)
    :param val_ratio: Val ratio (default: 0.1)
    :param test_ratio: Test ratio (default: 0.1)
    :param seed: Random seed (default: 42)
    :param move: Move instead of copy.
    :param do_not_split_text: Do not split text files, only metadata.
    :return:
    """
    if not os.path.exists(text_directory):
        raise ValueError(f"Text directory {text_directory} does not exist.")
    if not os.path.exists(metadata_directory):
        raise ValueError(f"Metadata directory {metadata_directory} does not exist.")
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Train, val and test ratios must sum to 1.0")

    pids = []
    for filename in os.listdir(text_directory):
        if filename.endswith(".txt"):
            pid = filename.split(".")[0]
            pids.append(pid)

    train_ids, val_ids, test_ids = split_ids(
        pids, train_ratio, val_ratio, seed
    )

    text_sub = ensure_subdirs(Path(text_directory))
    meta_sub = ensure_subdirs(Path(metadata_directory))

    def handle_ids(id_list, split_name):
        for id_ in id_list:
            if not do_not_split_text:
                txt_src = text_directory / f"{id_}.txt"
                txt_dst = text_sub[split_name] / f"{id_}.txt"
                copy_or_move(txt_src, txt_dst, move)
            json_src = metadata_directory / f"{id_}.json"
            json_src_dan = metadata_directory / f"{id_}_dan.json"
            json_dst = meta_sub[split_name] / f"{id_}.json"
            json_dst_dan = meta_sub[split_name] / f"{id_}_dan.json"
            copy_or_move(json_src, json_dst, move)
            copy_or_move(json_src_dan, json_dst_dan, move)

    handle_ids(train_ids, "train")
    handle_ids(val_ids, "val")
    handle_ids(test_ids, "test")
    logger.info(f"Dataset split into {len(train_ids)} train, {len(val_ids)} val, {len(test_ids)} test samples.")


def cli():
    """Command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text-directory", required=True, type=Path,
                        help="path to directory where text are stored.")
    parser.add_argument(
        "-m", "--metadata-directory", required=True, type=Path,
        help="path to directory where metadata json files are stored."
    )
    parser.add_argument("--train", type=float, default=0.89, help="Train ratio (default: 0.89)")
    parser.add_argument("--val", type=float, default=0.01, help="Val ratio (default: 0.01)")
    parser.add_argument("--test", type=float, default=0.1, help="Test ratio (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--move", action="store_true", help="Move instead of copy.")
    parser.add_argument("--do-not-split-text", action="store_true", help="Do not split text files, only metadata.")
    args = parser.parse_args()
    main(args.text_directory, args.metadata_directory, args.train, args.val, args.test, args.seed, args.move,
         args.do_not_split_text)
