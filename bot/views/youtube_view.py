import discord
import aiohttp
import re
import os

SERPAPI_KEY = os.environ.get("SERPAPI_API_KEY2")

EMOJI_YT = "<:Youtube:1510932567619141693>"
EMOJI_FILM = "<:world:1510934057696104538>"
EMOJI_VEF = "<a:vef:1510870340232806462>"
EMOJI_EYE = "<:views:1510931975358255244>"
EMOJI_LIKE = "<a:like:1510931913236287671>"
EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"


def extract_video_id(content: str):
    content = content.strip()

    if re.fullmatch(r"[\w-]{11}", content):
        return content

    patterns = [
        r"v=([\w-]{11})",
        r"youtu\.be/([\w-]{11})",
        r"shorts/([\w-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)

    return None


class CopyVideoIDButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Copy ID",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        await interaction.response.send_message(
            view.video_id,
            ephemeral=True
        )


class YouTubeVideoView(discord.ui.View):
    def __init__(self, data: dict, video_id: str):
        super().__init__(timeout=180)

        self.data = data
        self.video_id = video_id

        channel = data.get("channel", {})

        self.add_item(
            discord.ui.Button(
                label="Visit",
                style=discord.ButtonStyle.link,
                url=f"https://www.youtube.com/watch?v={video_id}"
            )
        )

        if channel.get("link"):
            self.add_item(
                discord.ui.Button(
                    label="Channel",
                    style=discord.ButtonStyle.link,
                    url=channel["link"]
                )
            )

        self.add_item(
            CopyVideoIDButton()
        )

    def create_embed(self):

        title = self.data.get(
            "title",
            "Unknown Video"
        )

        thumbnail = self.data.get(
            "thumbnail",
            ""
        )

        channel = self.data.get(
            "channel",
            {}
        )

        channel_name = channel.get(
            "name",
            "Unknown"
        )

        verified = channel.get(
            "verified",
            False
        )

        views = self.data.get(
            "extracted_views",
            0
        )

        likes = self.data.get(
            "extracted_likes",
            0
        )

        published = self.data.get(
            "published_date",
            "Unknown"
        )

        verify_text = (
            f" {EMOJI_VEF}"
            if verified
            else ""
        )

        desc = (
            f"# {EMOJI_YT} YouTube\n\n"
            f" **{EMOJI_FILM} {title}**\n\n"
            f"channel: {channel_name}{verify_text}\n"
            f"views: {views:,} {EMOJI_EYE}\n"
            f"likes: {likes:,} {EMOJI_LIKE}\n"
            f"[{title}](https://www.youtube.com/watch?v={self.video_id})\n\n"
            f"published: {published}"
        )

        embed = discord.Embed(
            description=desc,
            color=0xFF0000
        )

        if thumbnail:
            embed.set_image(
                url=thumbnail
            )

        embed.set_footer(
            text=f"youtube video | {self.video_id}"
        )

        return embed


async def fetch_youtube_video(content: str):

    video_id = extract_video_id(content)

    if not video_id:
        return None, "Invalid YouTube URL or Video ID."

    url = (
        "https://serpapi.com/search.json"
        f"?engine=youtube_video"
        f"&v={video_id}"
        f"&api_key={SERPAPI_KEY}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as r:

            if r.status != 200:
                return None, "SerpApi Error."

            data = await r.json()

    return {
        "video_id": video_id,
        "data": data
    }, None