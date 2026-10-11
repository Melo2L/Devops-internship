from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

# Security limits for uploaded projects.
MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_FILES = 10_000
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024  # 500 MB


class UnsafeArchiveError(Exception):
    """Raised when an uploaded archive violates security rules."""


def validate_zip_archive(archive_path: Path) -> list[str]:
    """
    Validate a ZIP archive before extraction.

    The uploaded project is considered untrusted input.
    This function does not execute any project code.
    """

    if not archive_path.is_file():
        raise UnsafeArchiveError("Archive does not exist.")

    if archive_path.stat().st_size > MAX_ARCHIVE_SIZE:
        raise UnsafeArchiveError("Archive exceeds the maximum allowed size.")

    try:
        with ZipFile(archive_path) as archive:
            members = archive.infolist()

            if not members:
                raise UnsafeArchiveError("Archive is empty.")

            if len(members) > MAX_FILES:
                raise UnsafeArchiveError("Archive contains too many files.")

            total_uncompressed_size = 0
            safe_members: list[str] = []

            for member in members:
                filename = member.filename

                if not filename or "\x00" in filename:
                    raise UnsafeArchiveError("Archive contains an invalid filename.")

                # ZIP paths use POSIX-style separators.
                normalized = filename.replace("\\", "/")
                path = PurePosixPath(normalized)

                # Reject absolute paths and path traversal.
                if path.is_absolute() or ".." in path.parts:
                    raise UnsafeArchiveError(
                        f"Unsafe archive path detected: {filename}"
                    )

                # Reject Windows drive-letter paths.
                if len(normalized) >= 2 and normalized[1] == ":":
                    raise UnsafeArchiveError(
                        f"Unsafe archive path detected: {filename}"
                    )

                # Reject symbolic links.
                file_mode = (member.external_attr >> 16) & 0o170000

                if file_mode == 0o120000:
                    raise UnsafeArchiveError(f"Symbolic link detected: {filename}")

                total_uncompressed_size += member.file_size

                if total_uncompressed_size > MAX_EXTRACTED_SIZE:
                    raise UnsafeArchiveError(
                        "Archive exceeds the maximum extracted size."
                    )

                safe_members.append(normalized)

            return safe_members

    except BadZipFile as exc:
        raise UnsafeArchiveError(
            "The uploaded file is not a valid ZIP archive."
        ) from exc
