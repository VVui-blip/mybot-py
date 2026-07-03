import discord
import aiohttp

EMOJI_GITHUB = "<:github:1521924758176923708>"
EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"


async def fetch_github_user(username: str):

    url = f"https://api.github.com/users/{username}"

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as resp:

            if resp.status != 200:
                return None

            return await resp.json()


class GithubView(discord.ui.View):

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
                url=data["html_url"]
            )
        )

    def create_embed(self):

        username = self.data["login"]

        name = self.data.get(
            "name"
        ) or "Unknown"

        bio = self.data.get(
            "bio"
        ) or "No bio"

        company = self.data.get(
            "company"
        ) or "Unknown"

        location = self.data.get(
            "location"
        ) or "Unknown"

        repos = self.data.get(
            "public_repos",
            0
        )

        followers = self.data.get(
            "followers",
            0
        )

        following = self.data.get(
            "following",
            0
        )

        created = self.data.get(
            "created_at",
            "Unknown"
        )[:10]

        avatar = self.data.get(
            "avatar_url"
        )

        desc = (
            f"# {EMOJI_GITHUB} Github Profile\n\n"
            f"@{username} {EMOJI_OSS}\n"
            f"Name: **{name}**\n"
            f"Followers: **{followers:,}**\n"
            f"Following: **{following:,}**\n"
            f"Repos: **{repos:,}**\n"
            f"Company: **{company}**\n"
            f"Location: **{location}**\n"
            f"Created: **{created}**\n"
            f"```{bio[:500]}```"
        )

        embed = discord.Embed(
            description=desc,
            color=0x24292F
        )

        embed.set_thumbnail(
            url=avatar
        )

        embed.set_footer(
            text=f"github | @{username}"
        )

        return embed

    @discord.ui.button(
        label="Copy URL",
        style=discord.ButtonStyle.success
    )
    async def copy_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            self.data["html_url"],
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