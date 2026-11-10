from unittest.mock import AsyncMock, MagicMock

# Create a mock context with an optional attachment
# has the fields commands expect without starting a discord session
def fake_ctx(is_bot=False, with_attachment=True):
    ctx = MagicMock()
    ctx.author.id = 123
    ctx.author.bot = is_bot
    ctx.author.display_name = "Tester"
    ctx.send = AsyncMock()
    attachment = MagicMock()
    attachment.url = "https://example.com/fake_image.png"
    attachment.content_type = "image/png"
    ctx.message = MagicMock()
    ctx.message.author = ctx.author
    ctx.message.attachments = [attachment] if with_attachment else []
    return ctx

# the bot always hands the services the Discord id as a string
AUTHOR_ID = "123"

def mock_interaction(commandName="nearest"):
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 5
    interaction.user.display_name = "TestUser"
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.command = MagicMock()
    interaction.command.name = commandName
    return interaction
