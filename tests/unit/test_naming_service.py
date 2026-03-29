from services.naming_service import build_filename


def test_build_filename_formats_components() -> None:
    value = build_filename('My Project', 'Meeting Notes', 'Kickoff Doc', 1, 'pdf', '%Y%m%d')
    assert value.endswith('_v01.pdf')
    assert 'My_Project' in value
    assert 'Meeting_Notes' in value
