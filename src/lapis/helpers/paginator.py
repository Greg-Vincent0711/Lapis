from discord import Interaction, ButtonStyle
from discord.ui import View, button

class HelpPaginator(View):
    def __init__(self, embeds):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0

        self.checkPageBoundary()

    def checkPageBoundary(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.embeds) - 1

    @button(emoji="◀️", style=ButtonStyle.secondary)
    async def previous(self, interaction: Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.checkPageBoundary()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @button(emoji="▶️", style=ButtonStyle.secondary)
    async def next(self, interaction: Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.checkPageBoundary()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


