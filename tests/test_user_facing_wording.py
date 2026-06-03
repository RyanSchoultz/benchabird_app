from pathlib import Path


def test_show_day_user_facing_wording_does_not_reference_run_calculate():
    root = Path(__file__).resolve().parents[1]
    checked_paths = [
        root / "views",
        root / "services" / "reports",
        root / "README.md",
    ]

    offenders = []
    for path in checked_paths:
        files = path.rglob("*.py") if path.is_dir() else [path]
        for file in files:
            text = file.read_text(encoding="utf-8")
            if "Run Calculate" in text:
                offenders.append(str(file.relative_to(root)))

    assert offenders == []
