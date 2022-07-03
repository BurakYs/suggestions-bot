from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from alaric import AQ
from alaric.comparison import EQ

if TYPE_CHECKING:
    from suggestions import State


class GuildConfig:
    def __init__(
        self,
        guild_id: int,
        log_channel_id: Optional[int] = None,
        suggestions_channel_id: Optional[int] = None,
        **kwargs,
    ):
        self.guild_id: int = guild_id
        self.log_channel_id: Optional[int] = log_channel_id
        self.suggestions_channel_id: Optional[int] = suggestions_channel_id

    @classmethod
    async def from_id(cls, guild_id: int, state: State) -> GuildConfig:
        """Returns a valid GuildConfig instance from an id.

        Parameters
        ----------
        guild_id: int
            The guild we want
        state: State
            Internal state to marshall data

        Returns
        -------
        GuildConfig
            The valid guilds config
        """
        guild_config: Optional[GuildConfig] = await state.suggestions_db.find(
            AQ(EQ("guild_id", guild_id))
        )
        if not guild_config:
            return GuildConfig(guild_id=guild_id)

        return guild_config

    def as_dict(self) -> Dict:
        return {
            "guild_id": self.guild_id,
            "log_channel_id": self.log_channel_id,
            "suggestions_channel_id": self.suggestions_channel_id,
        }

    def as_filter(self) -> Dict:
        return {"guild_id": self.guild_id}
