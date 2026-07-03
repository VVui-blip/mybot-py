import os
import httpx

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


async def search_eye(query: str) -> str:

    if not SERPER_API_KEY:
        return "NO_SEARCH"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query,
                    "num": 3
                },
                timeout=15
            )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "organic",
            []
        )

        if not results:
            return "NO_SEARCH"

        output = []

        for item in results[:3]:

            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")

            output.append(
                f"{title}\n{snippet}\nSource: {url}"
            )

        return "\n\n".join(output)

    except httpx.HTTPStatusError as e:
        # Log status code + body so failures (quota exhausted, bad key, etc.)
        # are traceable instead of a generic "NO_SEARCH".
        print(
            f"Serper HTTP Error: {e.response.status_code} - {e.response.text}"
        )

        return "NO_SEARCH"

    except Exception as e:

        print(
            f"Serper Error: {e}"
        )

        return "NO_SEARCH"
