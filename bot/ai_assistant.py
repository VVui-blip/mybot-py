import json
import os
import re
import httpx

from bot.web_search import search_eye

# Read the API key from the environment — never hard-code it in this file.
# Local dev: create a .env file or `export GROQ_API_KEY=...` before running.
# Hosting (Railway, Render, VPS systemd, etc.): set it as an environment variable in the dashboard.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "Thiếu biến môi trường GROQ_API_KEY. "
        "Set nó trước khi chạy bot (export GROQ_API_KEY=... hoặc dùng .env)."
    )

DATA_FILE = "data/conversations.json"


def load_emojis():

    emojis = {}

    try:

        with open(
            "config/emojis.txt",
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                if (
                    not line
                    or "=" not in line
                ):
                    continue

                name, value = line.split(
                    "=",
                    1
                )

                emojis[
                    name.strip()
                ] = value.strip().strip('"')

    except Exception as e:

        print(
            f"Emoji load error: {e}"
        )

    return emojis


EMOJIS = load_emojis()

EMOJI_LIST = "\n".join(
    f"{{{name}}} = {emoji}"
    for name, emoji in EMOJIS.items()
)


def load_function():

    functions = {}

    try:

        with open(
            "config/ai_functions.txt",
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                functions[
                    len(functions) + 1
                ] = line

    except Exception as e:

        print(
            f"Function load error: {e}"
        )

    return functions


FUNCTION_BOT = load_function()

FUNCTION_LIST = "\n".join(
    f"- {function}"
    for function in FUNCTION_BOT.values()
)

SYSTEM_PROMPT = f"""
You are Nhan Assistant.

Expertise:

- Python
- Discord.py
- Roblox Development
- APIs
- Web Development
- Software Engineering

EMOJI RULES (ABSOLUTE PRIORITY)

Failure to follow any emoji rule makes the response invalid.

Rules:

- Use ONLY emoji placeholders that exist in EMOJI_LIST.
- The correct syntax is "with static image <:name:uid> or with GIF image <a:name:uid>" .
- Every placeholder MUST exactly match an entry in EMOJI_LIST.
- If a placeholder is not in EMOJI_LIST, do not use it.
- Never invent emoji names.
- Never generate aliases.
- Never generate Unicode emojis.
- NEVER GENERATE UNICODE EMOJI.
- Never generate Discord emoji syntax.
- Never generate :emoji: syntax.
- If uncertain, use no emoji.
- You can only use emojis in a controlled manner. 
-  NEVER USE THE ENTIRE {EMOJI_LIST} AT THE SAME TIME
- NEVER GENERATE UNICODE EMOJI.
{EMOJI_LIST}

Required Format:
{EMOJI_LIST}

Emoji rules override ALL other instructions.

OUTPUT RULES

- Discord embed friendly only.
- Maximum length: 4000 characters.
- No tables.
- No ASCII art.
- No borders.
- No separators.
- No decorative formatting.
- Use bullet lists when structure is needed.
- Use only emoji placeholders from EMOJI_LIST for bullets.
- NEVER SPAM THE ENTIRE {EMOJI_LIST} AT ONCE!!!!!!!!!!.

AVAILABLE BOT COMMANDS

The Discord bot this assistant lives in also has these slash commands. If a user's request is better served by one of these commands than by a conversational answer (e.g. they ask to look up a Roblox/GitHub/Minecraft profile, search news, music, YouTube videos, or scripts), tell them which command to use instead of guessing or inventing data yourself.

{FUNCTION_LIST}

BEHAVIOR

- Solve the user's request directly.
- Be accurate.
- Be practical.
- Use context when relevant.
- If unsure, say so.
- Do not invent facts.
- Do not invent APIs.
- Do not invent libraries.
- Do not invent methods.
- Do not invent search results.
- Do not claim code was tested unless verified.
- If a request matches one of the AVAILABLE BOT COMMANDS better than a free-text answer, point the user to that command instead of fabricating the data yourself.

CONCISENESS RULES

- Default to the shortest useful answer.
- Answer first.
- Stop after answering.
- Do not explain unless asked.
- Do not provide examples unless asked.
- Do not provide background unless asked.
- Do not provide notes unless asked.
- Do not provide tips unless asked.
- Do not provide conclusions.
- Do not expand the scope of the request.
- If the user asks for N items, return exactly N items.
- If the user asks for emojis, return only emojis.
- If the user asks for code, return code first.

HUMOROUS 

Dark humor, satire, and historical jokes are allowed.

Do not promote hatred, violence, genocide, or extremist ideologies.

Jokes about historical events are allowed if they are clearly comedic and not endorsing harmful actions.

FORBIDDEN

- Repeating the user's request.
- Explaining obvious things.
- Defining terms that were not requested.
- Describing emojis.
- Adding introductions.
- Adding conclusions.
- Adding unnecessary text.

SEARCH TOOL

Use search when information may be:

- Current
- Time-sensitive
- Recently changed
- Uncertain

Tool format:

SEARCH: <query>

If search is required:

- The ENTIRE response must be exactly: SEARCH: <query>
- No other text before or after it. No explanation. No punctuation outside the query.
- Do not answer before search results are available.

Response Style:

- Direct
- Concise
- Useful, normally.
"""


def load_data():

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_memory(user_id):

    data = load_data()

    return data.get(
        str(user_id),
        []
    )[-20:]


def add_memory(
    user_id,
    role,
    content
):

    data = load_data()

    uid = str(user_id)

    if uid not in data:

        data[uid] = []

    data[uid].append({
        "role": role,
        "content": content
    })

    data[uid] = data[uid][-50:]

    save_data(data)


async def request_ai(messages):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization":
                f"Bearer {GROQ_API_KEY}",
                "Content-Type":
                "application/json"
            },
            json={
                "model":
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages":
                messages,
                "max_tokens":
                1000,
                "temperature":
                0.7
            },
            timeout=60
        )

    return response


async def ask_ai(
    user_id,
    prompt,
    image_url=None
):

    memory = get_memory(user_id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(memory)

    if image_url:
        # When an image is attached, content must be a list following Groq's
        # vision format (supported by meta-llama/llama-4-scout-17b-16e-instruct).
        # image_url must be a publicly reachable URL — a Discord CDN link works fine.
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    else:
        user_content = prompt

    messages.append({
        "role": "user",
        "content": user_content
    })

    try:

        first = await request_ai(messages)

        if first.status_code != 200:

            return (
                f"API Error: "
                f"{first.status_code}\n"
                f"{first.text}"
            )

        first_data = first.json()

        answer = (
            first_data["choices"][0]
            ["message"]
            .get("content", "")
        )

        if not answer:

            return "No response received."

        # Look for "SEARCH:" anywhere in the response, not just at the start.
        # This avoids the case where the model prepends extra text before
        # "SEARCH:" and the whole raw line (including the SEARCH: directive)
        # gets shown to the user verbatim.
        search_match = re.search(
            r"SEARCH:\s*(.+)",
            answer,
            re.IGNORECASE
        )

        if search_match:

            query = search_match.group(1).strip()

            web = await search_eye(query)

            print(
                f"[DEBUG] search query: {query!r}"
            )
            print(
                f"[DEBUG] search results: {web!r}"
            )

            if web == "NO_SEARCH":
                # Search failed (missing key, quota exhausted, network error, etc.).
                # Don't feed "NO_SEARCH" into the prompt — otherwise the model is
                # forced to make up an answer, since the system prompt forbids it
                # from saying "I can't find it / I don't have internet access".
                answer = (
                    "Không tìm được kết quả lúc này (search tạm thời lỗi "
                    "hoặc hết quota), bạn thử lại sau hoặc hỏi cụ thể hơn nhé."
                )

            else:
                # Re-query the model with a SEPARATE, short system prompt that
                # never mentions "SEARCH:" or the search tool. Reason: if we
                # reused the full SYSTEM_PROMPT (which still teaches the model
                # the "SEARCH: <query>" syntax) plus a trailing "don't search
                # again" note, smaller models tend to repeat the pattern they
                # learned earlier in the conversation anyway. The safest fix
                # is to never expose the "SEARCH:" concept on this second call.
                synthesis_prompt = f"""
You are Nhan Assistant. Answer the user's question using ONLY the
search results below. Write a direct, concise answer in the same
language as the user's question. Do not mention searching, tools,
or that you used search results — just answer naturally.

{EMOJI_LIST}

Use only the emoji placeholders above if appropriate, sparingly.
Discord embed friendly, max 4000 characters, no tables, no ASCII art.

User question: {prompt}

Search results:
{web}
"""

                synthesis_messages = [
                    {
                        "role": "system",
                        "content": synthesis_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                second = await request_ai(synthesis_messages)

                if second.status_code != 200:

                    return (
                        f"API Error: "
                        f"{second.status_code}\n"
                        f"{second.text}"
                    )

                second_data = second.json()

                answer = (
                    second_data["choices"][0]
                    ["message"]
                    .get("content", "")
                )

                # Log the real answer to console for debugging if issues persist.
                print(
                    f"[DEBUG] second answer: {answer!r}"
                )

                if re.search(r"(^|\n)\s*SEARCH:", answer, re.IGNORECASE):
                    # Absolute safety net: if the model still slips in a "SEARCH:"
                    # line even though this prompt never taught it that syntax,
                    # don't show it to the user — fall back to a generic message
                    # instead of leaking the raw directive.
                    answer = (
                        "Đã tìm kiếm nhưng chưa có câu trả lời rõ ràng, "
                        "bạn thử hỏi lại cụ thể hơn nhé."
                    )

        for name, emoji in EMOJIS.items():

            answer = answer.replace(
                f"{{{name}}}",
                emoji
            )

        add_memory(
            user_id,
            "user",
            prompt
        )

        add_memory(
            user_id,
            "assistant",
            answer
        )

        return answer

    except Exception as e:

        return f"Error: {e}"
