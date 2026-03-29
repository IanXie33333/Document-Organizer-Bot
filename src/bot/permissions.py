from discord import Interaction, Member
from config.settings import get_settings


def _member(interaction: Interaction) -> Member | None:
    user = interaction.user
    return user if isinstance(user, Member) else None


def _role_ids(member: Member | None) -> set[int]:
    if not member:
        return set()
    return {role.id for role in member.roles}


def _is_discord_admin(member: Member | None) -> bool:
    return bool(member and getattr(member.guild_permissions, 'administrator', False))


def can_upload(interaction: Interaction) -> bool:
    settings = get_settings()
    member = _member(interaction)
    if member is None:
        return False

    roles = _role_ids(member)
    has_role_access = bool(roles.intersection(settings.admin_roles | settings.uploader_roles))
    has_access = has_role_access or _is_discord_admin(member)
    if not has_access:
        return False

    if not settings.channel_allowlist:
        return True
    return bool(interaction.channel and interaction.channel.id in settings.channel_allowlist)


def can_view(interaction: Interaction) -> bool:
    settings = get_settings()
    member = _member(interaction)
    if member is None:
        return False

    roles = _role_ids(member)
    has_role_access = bool(roles.intersection(settings.admin_roles | settings.viewer_roles | settings.uploader_roles))
    has_access = has_role_access or _is_discord_admin(member)
    if not has_access:
        return False

    if not settings.channel_allowlist:
        return True
    return bool(interaction.channel and interaction.channel.id in settings.channel_allowlist)


def can_view_by_role(interaction: Interaction) -> bool:
    settings = get_settings()
    member = _member(interaction)
    if member is None:
        return False

    roles = _role_ids(member)
    has_role_access = bool(roles.intersection(settings.admin_roles | settings.viewer_roles | settings.uploader_roles))
    has_access = has_role_access or _is_discord_admin(member)
    return has_access
