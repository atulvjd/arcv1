from __future__ import annotations

from agents.base.state import AgentState


class AgentLifecycle:
    """
    Controls and validates an agent's lifecycle.
    """

    _VALID_TRANSITIONS = {
        AgentState.CREATED: {
            AgentState.INITIALIZING,
        },

        AgentState.INITIALIZING: {
            AgentState.READY,
            AgentState.ERROR,
        },

        AgentState.READY: {
            AgentState.RUNNING,
            AgentState.STOPPED,
            AgentState.ERROR,
        },

        AgentState.RUNNING: {
            AgentState.PAUSED,
            AgentState.STOPPED,
            AgentState.ERROR,
        },

        AgentState.PAUSED: {
            AgentState.RUNNING,
            AgentState.STOPPED,
            AgentState.ERROR,
        },

        AgentState.STOPPED: set(),

        AgentState.ERROR: {
            AgentState.STOPPED,
        },
    }

    def __init__(self):
        self._state = AgentState.CREATED

    @property
    def state(self):
        return self._state

    def transition(self, new_state: AgentState):

        allowed = self._VALID_TRANSITIONS[self._state]

        if new_state not in allowed:

            raise RuntimeError(
                f"Invalid transition "
                f"{self._state.name} -> {new_state.name}"
            )

        self._state = new_state

    def initialize(self):
        self.transition(AgentState.INITIALIZING)

    def ready(self):
        self.transition(AgentState.READY)

    def start(self):
        self.transition(AgentState.RUNNING)

    def pause(self):
        self.transition(AgentState.PAUSED)

    def stop(self):
        self.transition(AgentState.STOPPED)

    def error(self):
        self.transition(AgentState.ERROR)