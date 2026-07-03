import discord
import json
import aiohttp

EMOJI_RBX = "<:roblox:1510869824174034944>"
EMOJI_PAGE = "<:emoji_14:1510943251232981093>"

with open(
    "data/animations.json",
    "r",
    encoding="utf-8"
) as f:

    ANIMATIONS = json.load(f)


def search_animation(content: str):

    content = content.lower().strip()

    results = []

    for anim in ANIMATIONS:

        if (
            content in anim["name"].lower()
            or content in anim["type"].lower()
            or content in anim["package"].lower()
            or content == str(anim["id"])
        ):
            results.append(anim)

    return results


class CopyAnimationID(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Copy ID",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction):

        anim = self.view.animations[
            self.view.page
        ]

        await interaction.response.send_message(
            str(anim["id"]),
            ephemeral=True
        )


class AnimationView(discord.ui.View):

    def __init__(
        self,
        interaction,
        animations,
        search
    ):
        super().__init__(timeout=180)

        self.interaction = interaction
        self.animations = animations
        self.search = search

        self.page = 0
        self.max_page = len(animations)

        self.add_item(
            CopyAnimationID()
        )

        self.update_buttons()

    async def get_animation_thumbnail(
        self,
        asset_id: int
    ):

        url = (
            "https://thumbnails.roblox.com/v1/assets"
            f"?assetIds={asset_id}"
            "&size=420x420"
            "&format=Png"
            "&isCircular=false"
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

    async def create_embed(self):

        anim = self.animations[
            self.page
        ]

        name = anim["name"]
        asset_id = anim["id"]
        anim_type = anim["type"]
        package = anim["package"]

        thumbnail = await self.get_animation_thumbnail(
            asset_id
        )

        desc = (
            f"# {EMOJI_RBX} Roblox Animation\n\n"
            f"{EMOJI_PAGE} {self.page+1}/{self.max_page}\n"
            f"Name:\n"
            f"**{name}**\n"
            f"Type:\n"
            f"`{anim_type}`\n"
            f"Package:\n"
            f"`{package}`\n"
            f"Animation ID:\n"
            f"`{asset_id}`"
        )

        embed = discord.Embed(
            description=desc,
            color=0xE2231A
        )

        if thumbnail:
            embed.set_thumbnail(
                url=thumbnail
            )

        embed.set_footer(
            text=f"roblox animation | {self.search}"
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

        if (
            interaction.user.id
            != self.interaction.user.id
        ):
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

        anim = self.animations[
            self.page
        ]

        await interaction.response.send_message(
            f"https://www.roblox.com/library/{anim['id']}",
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

        if (
            interaction.user.id
            != self.interaction.user.id
        ):
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