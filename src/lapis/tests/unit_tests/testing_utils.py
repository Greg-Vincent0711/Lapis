import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from unittest.mock import AsyncMock, MagicMock

def fake_ctx(is_bot=False):
    ctx = MagicMock()
    ctx.author.id = "user123"
    ctx.author.bot = is_bot
    ctx.author.display_name = "Tester"
    ctx.send = AsyncMock()    
    attachment = MagicMock()
    attachment.url = "https://example.com/fake_image.png"
    ctx.message = MagicMock()
    ctx.message.author = ctx.author
    ctx.message.attachments = [attachment]
    return ctx

def mock_interaction(commandName = "nearest"):
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 5
    interaction.user.name = "TestUser"
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.command = MagicMock()
    interaction.command.name = commandName
    return interaction


def mock_interaction_spn(commandName = "spawn_near"):
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 5
    interaction.user.name = "TestUser"
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.command = MagicMock()
    interaction.command.name = commandName
    return interaction