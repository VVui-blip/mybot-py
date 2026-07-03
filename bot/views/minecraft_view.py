import discord
import aiohttp
import io

EMOJI_MC = "<:MC:1511021425832759448>"
EMOJI_JAVA = "<:java:1511026484847050922>"
EMOJI_BEDROCK = "<:bedrock:1511026376482885652>"

EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"


async def fetch_minecraft_user(username: str):

    async with aiohttp.ClientSession() as session:

        # Java edition lookup
        try:

            async with session.get(
                f"https://playerdb.co/api/player/minecraft/{username}"
            ) as r:

                if r.status == 200:

                    data = await r.json()

                    player = (
                        data.get("data", {})
                        .get("player")
                    )

                    if player:

                        return {
                            "username": player.get(
                                "username",
                                username
                            ),
                            "uuid": player.get(
                                "id",
                                "Unknown"
                            ),
                            "created": "Unknown",
                            "type": "Java"
                        }

        except:
            pass

        # Bedrock / Xbox lookup
        try:

            async with session.get(
                f"https://playerdb.co/api/player/xbox/{username}"
            ) as r:

                if r.status == 200:

                    data = await r.json()

                    player = (
                        data.get("data", {})
                        .get("player")
                    )

                    if player:

                        return {
                            "username": player.get(
                                "username",
                                username
                            ),
                            "uuid": player.get(
                                "id",
                                "Unknown"
                            ),
                            "created": "Unknown",
                            "type": "Bedrock"
                        }

        except:
            pass

    return None


class MinecraftView(discord.ui.View):

    def __init__(
        self,
        interaction: discord.Interaction,
        data: dict
    ):
        super().__init__(timeout=180)

        self.interaction = interaction
        self.data = data

        self.add_item(
            discord.ui.Button(
                label="Visit",
                style=discord.ButtonStyle.link,
                url=f"https://namemc.com/profile/{data['username']}"
            )
        )

    def create_embed(self):

        username = self.data["username"]

        uuid = self.data["uuid"]

        created = str(
            self.data["created"]
        )[:10]

        account_type = self.data.get(
            "type",
            "Unknown"
        )

        type_emoji = (
            EMOJI_JAVA
            if account_type.lower() == "java"
            else EMOJI_BEDROCK
        )

        avatar = (
            f"https://mc-heads.net/avatar/"
            f"{username}/512"
        )

        body = (
            f"https://mc-heads.net/body/"
            f"{username}/512"
        )

        desc = (
            f"# {EMOJI_MC} Minecraft Profile\n\n"
            f"Username: **{username}** {EMOJI_OSS}\n"
            f"Type: {type_emoji} **{account_type}**\n\n"
            f"UUID:\n"
            f"`{uuid}`\n\n"
            f"Creation:\n"
            f"`{created}`"
        )

        embed = discord.Embed(
            description=desc,
            color=0x55AA55
        )

        embed.set_thumbnail(
            url=avatar
        )

        embed.set_image(
            url=body
        )

        embed.set_footer(
            text=f"minecraft | {username}"
        )

        return embed

    @discord.ui.button(
        label="Install",
        style=discord.ButtonStyle.success
    )
    async def install_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        username = self.data["username"]

        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"https://mc-heads.net/skin/{username}"
            ) as r:

                skin = await r.read()

        file = discord.File(
            io.BytesIO(skin),
            filename=f"{username}_skin.png"
        )

        await interaction.response.send_message(
            file=file,
            ephemeral=True
        )

    @discord.ui.button(
        label="Copy UUID",
        style=discord.ButtonStyle.blurple
    )
    async def copy_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            self.data["uuid"],
            ephemeral=True
        )

    async def on_timeout(self):

        for child in self.children:

            if (
                isinstance(
                    child,
                    discord.ui.Button
                )
                and child.style
                != discord.ButtonStyle.link
            ):
                child.disabled = True

        try:

            await self.interaction.edit_original_response(
                view=self
            )

        except:
            pass