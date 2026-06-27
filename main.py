import asyncio
import redis.asyncio as redis
from core.bot import EquinoxBot
from backend.web_server import EquinoxWebServer
from config.settings import LUMINOUS_TOKEN, TENEBRIS_TOKEN, REDIS_URI

async def run_ecosystem():
    redis_client = redis.from_url(REDIS_URI, decode_responses=True)
    
    luminous = EquinoxBot(
        bot_name="Luminous",
        command_prefix="l!",
        theme_color=0xFCE883,
        persona="Luminous"
    )
    
    tenebris = EquinoxBot(
        bot_name="Tenebris",
        command_prefix="t!",
        theme_color=0x2B2D31,
        persona="Tenebris"
    )

    web_server = EquinoxWebServer(redis_client)

    shared_extensions = [
        "cogs_shared.status_ui",
        "cogs_shared.system_core",
        "cogs_shared.interaction_labs"
    ]

    async def inject_setup(bot):
        original_setup = bot.setup_hook
        async def new_setup():
            if original_setup:
                await original_setup()
            await bot.load_module_cogs(shared_extensions)
        bot.setup_hook = new_setup

    await inject_setup(luminous)
    await inject_setup(tenebris)

    print("[Equinox Core] Đang đánh thức hệ sinh thái và nạp đa luồng...")
    
    await asyncio.gather(
        luminous.start(LUMINOUS_TOKEN),
        tenebris.start(TENEBRIS_TOKEN),
        web_server.start()
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_ecosystem())
    except KeyboardInterrupt:
        print("\n[Equinox Core] Đã dập cầu dao. Ngắt kết nối an toàn toàn bộ hệ sinh thái.")
