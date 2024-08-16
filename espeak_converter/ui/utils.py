import asyncio


async def ainput(prompt=""):
    return await asyncio.to_thread(input, prompt)


async def choice(title, choices):
    choices = [f"{i}. {c}" for i, c in enumerate(choices, start=1)]
    if title:
        print(title)
    while True:
        print("\n".join(choices))
        answer = await ainput()
        try:
            answer = int(answer)
        except ValueError:
            continue
        if 1 <= answer <= len(choices):
            return answer - 1
