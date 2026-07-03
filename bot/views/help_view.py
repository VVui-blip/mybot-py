import discord
import math

EMOJI_HELP = "<:bloxtrap:1520694122065952940>"
EMOJI_PAGE = "<:emoji_14:1510943251232981093>"
EMOJI_OSS = "<a:loading1:1521615954855985242>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"


class HelpView(discord.ui.View):

    def __init__(
        self,
        bot,
        commands_data,
        author_id
    ):
        super().__init__(timeout=180)

        self.bot = bot
        self.commands_data = commands_data
        self.author_id = author_id

        self.page = 0
        self.per_page = 3

        self.max_page = max(
            1,
            math.ceil(
                len(commands_data)
                / self.per_page
            )
        )

        self.update_buttons()

    def update_buttons(self):

        self.return_btn.disabled = (
            self.page <= 0
        )

        self.next_btn.disabled = (
            self.page >= self.max_page - 1
        )

    def make_embed(self):

        start = (
            self.page
            * self.per_page
        )

        end = (
            start
            + self.per_page
        )

        current = self.commands_data[
            start:end
        ]

        cmd_text = ""

        for name, desc in current:

            cmd_text += (
                f"{EMOJI_OSS} `/{name}`\n"
                f"> {desc}\n\n"
            )

        embed = discord.Embed(
            description=(
                f"# {EMOJI_HELP} Help Menu\n\n"
                f"{EMOJI_PAGE} "
                f"{self.page + 1}/{self.max_page}\n"
                f"Total Commands: "
                f"**{len(self.commands_data)}**\n"
                f"{cmd_text}"
            ),
            color=0x71368A
        )

        if self.bot.user:

            embed.set_thumbnail(
                url=self.bot.user.display_avatar.url
            )

        embed.set_footer(
            text="help menu"
        )

        return embed

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.author_id
        ):

            await interaction.response.send_message(
                f"{EMOJI_X} Not your menu.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="◀ Return",
        style=discord.ButtonStyle.blurple
    )
    async def return_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.page -= 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.make_embed(),
            view=self
        )

    @discord.ui.button(
        label="Next ▶",
        style=discord.ButtonStyle.blurple
    )
    async def next_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.page += 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.make_embed(),
            view=self
        )

    async def on_timeout(self):

        for child in self.children:

            if isinstance(
                child,
                discord.ui.Button
            ):
                child.disabled = True

        try:

            await self.message.edit(
                view=self
            )

        except:
            pass