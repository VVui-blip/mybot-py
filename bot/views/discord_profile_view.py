import discord


EMOJI_DC = "<a:discord:1510907036404027412>"
EMOJI_OSS = "<a:oss:1510840776966279321>"


async def fetch_discord_user(
    bot,
    user_id: int
):

    try:

        user = await bot.fetch_user(
            user_id
        )

        return {
            "id": user.id,
            "username": user.name,
            "display_name": user.global_name,
            "avatar": (
                user.display_avatar.url
                if user.display_avatar
                else None
            ),
            "banner": (
                user.banner.url
                if user.banner
                else None
            ),
            "created_at": user.created_at,
            "bot": user.bot,
            "accent_color": (
                str(user.accent_color)
                if user.accent_color
                else "None"
            ),
            "flags": str(
                user.public_flags
            )
        }

    except:
        return None


class DiscordProfileView(
    discord.ui.View
):

    def __init__(
        self,
        interaction,
        data
    ):
        super().__init__(
            timeout=180
        )

        self.interaction = interaction
        self.data = data
        self.details = False

        self.add_item(
            discord.ui.Button(
                label="Visit",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/users/{data['id']}"
            )
        )

    async def create_embed(self):

        data = self.data

        if not self.details:

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_DC} Discord Profile\n\n"
                    f"Username:\n"
                    f"**{data['username']}** {EMOJI_OSS}\n"
                    f"Display Name:\n"
                    f"**{data['display_name'] or 'None'}**\n"
                    f"User ID:\n"
                    f"`{data['id']}`\n"
                    f"Created:\n"
                    f"<t:{int(data['created_at'].timestamp())}:F>"
                ),
                color=0x5865F2
            )

        else:

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_DC} Discord Details\n\n"
                    f"Username:\n"
                    f"`{data['username']}`\n"
                    f"Display Name:\n"
                    f"`{data['display_name'] or 'None'}`\n"
                    f"User ID:\n"
                    f"`{data['id']}`\n"
                    f"Bot:\n"
                    f"`{data['bot']}`\n"
                    f"Accent Color:\n"
                    f"`{data['accent_color']}`\n"
                    f"Public Flags:\n"
                    f"`{data['flags']}`\n"
                    f"Created:\n"
                    f"<t:{int(data['created_at'].timestamp())}:F>"
                ),
                color=0x5865F2
            )

        if data["avatar"]:

            embed.set_thumbnail(
                url=data["avatar"]
            )

        if data["banner"]:

            embed.set_image(
                url=data["banner"]
            )

        embed.set_footer(
            text=f"discord | {data['username']}"
        )

        return embed

    @discord.ui.button(
        label="Copy ID",
        style=discord.ButtonStyle.success
    )
    async def copy_btn(
        self,
        interaction,
        button
    ):

        if interaction.user.id != self.interaction.user.id:
            return

        await interaction.response.send_message(
            str(
                self.data["id"]
            ),
            ephemeral=True
        )

    @discord.ui.button(
        label="More",
        style=discord.ButtonStyle.blurple
    )
    async def more_btn(
        self,
        interaction,
        button
    ):

        if interaction.user.id != self.interaction.user.id:
            return

        self.details = not self.details

        button.label = (
            "Back"
            if self.details
            else "More"
        )

        await interaction.response.edit_message(
            embed=await self.create_embed(),
            view=self
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