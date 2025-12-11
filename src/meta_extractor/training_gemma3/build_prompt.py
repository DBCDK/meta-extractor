import argparse
from pathlib import Path
import json
import tempfile
import io
from typing import Dict, Any


def build_conversation_prompt(text: str, metadata: Dict[str, Any] , prompt: dict):
    """
    Build conversation prompt for training an LLM
    :param text: the input text
    :param metadata: the expected output metadata
    :param prompt: the system and user prompt
    :return: conversation prompt as json
    """
    conversation_prompt = {"conversations": []}
    system_prompt = {"role":"system","content":prompt["system"]}
    user_prompt = {"role": "user", "content": f"{prompt["user"]}\n\nInput:\n{text}"}
    assistant_prompt = {"role":"assistant","content":json.dumps(metadata)}
    conversation_prompt["conversations"].append(system_prompt)
    conversation_prompt["conversations"].append(user_prompt)
    conversation_prompt["conversations"].append(assistant_prompt)
    return conversation_prompt

def main(text_directory: str, metadata_directory: str, danish_metadata: bool, prompt_path: str, output_file: str):
    """
    Build prompt for gemma based on text from pdf and expected metadata output and prompt

    :param text_directory: path to text files
    :param metadata_directory: path to metadata files
    :param danish_metadata: true if the keys in the metadata are danish instead of english
    :param prompt_path: path to prompt JSON
    :param output_file: path to output jsonl file
    """

    text_dir = Path(text_directory)
    meta_dir = Path(metadata_directory)
    out_path = Path(output_file)

    # Read prompt once
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = json.load(f)


    # Prepare temp file in same dir, then atomically rename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                     dir=str(out_path.parent), newline='\n') as tmp:
        tmp_path = Path(tmp.name)

        # Wrap with a buffered TextIO to allow explicit flushes if desired
        with io.TextIOWrapper(tmp.buffer, encoding='utf-8', newline='\n') as buf:
            for i, txt_file in enumerate(sorted(text_dir.glob("*.txt")), 1):
                pid = txt_file.stem #example-1.txt > example-1

                try:
                    # Read text
                    text = txt_file.read_text(encoding="utf-8")

                    # Pick metadata postfix
                    postfix = "_dan.json" if danish_metadata else ".json"
                    meta_file = meta_dir / f"{pid}{postfix}"

                    # Read metadata
                    with open(meta_file, "r", encoding="utf-8") as mf:
                        metadata: Dict[str, Any] = json.load(mf)

                    # Build conversation/payload
                    conversation = build_conversation_prompt(text, metadata, prompt)

                    buf.write(json.dumps(conversation, ensure_ascii=False) + "\n")

                    # Optional: limit data-at-risk if something crashes
                    if i % 1000 == 0:
                        buf.flush()

                except FileNotFoundError as e:
                    # Missing metadata or text—log and continue
                    print(f"SKIP {pid}: {e}")
                    continue
                except json.JSONDecodeError as e:
                    print(f"BAD JSON for {pid}: {e}")
                    continue
                except Exception as e:
                    # Don't kill the whole run because of one file
                    print(f"ERROR processing {pid}: {e}")
                    continue

    # Atomic finalize
    tmp_path.replace(out_path)



def cli():
    """Command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text-directory", required=True, help="path to directory where pdfs texts are stored.")
    parser.add_argument(
        "-m", "--metadata-directory", required=True, help="path to directory where the metadata json files are stored."
    )
    parser.add_argument(
        "-p", "--prompt", help="path to prompt as json"
    )
    parser.add_argument(
        "-d", "--danish_metadata", action="store_true", default=False, help="get metadata with Danish keys"
    )
    parser.add_argument("-o", "--output-file", default="./conversions.jsonl", help="path to where conversation prompt should be written.")
    args = parser.parse_args()
    main(args.text_directory, args.metadata_directory, args.danish_metadata, args.prompt, args.output_file)
