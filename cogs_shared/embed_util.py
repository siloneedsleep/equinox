import discord
from datetime import datetime


def create_premium_embed(title: str, description: str, color: int = 0x2b2d31, **kwargs) -> discord.Embed:
    """
    Tạo Embed cao cấp và đồng nhất cho toàn bộ hệ thống Equinox.
    Hỗ trợ chèn thêm fields, footer, author, thumbnail, image qua kwargs.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )

    if "fields" in kwargs:
        for field in kwargs["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=field.get("inline", False))

    if "thumbnail" in kwargs:
        embed.set_thumbnail(url=kwargs["thumbnail"])

    if "image" in kwargs:
        embed.set_image(url=kwargs["image"])

    if "author" in kwargs:
        author = kwargs["author"]
        embed.set_author(
            name=author.get("name"),
            icon_url=author.get("icon_url"),
            url=author.get("url")
        )

    footer_text = kwargs.get("footer_text", "🪐 Equinox Network • System Log")
    footer_icon = kwargs.get("footer_icon", None)
    embed.set_footer(text=footer_text, icon_url=footer_icon)

    return embed
