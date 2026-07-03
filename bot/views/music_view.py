import discord
import yt_dlp
import json
import asyncio
import os

EMOJI_MUSIC = "<:spotify:1511354222560678068>"
EMOJI_PAGE = "<:emoji_14:1510943251232981093>"

EMOJI_OSS = "<a:oss:1510840776966279321>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X = "<a:X_:1510842480864661565>"

CACHE_FILE = "data/cache/music_cache.json"


def load_cache():

    if not os.path.exists(
        CACHE_FILE
    ):
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}


def save_cache(cache):

    os.makedirs(
        "data/cache",
        exist_ok=True
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=4
        )


async def search_music(query: str):

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "noplaylist": True
    }

    try:

        def load_search():

            with yt_dlp.YoutubeDL(
                ydl_opts
            ) as ydl:

                return ydl.extract_info(
                    f"ytsearch20:{query}",
                    download=False
                )

        data = await asyncio.to_thread(
            load_search
        )

        entries = data.get(
            "entries",
            []
        )

        results = []

        for item in entries:

            video_id = item.get(
                "id"
            )

            if not video_id:
                continue

            results.append(
                {
                    "id": video_id
                }
            )

        return results

    except:

        return []

async def get_video_info(
    video_id: str
):

    cache = load_cache()

    if video_id in cache:
        return cache[video_id]

    watch_url = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": True,
        "quiet": True
    }

    try:

        def load_info():

            with yt_dlp.YoutubeDL(
                ydl_opts
            ) as ydl:

                return ydl.extract_info(
                    watch_url,
                    download=False
                )

        info = await asyncio.to_thread(
            load_info
        )

        thumbnails = info.get(
            "thumbnails",
            []
        )

        banner = None

        if thumbnails:

            banner = thumbnails[-1].get(
                "url"
            )

        thumbnail = info.get(
            "thumbnail"
        )

        data = {
            "id": video_id,
            "title": info.get(
                "title",
                "Unknown"
            ),
            "view_count": info.get(
                "view_count",
                0
            ),
            "duration": info.get(
                "duration",
                0
            ),
            "thumbnail": thumbnail,
            "banner": banner,
            "upload_date": info.get(
                "upload_date",
                "Unknown"
            ),
            "webpage_url": info.get(
                "webpage_url",
                watch_url
            )
        }

        cache[video_id] = data

        save_cache(cache)

        return data

    except:

        return None


class PlayButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Play",
            style=discord.ButtonStyle.success
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if (
            member is None
            or member.voice is None
            or member.voice.channel is None
        ):

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_WARN} Warning\n\n"
                    f"You must join a voice channel first."
                ),
                color=0xFFA500
            )

            return await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        await interaction.response.defer()

        video_id = (
            view.results[
                view.page
            ]["id"]
        )

        info = await get_video_info(
            video_id
        )

        if not info:

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_WARN} Error\n\n"
                    f"Failed to load music information."
                ),
                color=0xFF0000
            )

            return await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        watch_url = (
            info["webpage_url"]
        )

        ydl_opts = {
            "format": "bestaudio",
            "noplaylist": True,
            "quiet": True
        }

        try:

            def load_stream():

                with yt_dlp.YoutubeDL(
                    ydl_opts
                ) as ydl:

                    return ydl.extract_info(
                        watch_url,
                        download=False
                    )

            full_info = await asyncio.to_thread(
                load_stream
            )

            stream_url = (
                full_info["url"]
            )

        except:

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_WARN} Error\n\n"
                    f"Unable to obtain audio stream."
                ),
                color=0xFF0000
            )

            return await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        voice_channel = (
            member.voice.channel
        )

        vc = interaction.guild.voice_client

        try:

            if vc is None:

                vc = await voice_channel.connect()

            elif vc.channel != voice_channel:

                await vc.move_to(
                    voice_channel
                )

            if vc.is_playing():

                vc.stop()

            source = discord.FFmpegOpusAudio(
                stream_url,
                before_options=(
                    "-reconnect 1 "
                    "-reconnect_streamed 1 "
                    "-reconnect_delay_max 5"
                )
            )

            def after_play(error):

                try:

                    asyncio.run_coroutine_threadsafe(
                        vc.disconnect(),
                        view.bot.loop
                    )

                except:
                    pass

            vc.play(
                source,
                after=after_play
            )

        except Exception as e:

            embed = discord.Embed(
                description=(
                    f"# {EMOJI_WARN} Error\n\n"
                    f"```{e}```"
                ),
                color=0xFF0000
            )

            return await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        embed = discord.Embed(
            description=(
                f"# {EMOJI_MUSIC} Music\n\n"
                f"{EMOJI_OSS} "
                f"**{info['title']}**"
            ),
            color=0x1DB954
        )

        if info.get(
            "thumbnail"
        ):

            embed.set_thumbnail(
                url=info["thumbnail"]
            )

        await interaction.followup.send(
            embed=embed
        )

class VisitButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Visit",
            style=discord.ButtonStyle.gray
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view

        video_id = view.results[
            view.page
        ]["id"]

        info = await get_video_info(
            video_id
        )

        if not info:

            return await interaction.response.send_message(
                "Video not found.",
                ephemeral=True
            )

        await interaction.response.send_message(
            info["webpage_url"],
            ephemeral=True
        )


class MusicView(
    discord.ui.View
):

    def __init__(
        self,
        interaction,
        results,
        search
    ):
        super().__init__(
            timeout=180
        )

        self.interaction = (
            interaction
        )

        self.bot = (
            interaction.client
        )

        self.results = results

        self.search = search

        self.page = 0

        self.max_page = len(
            results
        )

        self.selected_video = None

        self.add_item(
            PlayButton()
        )

        self.add_item(
            VisitButton()
        )

        self.update_buttons()

    async def create_embed(
        self
    ):

        video_id = self.results[
            self.page
        ]["id"]

        info = await get_video_info(
            video_id
        )

        if not info:

            return discord.Embed(
                description=(
                    f"{EMOJI_WARN} Failed to load video."
                ),
                color=0xFFAA00
            )

        title = info["title"]

        views = info[
            "view_count"
        ]

        duration = info[
            "duration"
        ]

        upload_date = info[
            "upload_date"
        ]

        thumbnail = info.get(
            "thumbnail"
        )

        banner = info.get(
            "banner"
        )

        mins = duration // 60
        secs = duration % 60

        duration_text = (
            f"{mins}:{secs:02d}"
        )

        desc = (
            f"# {EMOJI_MUSIC} Music\n\n"
            f"{EMOJI_PAGE} {self.page + 1}/{self.max_page}\n"
            f"{EMOJI_OSS} **{title}**\n"
            f"Views:\n"
            f"`{views:,}`\n"
            f"Duration:\n"
            f"`{duration_text}`\n"
            f"Upload Date:\n"
            f"`{upload_date}`"
        )

        embed = discord.Embed(
            description=desc,
            color=0x1DB954
        )

        if thumbnail:

            embed.set_thumbnail(
                url=thumbnail
            )

        if banner:

            embed.set_image(
                url=banner
            )

        embed.set_footer(
            text=(
                f"music | {self.search}"
            )
        )

        return embed

    def update_buttons(
        self
    ):

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

        await interaction.response.defer()

        await interaction.edit_original_response(
            embed=await self.create_embed(),
            view=self
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

        await interaction.response.defer()

        await interaction.edit_original_response(
            embed=await self.create_embed(),
            view=self
        )

    async def on_timeout(
        self
    ):

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