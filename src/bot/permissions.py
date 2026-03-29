from discord import Interaction, Member
from config.settings import get_settings


def _member(interaction: Interaction) -> Member | None:
    user = interaction.user
    return user if isinstance(user, Member) else None


def _role_ids(member: Member | None) -> set[int]:
    if not member:
        return set()
    return {role.id for role in member.roles}


def can_upload(interaction: Interaction) -> bool:
    settings = get_settings()
    member = _member(interaction)
    if member is None:
        return False
    roles = _role_ids(member)
    if roles.intersection(settings.admin_roles | settings.uploader_roles):
        if not settings.channel_allowlist:
            return True
        return bool(interaction.channel and interaction.channel.id in settings.channel_allowlist)
    return False


def can_view(interaction: Interaction) -> bool:
    settings = get_settings()
    member = _member(interaction)
    if member is None:
        return False
    roles = _role_ids(member)
    return bool(roles.intersection(settings.admin_roles | settings.viewer_roles | settings.uploader_roles))
