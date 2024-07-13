import argparse
import re
from pathlib import Path
import time
from typing import List, Set, Dict

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract WoW localization strings from Lua files.")
    parser.add_argument("-s", "--source", type=Path, default=Path(__file__).parent,
                        help="Source directory (default: script directory)")
    parser.add_argument("-t", "--target", type=Path,
                        default=Path(__file__).parent / "Dict",
                        help="Target directory (default: 'Dict' in script directory)")
    parser.add_argument("-e", "--exclude", type=str, nargs="+",
                        default=[],
                        help="Additional directories to exclude")
    parser.add_argument("-c", "--encoding", type=str, default="utf-8",
                        help="File encoding (default: utf-8)")
    parser.add_argument("-i", "--identifiers", type=str, default="L,AL,C",
                        help="Comma-separated list of localization string identifiers (default: L,AL,C)")
    return parser.parse_args()

def get_default_excluded_dirs() -> Set[str]:
    return {"language", "lang", "local", "locales", "locale", "locals", "dict", "lib", "libs"}

def extract_localization_strings(file_path: Path, identifiers: List[str], encoding: str) -> Dict[str, str]:
    pattern = rf'({"|".join(map(re.escape, identifiers))})\s*[\[\(](["\'])((?:(?!\2).)*)\2[\]\)]'
    strings: Dict[str, str] = {}
    try:
        with file_path.open("r", encoding=encoding) as file:
            content = file.read()
            matches = re.findall(pattern, content)
            for match in matches:
                key = f'{match[0]}["{match[2]}"]'
                strings[key] = match[2]
    except UnicodeDecodeError:
        print(f"Error: Unable to decode {file_path} with {encoding} encoding.")
    return strings

def process_directory(source_dir: Path, target_file: Path, excluded_dirs: Set[str],
                      identifiers: List[str], encoding: str) -> None:
    all_strings: Dict[str, Dict[str, str]] = {}
    file_count = 0
    start_time = time.time()

    for lua_file in source_dir.rglob("*.lua"):
        if any(excluded.lower() in lua_file.parts for excluded in excluded_dirs):
            continue

        relative_path = lua_file.relative_to(source_dir)
        print(f"Processing: {relative_path}")
        
        strings = extract_localization_strings(lua_file, identifiers, encoding)
        if strings:
            all_strings[str(relative_path)] = strings
        file_count += 1

    with target_file.open("w", encoding=encoding) as out_file:
        for file_path, strings in all_strings.items():
            out_file.write(f"--{file_path}\n")
            for key, value in strings.items():
                out_file.write(f'{key} = "{value}"\n')
            out_file.write("\n")

    end_time = time.time()
    print(f"\nProcessed {file_count} files in {end_time - start_time:.2f} seconds.")
    print(f"Extracted strings saved to: {target_file}")

def main() -> None:
    args = parse_arguments()
    source_dir = args.source.resolve()
    target_dir = args.target.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "localization_strings.lua"

    excluded_dirs = get_default_excluded_dirs().union(set(args.exclude))
    identifiers = args.identifiers.split(",")

    print(f"Source directory: {source_dir}")
    print(f"Target file: {target_file}")
    print(f"Excluded directories: {', '.join(excluded_dirs)}")
    print(f"Identifiers: {', '.join(identifiers)}")
    print(f"Encoding: {args.encoding}")

    process_directory(source_dir, target_file, excluded_dirs, identifiers, args.encoding)

if __name__ == "__main__":
    main()
