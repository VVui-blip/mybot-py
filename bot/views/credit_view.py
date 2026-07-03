import discord
import re
import math

EMOJI_TAB  = "<:bloxtrap:1520694122065952940>"
EMOJI_WARN = "<a:warn:1510842393329533049>"
EMOJI_X    = "<a:X_:1510842480864661565>"
EMOJI_CREW = "<:folder:1519960042416111708>"
EMOJI_DOT  = "·"

# Role -> emoji mapping (custom emojis provided by the server admins).
ROLE_EMOJI: dict[str, str] = {
    "owner":       "<:crownownerpng:1520692512266915910>",
    "founder":     "<:crownownerpng:1520692512266915910>",
    "admin":       "<:settingmanagementpng:1520692510505308261>",
    "manager":     "<:settingmanagementpng:1520692510505308261>",
    "partner":     "<:badgepartnerpng:1520692506340360243>",
    "developer":   "<:icondeveloperpng:1520692514133114920>",
    "dev":         "<:icondeveloperpng:1520692514133114920>",
    "moderator":   "<:toolsfixpng:1520692508643033210>",
    "mod":         "<:toolsfixpng:1520692508643033210>",
    "supporter":   "<:toolsfixpng:1520692508643033210>",
}


def get_role_emoji(role: str | None) -> str:
    """Return the emoji for a role string, falling back to EMOJI_CREW."""
    if not role:
        return EMOJI_CREW
    lower = role.lower()
    for key, emoji in ROLE_EMOJI.items():
        if key in lower:
            return emoji
    return EMOJI_CREW


PER_PAGE = 5

TAB_LINE_RE   = re.compile(r"^#\s*(.+)$")
ENTRY_LINE_RE = re.compile(r"^-\s*(.+)$")
UID_RE        = re.compile(r"\d{15,20}")
ROLE_RE       = re.compile(r"\[([^\]]+)\]")
NO_TAG_RE     = re.compile(r"#\s*no[_\s]?tag", re.IGNORECASE)


def parse_credit_file(path: str):
    """
    Parse credit.txt into a dict:
    {
        "Tab Name": [
            {"uid": 123456789012345678, "role": "Owner" or None, "no_tag": False},
            ...
        ],
        ...
    }
    Tab order is preserved.
    """
    tabs: dict[str, list] = {}
    current_tab: str | None = None

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {}

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("-"):

            entry_match = ENTRY_LINE_RE.match(line)

            if not entry_match or current_tab is None:
                continue

            content = entry_match.group(1)
            uid_match = UID_RE.search(content)

            if not uid_match:
                continue

            uid       = int(uid_match.group(0))
            role_m    = ROLE_RE.search(content)
            role      = role_m.group(1).strip() if role_m else None
            no_tag    = bool(NO_TAG_RE.search(content))

            tabs[current_tab].append({
                "uid":    uid,
                "role":   role,
                "no_tag": no_tag,
            })

        elif line.startswith("#"):

            tab_match = TAB_LINE_RE.match(line)

            if not tab_match:
                continue

            raw_name = tab_match.group(1).strip()

            if "=" in raw_name:
                # Support "Label = Tab Name" syntax — use only the part after "=".
                raw_name = raw_name.split("=", 1)[1].strip()

            if not raw_name:
                continue

            current_tab = raw_name

            if current_tab not in tabs:
                tabs[current_tab] = []

    return tabs


class CreditView(discord.ui.View):

    def __init__(
        self,
        interaction: discord.Interaction,
        tabs: dict,
        bot: discord.Client,
    ):
        super().__init__(timeout=180)

        self.interaction = interaction
        self.bot = bot

        self.tab_names = list(tabs.keys())
        self.tabs = tabs

        self.current_tab_index = 0 if self.tab_names else -1
        self.current_page = 0

        # Cache display names for UIDs with no_tag=True to avoid repeated fetches.
        self._name_cache: dict[int, str] = {}

        self.build_components()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def current_tab_name(self) -> str | None:
        if self.current_tab_index == -1:
            return None
        return self.tab_names[self.current_tab_index]

    @property
    def current_entries(self) -> list:
        if self.current_tab_index == -1:
            return []
        return self.tabs[self.current_tab_name]

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.current_entries) / PER_PAGE))

    # ── UI building ───────────────────────────────────────────────────────────

    def build_components(self):
        """Rebuild all buttons: one per tab (max 20, 5 per row, 4 rows for tabs)
        plus a final row for Prev / Next navigation."""

        self.clear_items()

        max_tabs = 20

        for index, name in enumerate(self.tab_names[:max_tabs]):

            row = index // 5

            button = discord.ui.Button(
                label=name[:80],
                style=(
                    discord.ButtonStyle.success
                    if index == self.current_tab_index
                    else discord.ButtonStyle.secondary
                ),
                row=row,
                custom_id=f"credit_tab_{index}",
            )
            button.callback = self.make_tab_callback(index)
            self.add_item(button)

        nav_row = (
            min(4, ((len(self.tab_names[:max_tabs]) - 1) // 5) + 1)
            if self.tab_names else 0
        )

        self.prev_btn = discord.ui.Button(
            label="◀ Prev",
            style=discord.ButtonStyle.blurple,
            row=nav_row,
            disabled=self.current_page <= 0,
        )
        self.prev_btn.callback = self.on_prev

        self.next_btn = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.blurple,
            row=nav_row,
            disabled=self.current_page >= self.total_pages - 1,
        )
        self.next_btn.callback = self.on_next

        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)

    def make_tab_callback(self, index: int):

        async def callback(interaction: discord.Interaction):
            try:
                if interaction.user.id != self.interaction.user.id:
                    return await interaction.response.send_message(
                        f"{EMOJI_X} This menu is not yours.", ephemeral=True
                    )
                self.current_tab_index = index
                self.current_page = 0
                self.build_components()
                await interaction.response.edit_message(
                    embed=await self.create_embed(), view=self
                )
            except discord.NotFound:
                pass

        return callback

    async def on_prev(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.interaction.user.id:
                return await interaction.response.send_message(
                    f"{EMOJI_X} This menu is not yours.", ephemeral=True
                )
            self.current_page -= 1
            self.build_components()
            await interaction.response.edit_message(
                embed=await self.create_embed(), view=self
            )
        except discord.NotFound:
            pass

    async def on_next(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.interaction.user.id:
                return await interaction.response.send_message(
                    f"{EMOJI_X} This menu is not yours.", ephemeral=True
                )
            self.current_page += 1
            self.build_components()
            await interaction.response.edit_message(
                embed=await self.create_embed(), view=self
            )
        except discord.NotFound:
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def resolve_display_name(self, uid: int) -> str:

        if uid in self._name_cache:
            return self._name_cache[uid]

        name = f"`{uid}`"

        try:
            member = None
            if self.interaction.guild:
                member = self.interaction.guild.get_member(uid)

            if member:
                name = member.display_name
            else:
                user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                name = user.name

        except (discord.NotFound, discord.HTTPException):
            pass

        self._name_cache[uid] = name
        return name

    # ── Embed ─────────────────────────────────────────────────────────────────

    async def create_embed(self) -> discord.Embed:

        if not self.tab_names:
            return discord.Embed(
                description=f"{EMOJI_WARN} `credit.txt` has no data.",
                color=0xFF0000,
            )

        start        = self.current_page * PER_PAGE
        page_entries = self.current_entries[start : start + PER_PAGE]

        lines: list[str] = []

        for entry in page_entries:

            if entry["no_tag"]:
                name_part = await self.resolve_display_name(entry["uid"])
            else:
                name_part = f"<@{entry['uid']}>"

            role = entry["role"]
            icon = get_role_emoji(role)

            if role:
                lines.append(f"{icon} {name_part} {EMOJI_DOT} {role}")
            else:
                lines.append(f"{icon} {name_part}")

        if not lines:
            lines.append(f"{EMOJI_WARN} This tab has no members yet.")

        total       = len(self.current_entries)
        member_label = "member" if total == 1 else "members"

        header = (
            f"## {EMOJI_TAB}  {self.current_tab_name}\n"
            f"-# {total} {member_label} {EMOJI_DOT} page {self.current_page + 1}/{self.total_pages}\n"
            f"\u200b\n"
        )

        embed = discord.Embed(
            description=header + "\n".join(lines),
            color=0x5865F2,
        )

        embed.set_footer(
            text=(
                f"credits  {EMOJI_DOT}  {self.current_tab_name}"
                f"  {EMOJI_DOT}  {self.current_page + 1}/{self.total_pages}"
            )
        )

        return embed

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except Exception:
            pass
