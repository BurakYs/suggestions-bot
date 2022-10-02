import os
from unittest.mock import AsyncMock

import disnake
import pytest

from causar import Causar, InjectionMetadata

import suggestions
from tests.mocks import MockedSuggestionsMongoManager


@pytest.fixture
async def mocked_database() -> MockedSuggestionsMongoManager:
    return MockedSuggestionsMongoManager()


@pytest.fixture
async def causar(monkeypatch, mocked_database) -> Causar:
    if "./suggestions" not in [x[0] for x in os.walk(".")]:
        monkeypatch.chdir("..")

    # Mock these to avoid Task's complaining after tests end
    monkeypatch.setattr(
        "disnake.ext.commands.common_bot_base.CommonBotBase._fill_owners",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "disnake.ext.commands.interaction_bot_base.InteractionBotBase._prepare_application_commands",
        AsyncMock(),
    )

    bot = await suggestions.create_bot(mocked_database)
    await bot.load_cogs()
    return Causar(bot)  # type: ignore


@pytest.fixture
async def injection_metadata(causar: Causar) -> InjectionMetadata:
    return InjectionMetadata(
        guild_id=881118111967883295, channel_id=causar.faker.generate_snowflake()
    )