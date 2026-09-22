from ..constants.us_state_office import ABB_TO_FULL_OFFICE, ABB_TO_FULL_STATE


def check_state(state: str | None) -> str | None:
    """Normalize a state abbreviation or name to its canonical form, or None if unrecognized."""
    if not isinstance(state, str):
        return None
    state = state.lower().strip()
    if not state:
        return None
    if len(state) == 2:
        return ABB_TO_FULL_STATE.get(state)
    return next((v for v in ABB_TO_FULL_STATE.values() if v.lower() == state), None)


def check_office(office: str) -> str | None:
    """Normalize an office abbreviation or name to its canonical form, or None if unrecognized."""
    if not isinstance(office, str):
        return None
    office = office.lower().strip()
    if not office:
        return None
    if len(office) == 1:
        return ABB_TO_FULL_OFFICE.get(office)
    return next((v for v in ABB_TO_FULL_OFFICE.values() if v.lower() == office), None)


def state_abb_to_full(state: str) -> str | None:
    return ABB_TO_FULL_STATE.get(state.lower().strip())


def state_full_to_abb(state: str) -> str | None:
    for k in ABB_TO_FULL_STATE:
        if ABB_TO_FULL_STATE[k].lower().strip() == state.lower().strip():
            return k
    return None
