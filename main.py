import discord
from discord import app_commands
import aiohttp
import time
import os

from bot.views.scriptblox_view import ScriptBloxPagination, EMOJI_SCR, EMOJI_LUA, EMOJI_X, EMOJI_OSS, EMOJI_WARN
from bot.views.roblox_user_view import RobloxUserView
from bot.views.help_view import HelpView
from bot.views.youtube_view import YouTubeVideoView, fetch_youtube_video
from bot.views.news_view import fetch_news, NewsPagination
from bot.views.github_view import fetch_github_user, GithubView
from bot.views.roblox_animation_view import search_animation, AnimationView
from bot.views.roblox_asset_view import search_assets, RobloxAssetView
from bot.views.discord_profile_view import fetch_discord_user, DiscordProfileView
from bot.views.minecraft_view import MinecraftView, fetch_minecraft_user
from bot.views.music_view import search_music, MusicView
from bot.views.credit_view import parse_credit_file, CreditView
from bot.views.url_shortener_view import shorten_url, URLShortenerView
from bot.ai_assistant import ask_ai

DIS = "<a:discord:1510907036404027412>"
CHAT = "<a:loading:1521599268098674839>"


class MyBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        


bot = MyBot()


async def safe_defer(interaction: discord.Interaction) -> bool:
    """Defer an interaction safely.

    Discord only gives 3 seconds to ACK an interaction. If the bot is
    delayed (slow network, the OS freezing the background process, etc.)
    defer() will raise NotFound. Wrap it to avoid a traceback and let the
    command know to stop early instead of calling followup on a dead
    interaction.
    """
    try:
        await interaction.response.defer()
        return True
    except discord.NotFound:
        cmd_name = interaction.command.name if interaction.command else "?"
        print(f"[WARN] Interaction hết hạn trước khi defer được (lệnh: {cmd_name}).")
        return False


@bot.event
async def on_ready():
    print(f"The bot operates under the name: {bot.user.name}")


@bot.tree.command(name="scriptblox", description="Search for script code on ScriptBlox")
@app_commands.describe(content="Keywords for script search")
async def scriptblox(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    api_url = f"https://scriptblox.com/api/script/search?q={content}&max=50"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    await interaction.followup.send(f"{EMOJI_WARN} Lỗi kết nối API.")
                    return

                payload = await response.json()
                result_data = payload.get("result", {})
                scripts = result_data.get("scripts", [])

                if not scripts:
                    err_desc = (
                        f"# {EMOJI_SCR} Scriptblox.com API\n"
                        f"{EMOJI_LUA} {content} = ????\n"
                        f"creation:\n"
                        f"```lua\nCannot be found | không thể tìm thấy\n```"
                    )
                    err_embed = discord.Embed(description=err_desc, color=0x71368A)
                    err_embed.set_footer(text=f"scriptblox | {content}")
                    await interaction.followup.send(embed=err_embed)
                    return

                pagination_view = ScriptBloxPagination(interaction, scripts, content)
                initial_embed = pagination_view.create_embed()
                await interaction.followup.send(embed=initial_embed, view=pagination_view)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        await interaction.followup.send(f"{EMOJI_X} Đã xảy ra lỗi trong quá trình xử lý lệnh.")


@bot.tree.command(name="robloxuser", description="Search Roblox User")
@app_commands.describe(content="Username hoặc UserID")
async def robloxuser(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    try:
        async with aiohttp.ClientSession() as session:
            if content.isdigit():
                user_id = int(content)
            else:
                payload = {"usernames": [content], "excludeBannedUsers": False}

                async with session.post(
                    "https://users.roblox.com/v1/usernames/users",
                    json=payload
                ) as r:
                    if r.status != 200:
                        return await interaction.followup.send(f"{EMOJI_X} Roblox API Error.")

                    data = await r.json()

                    if not data["data"]:
                        return await interaction.followup.send(f"{EMOJI_WARN} User not found.")

                    user_id = data["data"][0]["id"]

            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as r:
                if r.status != 200:
                    return await interaction.followup.send(f"{EMOJI_WARN} User not found.")

                user_info = await r.json()

            thumb_url = (
                "https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            )

            async with session.get(thumb_url) as r:
                thumb_json = await r.json()
                avatar_url = ""
                if thumb_json.get("data"):
                    avatar_url = thumb_json["data"][0].get("imageUrl", "")

            user_info["avatar"] = avatar_url

            view = RobloxUserView(user_info)
            embed = view.create_embed()
            await interaction.followup.send(embed=embed, view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="assistant", description="Chat with AI Assistant")
@app_commands.describe(prompt="Ask anything", image="Optional image to ask about")
async def assistant(interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
    if not await safe_defer(interaction):
        return

    try:
        image_url = None
        if image is not None:
            if not (image.content_type or "").startswith("image/"):
                await interaction.followup.send(f"{EMOJI_WARN} Attachments must be images.")
                return
            image_url = image.url

        answer = await ask_ai(interaction.user.id, prompt, image_url)

        embed = discord.Embed(
            title=f"{CHAT} Assistant",
            description=answer[:4000],
            color=0xFFA500
        )
        embed.set_footer(text=f"{interaction.user}")

        if image_url:
            embed.set_thumbnail(url=image_url)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")



@bot.tree.command(name="youtubevideo", description="Analyzing YouTube video")
@app_commands.describe(content="YouTube URL hoặc Video ID")
async def youtubevideo(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    try:
        result, error = await fetch_youtube_video(content)

        if error:
            return await interaction.followup.send(f"{EMOJI_WARN} {error}")

        data = result["data"]
        view = YouTubeVideoView(data, result["video_id"])

        await interaction.followup.send(embed=view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="news", description="Search Google News")
@app_commands.describe(content="News keyword")
async def news(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    try:
        results = await fetch_news(content)

        if not results:
            embed = discord.Embed(
                description=f"{EMOJI_WARN} No news found.",
                color=0xFFA500
            )
            return await interaction.followup.send(embed=embed)

        view = NewsPagination(interaction, results, content)
        await interaction.followup.send(embed=view.create_embed(), view=view)

    except Exception as e:
        print(e)
        embed = discord.Embed(description=f"{EMOJI_X} {e}", color=0xFF0000)
        await interaction.followup.send(embed=embed)


@bot.tree.command(name="githubaccount", description="Search Github Account")
@app_commands.describe(username="Github username")
async def githubaccount(interaction: discord.Interaction, username: str):
    if not await safe_defer(interaction):
        return

    try:
        data = await fetch_github_user(username)

        if not data:
            embed = discord.Embed(
                description=f"{EMOJI_X} Github account not found.",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=embed)

        view = GithubView(interaction, data)
        await interaction.followup.send(embed=view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="minecraftaccount", description="Search Minecraft Account")
@app_commands.describe(username="Minecraft username")
async def minecraftaccount(interaction: discord.Interaction, username: str):
    if not await safe_defer(interaction):
        return

    try:
        data = await fetch_minecraft_user(username)

        if not data:
            embed = discord.Embed(
                description=f"{EMOJI_X} Minecraft account not found.",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=embed)

        view = MinecraftView(interaction, data)
        await interaction.followup.send(embed=view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="robloxanimation", description="Search Roblox Animation")
@app_commands.describe(content="Animation Name, Package, Type or ID")
async def robloxanimation(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    try:
        animations = search_animation(content)

        if not animations:
            embed = discord.Embed(
                title="Animation Not Found",
                description=f"{EMOJI_X} No animation found for `{content}`.",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=embed)

        view = AnimationView(interaction, animations, content)
        await interaction.followup.send(embed=await view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="robloxassets", description="Search Roblox Asset")
@app_commands.describe(content="Asset Name")
async def robloxassets(interaction: discord.Interaction, content: str):
    if not await safe_defer(interaction):
        return

    try:
        assets = await search_assets(content)

        if not assets:
            embed = discord.Embed(
                title="Asset Not Found",
                description=f"{EMOJI_X} No asset found for `{content}`.",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=embed)

        view = RobloxAssetView(interaction, assets, content)
        await interaction.followup.send(embed=await view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="discordprofile", description="Discord User Profile")
@app_commands.describe(user_id="Discord User ID")
async def discordprofile(interaction: discord.Interaction, user_id: str):
    if not await safe_defer(interaction):
        return

    try:
        try:
            parsed_id = int(user_id)
        except ValueError:
            embed = discord.Embed(description=f"{EMOJI_X} Invalid User ID.", color=0xFF0000)
            return await interaction.followup.send(embed=embed)

        data = await fetch_discord_user(bot, parsed_id)

        if not data:
            embed = discord.Embed(description=f"{EMOJI_X} User not found.", color=0xFF0000)
            return await interaction.followup.send(embed=embed)

        view = DiscordProfileView(interaction, data)
        await interaction.followup.send(embed=await view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")


@bot.tree.command(name="music", description="Search Music")
@app_commands.describe(name="Music Name")
async def music(interaction: discord.Interaction, name: str):
    if not await safe_defer(interaction):
        return

    try:
        results = await search_music(name)

        if not results:
            embed = discord.Embed(
                description=f"{EMOJI_X} Music not found for `{name}`.",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=embed)

        view = MusicView(interaction, results, name)
        await interaction.followup.send(embed=await view.create_embed(), view=view)

    except Exception as e:
        print(e)
        await interaction.followup.send(f"{EMOJI_X} {e}")

@bot.tree.command(name="credits", description="View the credits and roles by tab")
async def credit(interaction: discord.Interaction):
    if not await safe_defer(interaction):
        # Defer failed (e.g. interaction already expired) — abort early.
        return

    tabs = parse_credit_file("config/credits.txt")
    if not tabs:
        embed = discord.Embed(
            description=f"{EMOJI_X} Không tìm thấy dữ liệu trong `config/credits.txt`.",
            color=0xFF0000
        )
        return await interaction.followup.send(embed=embed)

    view = CreditView(interaction, tabs, bot)
    await interaction.followup.send(embed=await view.create_embed(), view=view)

def _load_token() -> str | None:
    """Load the bot token.

    Priority:
      1. DISCORD_TOKEN environment variable (recommended for production/hosting).
      2. token.txt in the project root (convenient for local development).
    Both are excluded from version control via .gitignore.
    """
    env_token = os.environ.get("DISCORD_TOKEN")
    if env_token:
        return env_token.strip()

    if os.path.exists("token.txt"):
        with open("token.txt", "r", encoding="utf-8") as f:
            return f.read().strip()

    return None

@bot.tree.command(name="help", description="View the list of bot commands.")
async def help_command(interaction: discord.Interaction):

    commands_data = [
        (cmd.name, cmd.description or "No description")
        for cmd in bot.tree.get_commands()
    ]

    commands_data.sort(key=lambda c: c[0])

    view = HelpView(bot, commands_data, interaction.user.id)

    await interaction.response.send_message(
        embed=view.make_embed(),
        view=view
    )

@bot.tree.command(name="shorten", description="URL shortening")
@app_commands.describe(
    url="Đường dẫn cần rút gọn",
    alias="Custom shortened name (3-16 characters, optional)",
    password="Password to protect the link (optional)",
    max_clicks="Limit the number of clicks (optional)"
)
async def shorten_command(
    interaction: discord.Interaction,
    url: str,
    alias: str = None,
    password: str = None,
    max_clicks: int = None
):
    await interaction.response.defer()

    data, error = await shorten_url(url, alias, password, max_clicks)

    if error:
        embed = discord.Embed(
            description=f"{EMOJI_X} Notification: **{error}**",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)
        return

    view = URLShortenerView(data)

    await interaction.followup.send(
        embed=view.create_embed(),
        view=view
    )

if __name__ == "__main__":
    TOKEN = _load_token()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Thiếu token. Set biến môi trường DISCORD_TOKEN hoặc tạo file token.txt.")
