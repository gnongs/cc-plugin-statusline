import subprocess


def get_git_info(cwd):
    """Get branch name and file status counts (staged, modified, untracked)."""
    try:
        branch_result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1
        )
        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()
        else:
            # No commits yet — fallback to symbolic-ref
            sym_result = subprocess.run(
                ["git", "-C", cwd, "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True, timeout=1
            )
            if sym_result.returncode != 0:
                return None, 0, 0, 0
            branch = sym_result.stdout.strip()

        status_result = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True, text=True, timeout=2
        )
        staged = modified = untracked = 0
        if status_result.returncode == 0:
            for line in status_result.stdout.splitlines():
                if len(line) < 2:
                    continue
                x, y = line[0], line[1]
                if x == '?' and y == '?':
                    untracked += 1
                else:
                    if x not in (' ', '?'):
                        staged += 1
                    if y not in (' ', '?'):
                        modified += 1

        return branch, staged, modified, untracked
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None, 0, 0, 0
