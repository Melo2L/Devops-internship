from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo

import pytest

from backend.security.secure_extraction import extract_archive_safely
from backend.security.secure_upload import (
    MAX_EXTRACTED_SIZE,
    MAX_FILES,
    UnsafeArchiveError,
    validate_zip_archive,
)


def create_zip(path: Path, filename: str, content: str = "test") -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(filename, content)


def test_valid_zip_is_accepted() -> None:
    with TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "project.zip"

        create_zip(
            archive_path,
            "src/main.py",
            "print('hello')",
        )

        members = validate_zip_archive(archive_path)

        assert "src/main.py" in members


def test_path_traversal_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "malicious.zip"

        create_zip(
            archive_path,
            "../../evil.txt",
            "malicious content",
        )

        try:
            validate_zip_archive(archive_path)
        except UnsafeArchiveError as exc:
            assert "Unsafe archive path" in str(exc)
        else:
            raise AssertionError("Path traversal archive was not rejected.")


def test_safe_extraction_stays_inside_workspace() -> None:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        archive_path = temp_path / "project.zip"
        workspace = temp_path / "workspace"

        create_zip(
            archive_path,
            "src/main.py",
            "print('hello')",
        )

        from backend.security.secure_extraction import (
            extract_archive_safely,
        )

        extracted_files = extract_archive_safely(
            archive_path,
            workspace,
        )

        extracted_file = workspace / "src" / "main.py"

        assert extracted_file.exists()
        assert extracted_file in extracted_files
        assert extracted_file.read_text() == "print('hello')"


def test_extraction_blocks_path_traversal() -> None:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        archive_path = temp_path / "malicious.zip"
        workspace = temp_path / "workspace"

        create_zip(
            archive_path,
            "../../evil.txt",
            "malicious content",
        )

        from backend.security.secure_extraction import (
            extract_archive_safely,
        )

        try:
            extract_archive_safely(
                archive_path,
                workspace,
            )
        except UnsafeArchiveError as exc:
            assert "Unsafe extraction path" in str(exc)
        else:
            raise AssertionError("Path traversal archive was extracted.")


def test_extraction_rejects_archive_exceeding_size_limit(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "large.zip"
    workspace = tmp_path / "workspace"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "large.txt",
            b"A" * (MAX_EXTRACTED_SIZE + 1),
        )

    try:
        extract_archive_safely(archive_path, workspace)
    except UnsafeArchiveError:
        pass
    else:
        raise AssertionError("An archive exceeding the extraction limit was accepted.")


def test_extraction_rejects_symlink_escape(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "malicious.zip"
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"

    workspace.mkdir()
    outside.mkdir()

    link = workspace / "escape"
    link.symlink_to(outside, target_is_directory=True)

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("escape/evil.txt", "malicious content")

    with pytest.raises(UnsafeArchiveError):
        extract_archive_safely(archive_path, workspace)

    assert not (outside / "evil.txt").exists()


def test_extraction_rejects_too_many_files(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "too_many_files.zip"
    workspace = tmp_path / "workspace"

    with ZipFile(archive_path, "w") as archive:
        for index in range(MAX_FILES + 1):
            archive.writestr(
                f"file_{index}.txt",
                "x",
            )

    with pytest.raises(UnsafeArchiveError, match="too many files"):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_corrupted_zip(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "corrupted.zip"
    workspace = tmp_path / "workspace"

    archive_path.write_bytes(b"This is not a valid ZIP archive")

    with pytest.raises(
        UnsafeArchiveError,
        match="not a valid ZIP archive",
    ):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_null_byte_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_extraction

    archive_path = tmp_path / "invalid_name.zip"
    workspace = tmp_path / "workspace"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("safe.txt", "placeholder")

    class InvalidNameMember:
        filename = "safe\x00.txt"
        external_attr = 0
        file_size = 11

        def is_dir(self) -> bool:
            return False

    class FakeArchive:
        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def infolist(self):
            return [InvalidNameMember()]

    monkeypatch.setattr(
        secure_extraction,
        "ZipFile",
        lambda _: FakeArchive(),
    )

    with pytest.raises(
        UnsafeArchiveError,
        match="invalid filename",
    ):
        extract_archive_safely(archive_path, workspace)


def test_validation_rejects_nonexistent_archive(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "does_not_exist.zip"

    with pytest.raises(
        UnsafeArchiveError,
        match="Archive does not exist",
    ):
        validate_zip_archive(archive_path)


def test_validation_rejects_empty_zip(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "empty.zip"

    with ZipFile(archive_path, "w"):
        pass

    with pytest.raises(
        UnsafeArchiveError,
        match="Archive is empty",
    ):
        validate_zip_archive(archive_path)


def test_validation_rejects_absolute_path(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "absolute_path.zip"

    create_zip(
        archive_path,
        "/tmp/evil.txt",
        "malicious content",
    )

    with pytest.raises(
        UnsafeArchiveError,
        match="Unsafe archive path",
    ):
        validate_zip_archive(archive_path)


def test_validation_rejects_windows_drive_path(tmp_path: Path) -> None:
    archive_path = tmp_path / "windows_path.zip"
    create_zip(archive_path, "C:\\evil.txt")

    with pytest.raises(UnsafeArchiveError, match="Unsafe archive path"):
        validate_zip_archive(archive_path)


def test_validation_rejects_too_many_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "too_many.zip"

    with ZipFile(archive_path, "w") as archive:
        for index in range(MAX_FILES + 1):
            archive.writestr(f"file_{index}.txt", "x")

    with pytest.raises(UnsafeArchiveError, match="too many files"):
        validate_zip_archive(archive_path)


def test_validation_rejects_excessive_uncompressed_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_upload

    archive_path = tmp_path / "large_uncompressed.zip"
    create_zip(archive_path, "large.txt", "x")

    monkeypatch.setattr(secure_upload, "MAX_EXTRACTED_SIZE", 0)

    with pytest.raises(UnsafeArchiveError, match="maximum extracted size"):
        validate_zip_archive(archive_path)


def test_extraction_rejects_windows_drive_path(tmp_path: Path) -> None:
    archive_path = tmp_path / "windows_path.zip"
    workspace = tmp_path / "workspace"
    create_zip(archive_path, "C:\\evil.txt")

    with pytest.raises(UnsafeArchiveError, match="Unsafe extraction path"):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_size_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_extraction

    archive_path = tmp_path / "size_mismatch.zip"
    workspace = tmp_path / "workspace"
    create_zip(archive_path, "file.txt", "content")

    original_zip_file = secure_extraction.ZipFile

    class FakeMember:
        filename = "file.txt"
        external_attr = 0
        file_size = 100

        def is_dir(self) -> bool:
            return False

    class FakeArchive:
        def __init__(self, path: Path) -> None:
            self.archive = original_zip_file(path)

        def __enter__(self):
            self.archive.__enter__()
            return self

        def __exit__(self, *args: object):
            return self.archive.__exit__(*args)

        def infolist(self):
            return [FakeMember()]

        def open(self, member):
            return self.archive.open("file.txt")

    monkeypatch.setattr(
        secure_extraction,
        "ZipFile",
        FakeArchive,
    )

    with pytest.raises(
        UnsafeArchiveError,
        match="does not match ZIP metadata",
    ):
        extract_archive_safely(archive_path, workspace)


def test_validation_rejects_archive_above_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_upload

    archive_path = tmp_path / "oversized.zip"
    create_zip(archive_path, "file.txt", "content")

    monkeypatch.setattr(secure_upload, "MAX_ARCHIVE_SIZE", 1)

    with pytest.raises(UnsafeArchiveError, match="maximum allowed size"):
        validate_zip_archive(archive_path)


def test_validation_rejects_symlink_metadata(tmp_path: Path) -> None:
    import stat

    archive_path = tmp_path / "symlink.zip"

    with ZipFile(archive_path, "w") as archive:
        info = ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target.txt")

    with pytest.raises(UnsafeArchiveError, match="Symbolic link"):
        validate_zip_archive(archive_path)


def test_extraction_creates_explicit_directory(tmp_path: Path) -> None:
    archive_path = tmp_path / "directory.zip"
    workspace = tmp_path / "workspace"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("src/", "")

    extracted = extract_archive_safely(archive_path, workspace)

    assert (workspace / "src").is_dir()
    assert extracted == []


def test_extraction_rejects_actual_size_above_declared_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_extraction

    archive_path = tmp_path / "oversized_content.zip"
    workspace = tmp_path / "workspace"
    create_zip(archive_path, "file.txt", "content")

    original_zip_file = secure_extraction.ZipFile

    class FakeMember:
        filename = "file.txt"
        external_attr = 0
        file_size = 2

        def is_dir(self) -> bool:
            return False

    class FakeArchive:
        def __init__(self, path: Path) -> None:
            self.archive = original_zip_file(path)

        def __enter__(self):
            self.archive.__enter__()
            return self

        def __exit__(self, *args: object):
            return self.archive.__exit__(*args)

        def infolist(self):
            return [FakeMember()]

        def open(self, member):
            return self.archive.open("file.txt")

    monkeypatch.setattr(secure_extraction, "ZipFile", FakeArchive)

    with pytest.raises(UnsafeArchiveError, match="exceeds its declared size"):
        extract_archive_safely(archive_path, workspace)


def test_validation_rejects_empty_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_upload

    class FakeMember:
        filename = ""
        file_size = 0
        external_attr = 0

    class FakeArchive:
        def __enter__(self):
            return self

        def __exit__(self, *args: object):
            return None

        def infolist(self):
            return [FakeMember()]

    monkeypatch.setattr(secure_upload, "ZipFile", lambda path: FakeArchive())

    archive_path = tmp_path / "empty-name.zip"
    archive_path.touch()

    with pytest.raises(UnsafeArchiveError, match="invalid filename"):
        validate_zip_archive(archive_path)


def test_extraction_rejects_nonexistent_archive(tmp_path: Path) -> None:
    archive_path = tmp_path / "missing.zip"
    workspace = tmp_path / "workspace"

    with pytest.raises(UnsafeArchiveError, match="does not exist"):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_symlink_metadata(tmp_path: Path) -> None:
    import stat
    from zipfile import ZipInfo

    archive_path = tmp_path / "symlink.zip"
    workspace = tmp_path / "workspace"

    with ZipFile(archive_path, "w") as archive:
        info = ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target.txt")

    with pytest.raises(UnsafeArchiveError, match="Symbolic link"):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_declared_size_over_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_extraction

    archive_path = tmp_path / "large.zip"
    workspace = tmp_path / "workspace"
    create_zip(archive_path, "file.txt", "content")

    monkeypatch.setattr(secure_extraction, "MAX_EXTRACTED_SIZE", 1)

    with pytest.raises(UnsafeArchiveError, match="maximum extracted size"):
        extract_archive_safely(archive_path, workspace)


def test_extraction_rejects_actual_total_size_over_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.security import secure_extraction

    archive_path = tmp_path / "actual-large.zip"
    workspace = tmp_path / "workspace"
    create_zip(archive_path, "file.txt", "content")

    original_zip_file = secure_extraction.ZipFile

    class FakeMember:
        filename = "file.txt"
        external_attr = 0
        file_size = 2

        def is_dir(self) -> bool:
            return False

    class FakeArchive:
        def __init__(self, path: Path) -> None:
            self.archive = original_zip_file(path)

        def __enter__(self):
            self.archive.__enter__()
            return self

        def __exit__(self, *args: object):
            return self.archive.__exit__(*args)

        def infolist(self):
            return [FakeMember()]

        def open(self, member):
            return self.archive.open("file.txt")

    monkeypatch.setattr(secure_extraction, "ZipFile", FakeArchive)
    monkeypatch.setattr(secure_extraction, "MAX_EXTRACTED_SIZE", 3)

    with pytest.raises(UnsafeArchiveError, match="maximum extracted size"):
        extract_archive_safely(archive_path, workspace)
