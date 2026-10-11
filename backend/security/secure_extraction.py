from pathlib import Path
from zipfile import BadZipFile, ZipFile

from backend.security.secure_upload import (
    MAX_ARCHIVE_SIZE,
    MAX_EXTRACTED_SIZE,
    MAX_FILES,
    UnsafeArchiveError,
)


def extract_archive_safely(
    archive_path: Path,
    workspace: Path,
) -> list[Path]:
    """
    Extract a ZIP archive into an isolated workspace.

    The archive is untrusted input. Extraction enforces size and file-count
    limits and rejects unsafe paths and symbolic links.
    No extracted file is executed.
    """

    if not archive_path.is_file():
        raise UnsafeArchiveError("Archive does not exist.")

    if archive_path.stat().st_size > MAX_ARCHIVE_SIZE:
        raise UnsafeArchiveError("Archive exceeds the maximum allowed size.")

    workspace.mkdir(parents=True, exist_ok=True)
    workspace_root = workspace.resolve()

    extracted_files: list[Path] = []
    total_extracted_size = 0

    try:
        with ZipFile(archive_path) as archive:
            members = archive.infolist()

            if len(members) > MAX_FILES:
                raise UnsafeArchiveError("Archive contains too many files.")

            for member in members:
                filename = member.filename

                if not filename or "\x00" in filename:
                    raise UnsafeArchiveError("Archive contains an invalid filename.")

                relative_path = Path(filename.replace("\\", "/"))

                if (
                    relative_path.is_absolute()
                    or ".." in relative_path.parts
                    or (len(filename) >= 2 and filename[1] == ":")
                ):
                    raise UnsafeArchiveError(f"Unsafe extraction path: {filename}")

                file_mode = (member.external_attr >> 16) & 0o170000

                if file_mode == 0o120000:
                    raise UnsafeArchiveError(f"Symbolic link detected: {filename}")

                destination = (workspace_root / relative_path).resolve()

                try:
                    destination.relative_to(workspace_root)
                except ValueError as exc:
                    raise UnsafeArchiveError(
                        f"Unsafe extraction path: {filename}"
                    ) from exc

                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                if total_extracted_size + member.file_size > MAX_EXTRACTED_SIZE:
                    raise UnsafeArchiveError(
                        "Archive exceeds the maximum extracted size."
                    )

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                actual_file_size = 0

                with archive.open(member) as source, destination.open("wb") as target:
                    while chunk := source.read(1024 * 1024):
                        actual_file_size += len(chunk)
                        total_extracted_size += len(chunk)

                        if total_extracted_size > MAX_EXTRACTED_SIZE:
                            raise UnsafeArchiveError(
                                "Archive exceeds the maximum extracted size."
                            )

                        if actual_file_size > member.file_size:
                            raise UnsafeArchiveError(
                                "Extracted file exceeds its declared size."
                            )

                        target.write(chunk)

                if actual_file_size != member.file_size:
                    raise UnsafeArchiveError(
                        "Extracted file size does not match ZIP metadata."
                    )

                extracted_files.append(destination)

    except BadZipFile as exc:
        raise UnsafeArchiveError(
            "The uploaded file is not a valid ZIP archive."
        ) from exc

    return extracted_files
