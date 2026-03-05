import sys
import io

from importlib.metadata import metadata, version, PackageNotFoundError
from importlib.metadata import files
from importlib.metadata import distribution
from pathlib import Path


def get_metadata():
    try:
        meta = metadata("LogSmith")

        # --- Project URLs ---
        project_urls = {}
        for entry in meta.get_all("Project-URL", []):
            if "," in entry:
                label, url = entry.split(",", 1)
                project_urls[label.strip()] = url.strip()

        # Homepage is one of the Project-URL entries
        homepage = project_urls.get("Homepage")

        # Extract license from modern fields
        license_value = (
            meta.get("License")
            or meta.get("License-Expression")
            or meta.get("License-File")
        )

        # Extract author name from Author-email
        author_email_field = meta.get("Author-email")
        author = None
        author_email = None
        if author_email_field:
            # Format: "Name <email>"
            if "<" in author_email_field and ">" in author_email_field:
                name, email = author_email_field.split("<", 1)
                author = name.strip()
                author_email = email.strip(">").strip()
            else:
                author_email = author_email_field

        # --- Keywords ---
        raw_keywords = meta.get("Keywords")
        keywords = [kw.strip() for kw in raw_keywords.split(",")] if raw_keywords else []

        # --- Classifiers ---
        classifiers = meta.get_all("Classifier") or []

        return {
            "name": meta.get("Name"),
            "version": version("LogSmith"),
            "description": meta.get("Summary"),
            "requires_python": meta.get("Requires-Python"),
            "author": author,
            "author_email": author_email,
            # "home_page": homepage,
            "project_urls": project_urls,
            "license": license_value,
            "keywords": keywords,
            "classifiers": classifiers,
        }

    except PackageNotFoundError:
        return {}



def get_license_text() -> str | None:
    try:
        dist = distribution("LogSmith")

        # 1. Real filesystem path to the distribution metadata directory
        # noinspection PyProtectedMember,PyUnresolvedReferences
        dist_info_dir = Path(dist._path)

        # 2. All possible locations for LICENSE
        candidates = [
            dist_info_dir / "LICENSE",                  # editable installs (rare)
            dist_info_dir / "license" / "LICENSE",      # some pip layouts
            dist_info_dir / "licenses" / "LICENSE",     # modern setuptools wheels
        ]

        # 3. Try each location
        for path in candidates:
            if path.is_file():
                return path.read_text(encoding="utf-8")

        # 4. Editable installs: LICENSE may be in project root
        #    Only attempt this if LogSmith is imported from a local path
        # noinspection PyBroadException
        try:
            import LogSmith
            project_root = Path(LogSmith.__file__).resolve().parent.parent
            root_license = project_root / "LICENSE"
            if root_license.is_file():
                return root_license.read_text(encoding="utf-8")
        except Exception:
            pass

        return None

    except PackageNotFoundError:
        return None



def get_file_list():
    # noinspection PyBroadException
    try:
        return [str(f) for f in files("LogSmith")]
    except Exception:
        return []


def _build_tree_from_paths(paths: list[str]):
    tree: dict[str, dict] = {}
    for p in paths:
        if "__pycache__" in p:
            continue
        parts = Path(p).parts
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree


def _render_tree_ascii(tree: dict, prefix: str = "") -> list[str]:
    lines = []
    entries = list(tree.items())
    for i, (name, subtree) in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "\\-- " if is_last else "+-- "
        lines.append(prefix + connector + name)
        if subtree:
            extension = "    " if is_last else "|   "
            lines.extend(_render_tree_ascii(subtree, prefix + extension))
    return lines


def get_logsmith_file_tree(file_list: list[str]) -> str:
    tree = _build_tree_from_paths(file_list)
    return "\n".join(_render_tree_ascii(tree))


def capture_stdout_from_string(text: str) -> str:
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        sys.stdout.write(text)
    finally:
        sys.stdout = old_stdout
    return buffer.getvalue()


def get_file_tree():
    file_list = get_file_list()
    file_tree = get_logsmith_file_tree(file_list)
    captured = capture_stdout_from_string(file_tree)
    return captured
