from __future__ import annotations

import datetime
import random
import string
from enum import Enum
from typing import TYPE_CHECKING, Literal, Union, Optional

import disnake
from alaric import AQ
from alaric.comparison import EQ
from disnake import Embed


if TYPE_CHECKING:
    from suggestions import SuggestionsBot, State


class SuggestionState(Enum):
    open = 0
    approved = 1
    rejected = 2

    @staticmethod
    def from_str(value: str) -> SuggestionState:
        mappings = {
            "open": SuggestionState.open,
            "approved": SuggestionState.approved,
            "rejected": SuggestionState.rejected,
        }
        return mappings[value.lower()]

    def as_str(self) -> str:
        if self is SuggestionState.rejected:
            return "rejected"

        elif self is SuggestionState.approved:
            return "approved"

        return "open"


class Suggestion:
    """An abstract wrapper encapsulating all suggestion functionality."""

    def __init__(
        self,
        guild_id: int,
        suggestion: str,
        suggestion_id: str,
        suggestion_author_id: int,
        created_at: datetime.datetime,
        state: Union[Literal["open", "approved", "rejected"], SuggestionState],
        *,
        channel_id: Optional[int] = None,
        message_id: Optional[int] = None,
        resolved_by: Optional[int] = None,
        resolved_at: Optional[datetime.datetime] = None,
        **kwargs,
    ):
        """

        Parameters
        ----------
        guild_id: int
            The guild this suggestion is in
        suggestion: str
            The suggestion content itself
        suggestion_id: str
            The id of the suggestion
        suggestion_author_id: int
            The id of the person who created the suggestion
        created_at: datetime.datetime
            When this suggestion was created
        state: Union[Literal["open", "approved", "rejected"], SuggestionState]
            The current state of the suggestion itself

        Other Parameters
        ----------------
        resolved_by: Optional[int]
            Who changed the final state of this suggestion
        resolved_at: Optional[datetime.datetime]
            When this suggestion was resolved
        channel_id: Optional[int]
            The channel this suggestion is currently in
        message_id: Optional[int]
            The current message ID. This could be the suggestion
            or the log channel message.
        """
        self.guild_id: int = guild_id
        self.suggestion: str = suggestion
        self.suggestion_id: str = suggestion_id
        self.suggestion_author_id: int = suggestion_author_id
        self.created_at: datetime.datetime = created_at
        self.state: SuggestionState = (
            SuggestionState.from_str(state)
            if not isinstance(state, SuggestionState)
            else state
        )

        self.resolved_by: Optional[int] = resolved_by
        self.resolved_at: Optional[datetime.datetime] = resolved_at

    @property
    def color(self) -> disnake.Color:
        if self.state is SuggestionState.rejected:
            return disnake.Color.red()

        elif self.state is SuggestionState.approved:
            return disnake.Color.green()

        return disnake.Color.yellow()

    @classmethod
    async def from_id(cls, suggestion_id: str, state: State) -> Suggestion:
        """Returns a valid Suggestion instance from an id.

        Parameters
        ----------
        suggestion_id: str
            The suggestion we want
        state: State
            Internal state to marshall data

        Returns
        -------
        Suggestion
            The valid suggestion

        Raises
        ------
        ValueError
            No suggestion found with that id
        """
        suggestion: Optional[Suggestion] = await state.suggestions_db.find(
            AQ(EQ("suggestion_id", suggestion_id))
        )
        if not suggestion:
            raise ValueError(f"No suggestion found with the id {suggestion_id}")

        return suggestion

    @classmethod
    async def new(
        cls,
        suggestion: str,
        guild_id: int,
        author_id: int,
        state: State,
    ) -> Suggestion:
        """Create and return a new valid suggestion.

        Parameters
        ----------
        suggestion: str
            The suggestion content
        guild_id: int
            The guild to attach the suggestion to
        author_id: int
            Who created the suggestion
        state: State
            A back-ref to insert into the database

        Returns
        -------
        Suggestion
            A valid suggestion.
        """
        suggestion_id = state.get_new_suggestion_id()
        suggestion: Suggestion = Suggestion(
            guild_id=guild_id,
            suggestion=suggestion,
            state=SuggestionState.open,
            suggestion_id=suggestion_id,
            suggestion_author_id=author_id,
            created_at=datetime.datetime.now(),
        )
        await state.suggestions_db.insert(suggestion)
        return suggestion

    def as_filter(self) -> dict:
        return {"suggestion_id": self.suggestion_id}

    def as_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "state": self.state.as_str(),
            "suggestion": self.suggestion,
            "suggestion_id": self.suggestion_id,
            "suggestion_author_id": self.suggestion_author_id,
        }

    async def as_embed(self, bot: SuggestionsBot) -> Embed:
        user = await bot.get_or_fetch_user(self.suggestion_author_id)
        return (
            Embed(
                description=f"**Submitter**\n{user.display_name}\n\n"
                f"**Suggestion**\n{self.suggestion}",
                colour=self.color,
            )
            .set_thumbnail(user.display_avatar)
            .set_footer(
                text=f"Author ID: {self.suggestion_author_id} | sID: {self.suggestion_id}"
            )
        )

    async def mark_approved(self, state: State):
        assert state.suggestions_db.collection_name == "suggestions"
        self.state = SuggestionState.approved
        state.remove_sid_from_cache(self.guild_id, self.suggestion_id)
        await state.suggestions_db.update(self, self)

    async def mark_rejected(self, state: State):
        assert state.suggestions_db.collection_name == "suggestions"
        self.state = SuggestionState.rejected
        state.remove_sid_from_cache(self.guild_id, self.suggestion_id)
        await state.suggestions_db.update(self, self)
