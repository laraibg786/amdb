from __future__ import annotations

import os
import sys
import sysconfig


class AmdbNotFound(FileNotFoundError):
    ...


def find_amdb_bin() -> str:
    """Return the amdb binary path.

    This mirrors Ruff's strategy: look in script directories, adjacent
    package `bin` folder, and common user-install locations.
    """

    exe_suffix = sysconfig.get_config_var("EXE") or ""
    amdb_exe = "amdb" + (exe_suffix or "")

    targets = [
        # scripts dir for current python
        sysconfig.get_path("scripts"),
        # scripts dir for base prefix
        sysconfig.get_path("scripts", vars={"base": sys.base_prefix}),
        # adjacent to module path: ../bin
        _join(_matching_parents(_module_path(), "amdb"), "bin"),
        # above package root (install --prefix)
        _join(_matching_parents(_module_path(), "lib/python*/site-packages/amdb"), "bin"),
        # user scheme scripts (e.g. ~/.local/bin)
        sysconfig.get_path("scripts", scheme=_user_scheme()),
    ]

    seen: list[str] = []
    for target in targets:
        if not target:
            continue
        if target in seen:
            continue
        seen.append(target)
        path = os.path.join(target, amdb_exe)
        if os.path.isfile(path):
            return path

    locations = "\n".join(f" - {t}" for t in seen)
    raise AmdbNotFound(
        f"Could not find the amdb binary in any of the following locations:\n{locations}\n"
    )


def _module_path() -> str | None:
    path = os.path.dirname(__file__)
    return path


def _matching_parents(path: str | None, match: str) -> str | None:
    from fnmatch import fnmatch

    if not path:
        return None
    parts = path.split(os.sep)
    match_parts = match.split("/")
    if len(parts) < len(match_parts):
        return None
    if not all(
        fnmatch(part, match_part) for part, match_part in zip(reversed(parts), reversed(match_parts))
    ):
        return None
    return os.sep.join(parts[:-len(match_parts)])


def _join(path: str | None, *parts: str) -> str | None:
    if not path:
        return None
    return os.path.join(path, *parts)


def _user_scheme() -> str:
    if sys.version_info >= (3, 10):
        return sysconfig.get_preferred_scheme("user")
    if os.name == "nt":
        return "nt_user"
    if sys.platform == "darwin" and getattr(sys, "_framework", False):
        return "osx_framework_user"
    return "posix_user"
