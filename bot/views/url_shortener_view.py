import discord
import aiohttp

EMOJI_LINK = "<:link:1522140488981942312>"
EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"

SPOO_API_URL = "https://spoo.me/api/v1/shorten"


async def shorten_url(
    long_url: str,
    alias: str = None,
    password: str = None,
    max_clicks: int = None
):
    payload = {"long_url": long_url}

    if alias:
        payload["alias"] = alias

    if password:
        payload["password"] = password

    if max_clicks:
        payload["max_clicks"] = max_clicks

    async with aiohttp.ClientSession() as session:

        async with session.post(
            SPOO_API_URL,
            json=payload
        ) as resp:

            data = await resp.json()

            if resp.status not in (200, 201):
                return None, data.get("error", "Unknown error")

            return data, None


class URLShortenerView(discord.ui.View):

    def __init__(self, data: dict):
        super().__init__(timeout=180)

        self.data = data

        self.add_item(
            discord.ui.Button(
                label="Open shortened link",
                style=discord.ButtonStyle.link,
                url=data["short_url"]
            )
        )

    def create_embed(self):

        desc = (
            f"# {EMOJI_LINK} URL has been shortened\n\n"
            f"{EMOJI_OSS} Original link:\n```{self.data['long_url']}```\n"
            f"{EMOJI_OSS} Shortened link:\n"
            f"```{self.data['short_url']}```\n\n"
            f"Alias: **{self.data['alias']}**\n"
            f"Status: **{self.data['status']}**"
        )

        embed = discord.Embed(
            description=desc,
            color=0x7C3AED
        )

        embed.set_footer(text="spoo.me | url shortener")

        return embed

    @discord.ui.button(
        label="Copy Link",
        style=discord.ButtonStyle.success
    )
    async def copy_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            self.data["short_url"],
            ephemeral=True
        )

    async def on_timeout(self):

        for child in self.children:

            if (
                isinstance(child, discord.ui.Button)
                and child.style != discord.ButtonStyle.link
            ):
                child.disabled = True