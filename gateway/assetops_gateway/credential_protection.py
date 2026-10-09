"""The gateway's own check that its upload-credential file is owner-only (S2-02 Q15).

Provisioning (`backend/.../gateway_credential_file.py`) writes the secret into a
protected file, but the gateway reads whatever path its configuration names.
`D-2026-10-09-s2-pilot-gateway-upload-credential` keeps the secret readable by
the gateway's own account only, so the gateway verifies the EFFECTIVE
protection itself before it reads the secret:

- Windows: the file's DACL is present, protected from inheritance, and every
  access-allowed entry names the current process user; a deny or inherit-only
  entry never widens access; any other entry type (unknown) is refused.
- POSIX: the file is owned by the effective user and grants no group/other bits.

A gateway-local copy of the provisioning validator (the gateway does not import
the backend). `restrict_to_current_user` applies the same owner-only protection;
the gateway itself never writes the credential, so only provisioning tools and
tests call it.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def owner_only_problem(path: Path) -> str | None:
    """None when only the current user can read `path`; otherwise what is wrong."""
    try:
        if sys.platform == "win32":
            return _win_dacl_problem(Path(path))
        info = os.stat(path)
    except OSError as error:
        return f"protection could not be read ({type(error).__name__})"
    if info.st_uid != os.geteuid():
        return "is not owned by the gateway's user"
    if stat.S_IMODE(info.st_mode) & 0o077:
        return f"has mode {oct(stat.S_IMODE(info.st_mode))}, not owner-only (0600)"
    return None


def restrict_to_current_user(path: Path) -> None:
    """Make `path` owner-only (protected single-entry DACL, or mode 0600)."""
    if sys.platform == "win32":
        _win_set_owner_only_dacl(Path(path))
    else:
        os.chmod(path, 0o600)


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


class _WindowsError(Exception):
    pass


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
        raise _WindowsError(f"cannot open the process token ({ctypes.get_last_error()})")
    try:
        needed = wintypes.DWORD()
        advapi.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, _TOKEN_USER, buffer, needed, ctypes.byref(needed)):
            raise _WindowsError(f"cannot read the current user ({ctypes.get_last_error()})")
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
        raise OSError(f"cannot build an owner-only ACL ({ctypes.get_last_error()})")
    error = advapi.SetNamedSecurityInfoW(
        str(path), _SE_FILE_OBJECT, _DACL_SECURITY_INFORMATION | _PROTECTED_DACL_SECURITY_INFORMATION,
        None, None, ctypes.cast(acl, ctypes.c_void_p), None)
    del keep
    if error:
        raise OSError(f"cannot restrict {path} to the current user (Windows error {error})")


def _win_dacl_problem(path: Path) -> str | None:
    try:
        ctypes, wintypes, advapi, kernel = _advapi()
        keep, user = _win_current_user_sid(ctypes, wintypes, advapi, kernel)
    except (_WindowsError, OSError, AttributeError) as error:
        return f"protection could not be checked ({error})"
    owner, group, dacl, sacl, descriptor = (ctypes.c_void_p() for _ in range(5))
    error = advapi.GetNamedSecurityInfoW(
        str(path), _SE_FILE_OBJECT, _OWNER_SECURITY_INFORMATION | _DACL_SECURITY_INFORMATION,
        ctypes.byref(owner), ctypes.byref(group), ctypes.byref(dacl), ctypes.byref(sacl),
        ctypes.byref(descriptor))
    if error:
        return f"has an unreadable security descriptor (Windows error {error})"
    try:
        control, revision = wintypes.WORD(), wintypes.DWORD()
        if not advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)):
            return "has an unreadable security descriptor control"
        if not control.value & _SE_DACL_PRESENT or not dacl.value:
            return "has no DACL (everyone has access)"
        if not control.value & _SE_DACL_PROTECTED:
            return "inherits access from its folder (DACL not protected)"
        ace_count = ctypes.c_ushort.from_address(dacl.value + 4).value  # ACL.AceCount
        for index in range(ace_count):
            ace = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                return "has an unreadable access entry"
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
