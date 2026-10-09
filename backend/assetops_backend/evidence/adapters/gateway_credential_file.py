"""The gateway's protected upload-credential file (S2-02 phase 2, corrected phase 3a).

The only place the raw bearer secret is written: once, into the file the gateway
reads as protected configuration (`D-2026-10-09-s2-pilot-gateway-upload-credential`).
Never a database row.

Issuance order (`D-2026-10-09-s2-ingestion-operational-semantics`, Q8):

1. `prepare` creates a NEW versioned file beside the configured path (never the
   configured path itself, so the old usable secret is not overwritten as a
   preparation step), restricts it to the current user, verifies the EFFECTIVE
   protection (POSIX mode/owner, or the Windows DACL), and only then writes the
   secret into it.
2. The caller commits the verifier, revocation and enablement in one transaction.
3. `activate` atomically renames the prepared file onto the configured path (an
   NTFS rename keeps the file's protected DACL) and re-verifies it.

A failure in step 1 or 2 calls `discard`; the configured file is untouched.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


class CredentialFileRefused(Exception):
    """The credential file could not be written or is not owner-only."""


def versioned_path(configured: str, selector: str) -> Path:
    path = Path(configured)
    return path.with_name(f"{path.name}.{selector}")


def prepare(configured: str, selector: str, token: str) -> Path:
    """Write the secret to a new protected versioned path; return that path."""
    path = versioned_path(configured, selector)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
    except OSError as error:
        raise CredentialFileRefused(f"could not create {path}: {type(error).__name__}: {error}") from None
    try:
        _protect(path)
        verify_owner_only(path)
        with open(path, "w", encoding="ascii", newline="\n") as handle:
            handle.write(token + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_text(encoding="ascii").strip() != token:
            raise CredentialFileRefused(f"{path} did not read back the written credential")
    except CredentialFileRefused:
        discard(path)
        raise
    except OSError as error:
        discard(path)
        raise CredentialFileRefused(f"could not write {path}: {type(error).__name__}: {error}") from None
    return path


def activate(prepared: Path, configured: str) -> Path:
    """Atomically move the prepared (protected) file onto the configured path."""
    target = Path(configured)
    try:
        os.replace(prepared, target)
    except OSError as error:
        raise CredentialFileRefused(f"could not move {prepared} to {target}: {type(error).__name__}") from None
    verify_owner_only(target)
    return target


def discard(path: Path) -> None:
    try:
        if path.exists():
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            path.unlink()
    except OSError:
        pass


def _protect(path: Path) -> None:
    if sys.platform == "win32":
        _win_set_owner_only_dacl(path)
    else:
        os.chmod(path, 0o600)


def verify_owner_only(path: Path) -> None:
    """Refuse unless only the current user can read the file (effective protection)."""
    if sys.platform == "win32":
        problem = _win_dacl_problem(path)
    else:
        info = os.stat(path)
        problem = None
        if info.st_uid != os.geteuid():
            problem = "is not owned by the current user"
        elif stat.S_IMODE(info.st_mode) & 0o077:
            problem = f"has mode {oct(stat.S_IMODE(info.st_mode))}, not owner-only"
    if problem:
        raise CredentialFileRefused(f"{path} {problem}")


# --- Windows DACL (ctypes; no pywin32 dependency) ---------------------------------

_SE_FILE_OBJECT = 1
_OWNER_SECURITY_INFORMATION = 0x1
_DACL_SECURITY_INFORMATION = 0x4
_PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
_SE_DACL_PRESENT = 0x0004
_SE_DACL_PROTECTED = 0x1000
_ACCESS_ALLOWED_ACE_TYPE = 0
_ACCESS_DENIED_ACE_TYPE = 1
_INHERIT_ONLY_ACE = 0x08
_FILE_ALL_ACCESS = 0x001F01FF
_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_ACL_REVISION = 2


def _advapi():
    import ctypes
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    vp, dw = ctypes.c_void_p, wintypes.DWORD
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, dw, ctypes.POINTER(wintypes.HANDLE)]
    advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, vp, dw, ctypes.POINTER(dw)]
    advapi.GetLengthSid.argtypes = [vp]
    advapi.GetLengthSid.restype = dw
    advapi.EqualSid.argtypes = [vp, vp]
    advapi.InitializeAcl.argtypes = [vp, dw, dw]
    advapi.AddAccessAllowedAce.argtypes = [vp, dw, dw, vp]
    advapi.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, ctypes.c_int, dw, vp, vp, vp, vp]
    advapi.SetNamedSecurityInfoW.restype = dw
    advapi.GetNamedSecurityInfoW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, dw, ctypes.POINTER(vp),
                                             ctypes.POINTER(vp), ctypes.POINTER(vp), ctypes.POINTER(vp),
                                             ctypes.POINTER(vp)]
    advapi.GetNamedSecurityInfoW.restype = dw
    advapi.GetSecurityDescriptorControl.argtypes = [vp, ctypes.POINTER(wintypes.WORD), ctypes.POINTER(dw)]
    advapi.GetAce.argtypes = [vp, dw, ctypes.POINTER(vp)]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [vp]
    return ctypes, wintypes, advapi, kernel


def _win_current_user_sid(ctypes, wintypes, advapi, kernel):
    """The process token's user SID, held in a buffer the caller keeps alive."""
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        raise CredentialFileRefused(f"cannot open the process token ({ctypes.get_last_error()})")
    try:
        needed = wintypes.DWORD()
        advapi.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, _TOKEN_USER, buffer, needed, ctypes.byref(needed)):
            raise CredentialFileRefused(f"cannot read the current user ({ctypes.get_last_error()})")
    finally:
        kernel.CloseHandle(token)
    sid = ctypes.c_void_p.from_buffer(buffer).value  # TOKEN_USER.User.Sid is the first field
    return buffer, sid


def _win_set_owner_only_dacl(path: Path) -> None:
    ctypes, wintypes, advapi, kernel = _advapi()
    keep, sid = _win_current_user_sid(ctypes, wintypes, advapi, kernel)
    size = 8 + 8 + advapi.GetLengthSid(sid)  # ACL header + ACE header/mask + SID
    acl = ctypes.create_string_buffer(size)
    if not advapi.InitializeAcl(acl, size, _ACL_REVISION) or not advapi.AddAccessAllowedAce(
            acl, _ACL_REVISION, _FILE_ALL_ACCESS, sid):
        raise CredentialFileRefused(f"cannot build an owner-only ACL ({ctypes.get_last_error()})")
    error = advapi.SetNamedSecurityInfoW(
        str(path), _SE_FILE_OBJECT, _DACL_SECURITY_INFORMATION | _PROTECTED_DACL_SECURITY_INFORMATION,
        None, None, ctypes.cast(acl, ctypes.c_void_p), None)
    del keep
    if error:
        raise CredentialFileRefused(f"cannot restrict {path} to the current user (Windows error {error})")


def _win_dacl_problem(path: Path) -> str | None:
    """None when the DACL is present, protected from inheritance, and grants
    access to no SID except the current user's; otherwise what is wrong."""
    ctypes, wintypes, advapi, kernel = _advapi()
    keep, user = _win_current_user_sid(ctypes, wintypes, advapi, kernel)
    owner, group, dacl, sacl, descriptor = (ctypes.c_void_p() for _ in range(5))
    error = advapi.GetNamedSecurityInfoW(
        str(path), _SE_FILE_OBJECT, _OWNER_SECURITY_INFORMATION | _DACL_SECURITY_INFORMATION,
        ctypes.byref(owner), ctypes.byref(group), ctypes.byref(dacl), ctypes.byref(sacl),
        ctypes.byref(descriptor))
    if error:
        return f"has an unreadable security descriptor (Windows error {error})"
    try:
        control, revision = wintypes.WORD(), wintypes.DWORD()
        advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision))
        if not control.value & _SE_DACL_PRESENT or not dacl.value:
            return "has no DACL (everyone has access)"
        if not control.value & _SE_DACL_PROTECTED:
            return "inherits access from its folder (DACL not protected)"
        ace_count = ctypes.c_ushort.from_address(dacl.value + 4).value  # ACL.AceCount
        for index in range(ace_count):
            ace = ctypes.c_void_p()
            advapi.GetAce(dacl, index, ctypes.byref(ace))
            ace_type = ctypes.c_ubyte.from_address(ace.value).value
            ace_flags = ctypes.c_ubyte.from_address(ace.value + 1).value
            if ace_type == _ACCESS_DENIED_ACE_TYPE or ace_flags & _INHERIT_ONLY_ACE:
                continue  # a deny or inherit-only entry never widens access to this file
            if ace_type != _ACCESS_ALLOWED_ACE_TYPE:
                return f"has an access entry of unsupported type {ace_type}"
            if not advapi.EqualSid(ctypes.c_void_p(ace.value + 8), user):
                return "grants access to another account"
        return None
    finally:
        kernel.LocalFree(descriptor)
        del keep
