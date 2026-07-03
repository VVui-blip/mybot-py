import discord

EMOJI_RBX = "<:Roblox:1510869824174034944>"
EMOJI_VEF = "<a:vef:1510870340232806462>"
EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"

class CopyUsernameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Copy",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        await interaction.response.send_message(
            f"@{view.user_data['name']}",
            ephemeral=True
        )


class RobloxUserView(discord.ui.View):
    def __init__(self, user_data: dict):
        super().__init__(timeout=180)

        self.user_data = user_data

        self.add_item(
            discord.ui.Button(
                label="Visit",
                style=discord.ButtonStyle.link,
                url=f"https://www.roblox.com/users/{user_data['id']}/profile"
            )
        )

        self.add_item(
            CopyUsernameButton()
        )

    def create_embed(self):
        username = self.user_data.get("name", "Unknown")
        display_name = self.user_data.get("displayName", "Unknown")
        user_id = self.user_data.get("id", 0)

        VERIFIED_USERS = {
            4848962740,
            4456392082
        }

        created = self.user_data.get("created", "")
        created = created[:10] if created else "Unknown"

        avatar_url = self.user_data.get("avatar", "")

        verified = (
            self.user_data.get("hasVerifiedBadge", False)
            or user_id in VERIFIED_USERS
        )

        verify_text = (
            f" {EMOJI_VEF}"
            if verified
            else ""
        )

        embed = discord.Embed(
            description=(
                f"# {EMOJI_RBX} Roblox\n\n"
                f"{EMOJI_OSS} @{username}\n"
                f"Userid: **{user_id}**\n"
                f"Display Name: **{display_name}**{verify_text}\n"
                f"Created: **{created}**"
            ),
            color=0x3498DB
        )

        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(
            text=f"roblox user | @{username}"
        )

        return embed

    async def on_timeout(self):
        for item in self.children:
            if (
                isinstance(item, discord.ui.Button)
                and item.style != discord.ButtonStyle.link
            ):
                item.disabled = True