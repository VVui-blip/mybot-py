import discord
import aiohttp

EMOJI_RBX = "<:roblox:1510869824174034944>"
EMOJI_PAGE = "<:emoji_14:1510943251232981093>"


async def search_assets(keyword: str):

    url = (
        "https://catalog.roproxy.com/v1/search/items/details"
        f"?Category=11"
        f"&Limit=30"
        f"&Keyword={keyword}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as r:

            if r.status != 200:
                return []

            data = await r.json()

    return data.get("data", [])


async def get_thumbnail(asset_id):

    url = (
        "https://thumbnails.roblox.com/v1/assets"
        f"?assetIds={asset_id}"
        "&size=420x420"
        "&format=Png"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as r:

            if r.status != 200:
                return None

            data = await r.json()

    try:
        return data["data"][0]["imageUrl"]
    except:
        return None


class CopyAssetID(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Copy ID",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction):

        asset = self.view.assets[
            self.view.page
        ]

        await interaction.response.send_message(
            str(asset["id"]),
            ephemeral=True
        )


class RobloxAssetView(discord.ui.View):

    def __init__(
        self,
        interaction,
        assets,
        keyword
    ):
        super().__init__(timeout=180)

        self.interaction = interaction
        self.assets = assets
        self.keyword = keyword

        self.page = 0
        self.max_page = len(assets)

        self.add_item(
            CopyAssetID()
        )

        self.update_buttons()

    async def create_embed(self):

        asset = self.assets[
            self.page
        ]

        asset_id = asset.get("id")

        thumbnail = await get_thumbnail(
            asset_id
        )

        name = asset.get(
            "name",
            "Unknown"
        )

        creator = asset.get(
            "creatorName",
            "Unknown"
        )

        description = asset.get(
            "description",
            "No description"
        )

        favorites = asset.get(
            "favoriteCount",
            0
        )

        if len(description) > 800:

            description = (
                description[:800]
                + "..."
            )

        embed = discord.Embed(
            description=(
                f"# {EMOJI_RBX} Roblox Asset\n\n"
                f"{EMOJI_PAGE} {self.page+1}/{self.max_page}\n"
                f"**{name}**\n"
                f"Creator: `{creator}`\n"
                f"Asset ID: `{asset_id}`\n"
                f"Favorites: `{favorites}`\n"
                f"```{description}```"
            ),
            color=0xE2231A
        )

        if thumbnail:

            embed.set_thumbnail(
                url=thumbnail
            )

        embed.set_footer(
            text=f"roblox asset | {self.keyword}"
        )

        return embed

    def update_buttons(self):

        self.return_btn.disabled = (
            self.page <= 0
        )

        self.next_btn.disabled = (
            self.page >= self.max_page - 1
        )

    @discord.ui.button(
        label="◀ Return",
        style=discord.ButtonStyle.blurple
    )
    async def return_btn(
        self,
        interaction,
        button
    ):

        if interaction.user.id != self.interaction.user.id:
            return

        self.page -= 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=await self.create_embed(),
            view=self
        )

    @discord.ui.button(
        label="Visit",
        style=discord.ButtonStyle.gray
    )
    async def visit_btn(
        self,
        interaction,
        button
    ):

        asset = self.assets[
            self.page
        ]

        await interaction.response.send_message(
            f"https://www.roblox.com/catalog/{asset['id']}",
            ephemeral=True
        )

    @discord.ui.button(
        label="Next ▶",
        style=discord.ButtonStyle.blurple
    )
    async def next_btn(
        self,
        interaction,
        button
    ):

        if interaction.user.id != self.interaction.user.id:
            return

        self.page += 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=await self.create_embed(),
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

            await self.interaction.edit_original_response(
                view=self
            )

        except:
            pass