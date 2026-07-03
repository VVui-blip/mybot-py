import discord
import aiohttp
import os

# Never hard-code API keys in source. Set SERPAPI_KEY as an environment
# variable (locally via .env, or in your host's dashboard for production).
SERPAPI_KEY = os.environ.get("SERPAPI_API_KEY1")

EMOJI_NEWS = "<:news:1510959604727808030>"
EMOJI_PAGE = "<:blue:1510959687342886982>"

EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"


async def fetch_news(query: str):

    url = (
        "https://serpapi.com/search.json"
        f"?engine=google_news"
        f"&q={query}"
        f"&api_key={SERPAPI_KEY}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as r:

            if r.status != 200:
                return None

            data = await r.json()

    return data.get("news_results", [])


class CopyURLButton(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Copy URL",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):

        view = self.view

        item = view.news[view.current_page]

        await interaction.response.send_message(
            item.get("link", "No URL"),
            ephemeral=True
        )


class NewsPagination(discord.ui.View):

    def __init__(
        self,
        interaction: discord.Interaction,
        news: list,
        search_content: str
    ):

        super().__init__(timeout=180)

        self.interaction = interaction
        self.news = news
        self.search_content = search_content

        self.current_page = 0
        self.total_pages = len(news)

        self.add_item(CopyURLButton())

        self.update_buttons()

    def create_embed(self):

        item = self.news[self.current_page]

        title = item.get(
            "title",
            "Unknown"
        )

        url = item.get(
            "link",
            ""
        )

        thumbnail = item.get(
            "thumbnail",
            ""
        )

        published = item.get(
            "date",
            "Unknown"
        )

        summary = (
            item.get("snippet")
            or item.get("description")
            or item.get("title")
            or "No description available."
        )

        if len(summary) > 500:
            summary = summary[:500] + "..."

        desc = (
            f"# {EMOJI_NEWS} News\n\n"
            f"{EMOJI_PAGE} {self.current_page + 1}/{self.total_pages}\n"
            f"**{title}**\n"
            f"```{summary}```\n"
            f"published: {published}\n"
            f"[read the whole thing]({url})"
        )

        embed = discord.Embed(
            description=desc,
            color=0x4285F4
        )

        if thumbnail:
            embed.set_image(
                url=thumbnail
            )

        embed.set_footer(
            text=f"news | {self.search_content}"
        )

        return embed

    def update_buttons(self):

        self.return_btn.disabled = (
            self.current_page == 0
        )

        self.next_btn.disabled = (
            self.current_page >= self.total_pages - 1
        )

    @discord.ui.button(
        label="◀ Return",
        style=discord.ButtonStyle.blurple
    )
    async def return_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.interaction.user.id:

            return await interaction.response.send_message(
                "Not your menu.",
                ephemeral=True
            )

        self.current_page -= 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    @discord.ui.button(
        label="Visit",
        style=discord.ButtonStyle.gray
    )
    async def visit_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        item = self.news[self.current_page]

        await interaction.response.send_message(
            item.get("link"),
            ephemeral=True
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

        if interaction.user.id != self.interaction.user.id:

            return await interaction.response.send_message(
                "Not your menu.",
                ephemeral=True
            )

        self.current_page += 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
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