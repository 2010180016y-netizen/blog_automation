from enum import Enum
from typing import Set, Dict

class ContentState(str, Enum):
    DRAFT = "DRAFT"
    QA_PASS = "QA_PASS"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"

class StateMachine:
    # Valid transitions: {current_state: {next_states}}
    TRANSITIONS: Dict[ContentState, Set[ContentState]] = {
        ContentState.DRAFT: {ContentState.QA_PASS, ContentState.REJECTED},
        ContentState.QA_PASS: {ContentState.READY, ContentState.REJECTED},
        ContentState.READY: {ContentState.PUBLISHED, ContentState.REJECTED},
        ContentState.REJECTED: {ContentState.DRAFT},
        ContentState.PUBLISHED: set()  # Terminal state
    }

    @classmethod
    def can_transition(cls, current: ContentState, next_state: ContentState) -> bool:
        return next_state in cls.TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(cls, current: ContentState, next_state: ContentState):
        if not cls.can_transition(current, next_state):
            raise ValueError(f"Invalid state transition: {current} -> {next_state}")
