"""3C2 §4's people and Sites, as a plain helper (6a spec §5; handshake I7): tenant `lakeside-power`, the Sites
KISIWA-001, KOBO-001, MTO-001 (MINIGRID) and FRIDGE-001 (COLDCHAIN), and the people below; tenant `other-op` with Zara.
`add_site(tenant_id, code, site_type, site_id)` and `add_person(person_id, name)` register them with a store.
6a's tests use it; 3C2's `World` keeps its own copy until unit 3 moves it here."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from assetops_backend.accounts.model import GrantRow
from assetops_backend.accounts.service import AccountService
from test_3c0a_accounts_service import PW, MemoryStore

SLUG = "lakeside-power"
EXEC, FIN, ANALYST, SM, TECH = ("OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST", "SITE_MANAGER",
                                "FIELD_TECHNICIAN")
T0 = datetime(2026, 11, 20, 9, 30, tzinfo=timezone.utc)


def email(name: str) -> str:
    return f"{name}@lakeside-power.example"


class LakesidePeople:
    def __init__(self, add_site, add_person) -> None:
        self.accounts_store = MemoryStore()
        self.accounts = AccountService(self.accounts_store, clock=lambda: T0)
        self.tenant = self.accounts_store.add_tenant(SLUG, "Lakeside Power")
        self.sites: dict[str, UUID] = {}
        for code, kind in (("KISIWA-001", "MINIGRID"), ("KOBO-001", "MINIGRID"), ("MTO-001", "MINIGRID"),
                           ("FRIDGE-001", "COLDCHAIN")):
            sid = self.accounts_store.add_site(self.tenant, code)
            add_site(self.tenant, code, kind, sid)
            self.sites[code] = sid
        self.people: dict[str, UUID] = {}
        self._add_person = add_person
        self._person(SLUG, email("amina"), "Amina", executive=True)
        for name, role, site in (("Joseph", FIN, None), ("Wanjiru", ANALYST, None), ("Peter", SM, "KOBO-001"),
                                 ("Halima", SM, "KISIWA-001"), ("David", SM, "MTO-001"), ("Musa", TECH, None)):
            self._person(SLUG, email(name.lower()), name)
            self.accounts.onboard_grant(SLUG, email(name.lower()), role, site)
        # Hassan: SITE_MANAGER of MTO-001 and FINANCE_AND_COMMERCIAL_LEAD (spec §5).
        self._person(SLUG, email("hassan"), "Hassan")
        self.accounts.onboard_grant(SLUG, email("hassan"), SM, "MTO-001")
        self.accounts.onboard_grant(SLUG, email("hassan"), FIN, None)
        self.other = self.accounts_store.add_tenant("other-op", "Other Op")
        self._person("other-op", "zara@other-op.example", "Zara", executive=True)

    def _person(self, slug: str, address: str, name: str, *, executive: bool = False) -> UUID:
        pid = self.accounts.onboard_create(slug, address, name, PW, executive=executive)
        self._add_person(pid, name)
        self.people[name] = pid
        return pid
