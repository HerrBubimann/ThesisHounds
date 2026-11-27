"""Bounded subprocess for operator-curated PUBLIC/synthetic PDFs, never private uploads."""

import ctypes
import json
import os
import sys
from pathlib import Path

MEMORY_BYTES = 384 * 1024 * 1024
_JOB = None


def constrain():
    global _JOB
    if os.name == "posix":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    elif os.name == "nt":
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_longlong),
                ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD),
                ("minimum", ctypes.c_size_t),
                ("maximum", ctypes.c_size_t),
                ("active", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class Limits(ctypes.Structure):
            _fields_ = [
                ("basic", Basic),
                ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t),
                ("peak_job", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        _JOB = kernel.CreateJobObjectW(None, None)
        limits = Limits()
        limits.basic.flags = 0x100 | 0x2 | 0x8  # process memory, CPU time, active process count
        limits.basic.process_time = 10 * 10_000_000
        limits.basic.active = 1
        limits.process_memory = MEMORY_BYTES
        if not (
            _JOB
            and kernel.SetInformationJobObject(_JOB, 9, ctypes.byref(limits), ctypes.sizeof(limits))
            and kernel.AssignProcessToJobObject(_JOB, kernel.GetCurrentProcess())
        ):
            raise RuntimeError("PARSER_RESOURCE_LIMIT_UNAVAILABLE")
    else:
        raise RuntimeError("PARSER_PLATFORM_NOT_SUPPORTED")


def main():
    try:
        constrain()
        # Fixed local source directory, independent of caller PYTHONPATH / current directory.
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from app.services.pdf_security import inspect_pdf

        restrict_parser()
        data = sys.stdin.buffer.read(8_000_001)
        pages, inspection = inspect_pdf(data)
        result = {
            "pages": pages,
            "text": "\n".join(pages.values()),
            "warnings": ["NO_OCR_OR_VISUAL_SAFETY_GUARANTEE"],
        }
        if (
            not result["pages"]
            or (not result["text"].strip() and sys.argv[1:] != ["--allow-empty-candidate"])
            or len(result["text"].encode()) > 2_000_000
        ):
            raise ValueError("PARSER_NO_USABLE_BOUNDED_TEXT")
        sys.stdout.buffer.write(
            json.dumps(
                {
                    "pages": result["pages"],
                    "warnings": result["warnings"],
                    "parser": "bounded-pypdf.v1",
                    "resource_limits": "ENFORCED",
                    "security_inspection": inspection,
                },
                ensure_ascii=False,
            ).encode()
        )
        return 0
    except Exception as exc:
        # Never echo parser exceptions, raw PDF data or file names.
        code = (
            "PDF_ACTIVE_CONTENT"
            if str(exc) in {"PDF_ACTIVE_OR_EMBEDDED_CONTENT_DENIED", "PDF_EMBEDDED_FILE_DENIED"}
            else "PUBLIC_PDF_EXTRACTION_REJECTED"
        )
        if str(exc) == "PDF_ENCRYPTED":
            code = "PDF_ENCRYPTED"
        sys.stdout.write(json.dumps({"error": code}))
        return 1


def restrict_parser():
    """Python audit boundary, not a claim of OS sandboxing native extensions."""
    roots = (
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
        Path(__file__).resolve().parents[2],
    )

    def audit(event, args):
        if event.startswith(
            ("socket.", "subprocess.", "os.exec", "os.spawn", "os.posix_spawn")
        ) or event in {
            "os.system",
            "os.remove",
            "os.rename",
            "os.mkdir",
            "os.rmdir",
            "ctypes.dlopen",
        }:
            raise PermissionError("PARSER_OPERATION_DENIED")
        if event == "open":
            path, mode, flags = args
            if isinstance(path, int):
                if path not in {0, 1, 2}:
                    raise PermissionError("PARSER_FD_DENIED")
                return
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) or not any(
                Path(path).resolve().is_relative_to(root) for root in roots
            ):
                raise PermissionError("PARSER_FILE_ACCESS_DENIED")

    sys.addaudithook(audit)


if __name__ == "__main__":
    raise SystemExit(main())
