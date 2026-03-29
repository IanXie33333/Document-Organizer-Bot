import importlib
import sys
from types import ModuleType, SimpleNamespace


def _import_permissions_module():
    discord_stub = ModuleType('discord')

    class Interaction:  # pragma: no cover - typing stub only
        pass

    class Member:  # pragma: no cover - typing stub only
        pass

    discord_stub.Interaction = Interaction
    discord_stub.Member = Member
    sys.modules['discord'] = discord_stub

    config_stub = ModuleType('config.settings')
    config_stub.get_settings = lambda: None
    sys.modules['config.settings'] = config_stub

    return importlib.import_module('bot.permissions')


class FakeRole:
    def __init__(self, role_id: int) -> None:
        self.id = role_id


class FakeMember:
    def __init__(self, role_ids: list[int], *, administrator: bool = False) -> None:
        self.roles = [FakeRole(rid) for rid in role_ids]
        self.guild_permissions = SimpleNamespace(administrator=administrator)


class FakeInteraction:
    def __init__(self, member: FakeMember | None, channel_id: int | None) -> None:
        self.user = member
        self.channel = SimpleNamespace(id=channel_id) if channel_id is not None else None


def _settings(*, admin_roles: set[int], uploader_roles: set[int], viewer_roles: set[int], channels: set[int]):
    return SimpleNamespace(
        admin_roles=admin_roles,
        uploader_roles=uploader_roles,
        viewer_roles=viewer_roles,
        channel_allowlist=channels,
    )


def test_can_upload_allows_discord_administrator_even_without_configured_role(monkeypatch) -> None:
    permissions = _import_permissions_module()
    monkeypatch.setattr(
        permissions,
        '_member',
        lambda interaction: interaction.user,
    )
    monkeypatch.setattr(
        permissions,
        'get_settings',
        lambda: _settings(admin_roles=set(), uploader_roles=set(), viewer_roles=set(), channels={1479314479488696403}),
    )
    interaction = FakeInteraction(FakeMember([], administrator=True), 1479314479488696403)
    assert permissions.can_upload(interaction) is True


def test_can_upload_still_requires_allowed_channel(monkeypatch) -> None:
    permissions = _import_permissions_module()
    monkeypatch.setattr(
        permissions,
        '_member',
        lambda interaction: interaction.user,
    )
    monkeypatch.setattr(
        permissions,
        'get_settings',
        lambda: _settings(admin_roles={1487744861162573865}, uploader_roles=set(), viewer_roles=set(), channels={1479314479488696403}),
    )
    interaction = FakeInteraction(FakeMember([1487744861162573865], administrator=False), 123)
    assert permissions.can_upload(interaction) is False
