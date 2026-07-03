import discord

# Custom emoji IDs used across ScriptBlox embeds.
EMOJI_SCR = "<:favicon:1521916985468780796>"
EMOJI_LUA = "<:luau:1510686322912788590>"
EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"

class ScriptBloxPagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, data: list, search_content: str):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.data = data
        self.search_content = search_content
        self.current_page = 0
        self.total_pages = len(data)

        self.update_buttons()

    def create_embed(self) -> discord.Embed:
        """Build the compact embed for the current page."""
        item = self.data[self.current_page]
        
        title = item.get('title', 'Unknown Title')
        time_created = item.get('createdAt', '').split('T')[0] if item.get('createdAt') else 'Unknown'
        script_code = item.get('script', '')

        game_info = item.get('game', {})
        game_img = game_info.get('image', '')
        banner_url = f"https://scriptblox.com{game_img}" if game_img and game_img.startswith('/') else game_img
        if not banner_url:
            script_img = item.get('image', '')
            banner_url = f"https://scriptblox.com{script_img}" if script_img and script_img.startswith('/') else script_img

        if script_code:
            # Cap the preview length to avoid embed overload; truncate long scripts.
            preview_code = script_code if len(script_code) <= 600 else f"{script_code[:600]}\n-- ... và còn tiếp ..."
            code_block = f"```lua\n{preview_code}\n```"
        else:
            code_block = "```lua\nCannot be found | không thể tìm thấy\n```"

        desc_content = (
            f"# {EMOJI_SCR} Scriptblox.com API\n"
            f"{EMOJI_LUA} {title} {EMOJI_OSS} \n"
            f"creation: {time_created}\n"
            f"{code_block}"
        )

        embed = discord.Embed(description=desc_content, color=0x71368A)
        
        if banner_url:
            embed.set_image(url=banner_url)

        embed.set_footer(text=f"scriptblox | {self.search_content}  •  [{self.current_page + 1}/{self.total_pages}]")
        
        return embed

    def update_buttons(self):
        """Enable/disable nav buttons based on the current page."""
        self.return_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page == self.total_pages - 1

    @discord.ui.button(label="Copy", style=discord.ButtonStyle.success, custom_id="copy_btn")
    async def copy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Secondary button: send the full script as an ephemeral message."""
        item = self.data[self.current_page]
        full_code = item.get('script', 'No code')
        await interaction.response.send_message(
            content=f"\n{full_code}\n", 
            ephemeral=True
        )

    @discord.ui.button(label="◀ Return", style=discord.ButtonStyle.blurple, custom_id="prev_btn")
    async def return_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("Menu này không phải của bạn.", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple, custom_id="next_btn")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("Menu này không phải của bạn.", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except Exception:
            pass
