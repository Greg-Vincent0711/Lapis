from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, button

'''
    splits item lists into manageable chunks for pagination
    Returns a list of embeds each containing a slice of the list we want to display
'''
def paginate(itemList, perPage, isCommandBased):
    pages = [itemList[i:i+perPage] for i in range(0, len(itemList), perPage)]
    paginatedItems = []
    for page in pages:
        pageInfo = ""
        if isCommandBased:
            for cmd in page:
                pageInfo += f"**!{cmd.name}** - {cmd.help or 'No description provided.'}\n"
        else:
            for item in page:
                pageInfo += f"- {(item)}\n"
        # 0x115599 is blue
        title = "Lapis' Commands" if isCommandBased else "Saved Locations"
        embed = Embed(title=title, description=pageInfo, color=0x115599)
        paginatedItems.append(embed)
    return paginatedItems
    

# helper class to graphically paginate data
class Paginator(View):
    def __init__(self, embeds):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0

        self.checkPageBoundary()

    def checkPageBoundary(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.embeds) - 1

    @button(emoji="◀️", style=ButtonStyle.secondary)
    async def previous(self, interaction: Interaction, button: button):
        if self.current_page > 0:
            self.current_page -= 1
            self.checkPageBoundary()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @button(emoji="▶️", style=ButtonStyle.secondary)
    # discord lib takes 3 args when calling next and prev
    async def next(self, interaction: Interaction, button: button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.checkPageBoundary()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

