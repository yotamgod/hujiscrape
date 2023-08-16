# hujiscrape

This is a simple scraping tool for HUJI sites.

* When running on Windows, make sure to add the following:
>     def main():
>         ...
>         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
>         ...
>         asyncio.run(coroutine)

Disclaimer: The project is in no way affiliated with The Hebrew University of Jerusalem, and was built independently.