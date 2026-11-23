"""Repo checks run by CI on every push.

1. Every SKILL.md starts with YAML frontmatter that has a non-empty `name` and
   `description`, and `name` matches the skill's folder.
2. No media files (audio, video, images) are committed, except the paths in
   MEDIA_ALLOWLIST below (keep it in sync with the `!` exceptions in .gitignore).

Standard library only, so it runs on a bare runner.
"""
import subprocess
import sys
from pathlib import Path

MEDIA_EXT = {
    '.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.opus',
    '.mp4', '.mkv', '.mov', '.webm', '.avi',
    '.png', '.jpg', '.jpeg', '.gif', '.webp',
}
MEDIA_ALLOWLIST = {
    'hinglish-story-reel/assets/ref_voice.wav',  # approved AI narrator reference (Kokoro, Apache-2.0)
}


def tracked_files():
    out = subprocess.run(['git', 'ls-files', '-z'], capture_output=True, text=True, check=True).stdout
    return [f for f in out.split('\0') if f]


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == '---':
            return fields
        if ':' in line and not line.startswith((' ', '\t')):
            key, _, val = line.partition(':')
            fields[key.strip()] = val.strip().strip('"\'')
    return None  # never closed


def main():
    errors = []
    files = tracked_files()

    skills = [f for f in files if Path(f).name == 'SKILL.md']
    if not skills:
        errors.append('no SKILL.md files found')
    for f in skills:
        fm = frontmatter(Path(f).read_text(encoding='utf-8'))
        if fm is None:
            errors.append(f'{f}: missing or unclosed --- frontmatter block')
            continue
        for key in ('name', 'description'):
            if not fm.get(key):
                errors.append(f'{f}: frontmatter has no `{key}`')
        folder = Path(f).parent.name
        if fm.get('name') and fm['name'] != folder:
            errors.append(f'{f}: name `{fm["name"]}` does not match folder `{folder}`')

    for f in files:
        if Path(f).suffix.lower() in MEDIA_EXT and f not in MEDIA_ALLOWLIST:
            errors.append(f'{f}: media file committed (add to MEDIA_ALLOWLIST and .gitignore only if intentional)')

    for e in errors:
        print(f'::error::{e}')
    print(f'checked {len(skills)} SKILL.md files and {len(files)} tracked files: '
          f'{"FAILED" if errors else "ok"}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
