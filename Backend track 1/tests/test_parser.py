import pytest
from app.parser import GenericKeyValueParser, ParserException


def test_parser_valid_input():
    parser = GenericKeyValueParser()
    content = b"key1 = value1\nkey2 : value2\nkey3 value3\n"
    settings, diagnostics = parser.parse(content)

    assert len(settings) == 3
    assert settings[0].key == "key1"
    assert settings[0].value == "value1"
    assert settings[1].key == "key2"
    assert settings[1].value == "value2"
    assert settings[2].key == "key3"
    assert settings[2].value == "value3"
    assert len(diagnostics) == 0


def test_parser_duplicate_keys():
    parser = GenericKeyValueParser()
    content = b"key1 = value1\nkey1 = value2\n"
    settings, diagnostics = parser.parse(content)

    assert len(settings) == 0
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == "warning"
    assert diagnostics[0].code == "CONFLICTING_VALUE"


def test_parser_redaction():
    parser = GenericKeyValueParser()
    content = b"authentication.password = secret\nnormal = public\n"
    settings, _ = parser.parse(content)

    assert len(settings) == 2
    for s in settings:
        if s.key == "authentication.password":
            assert s.sensitive is True
        else:
            assert s.sensitive is False


def test_parser_malformed_input():
    parser = GenericKeyValueParser()
    content = b"!invalid_key = value\n"
    settings, diagnostics = parser.parse(content)

    assert len(settings) == 0
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "MALFORMED_LINE"
    assert diagnostics[0].severity == "warning"


def test_parser_unrecoverable_binary():
    parser = GenericKeyValueParser()
    content = b"\x00\x01\x02\x03\xff\xfe"
    with pytest.raises(ParserException) as exc:
        parser.parse(content)
    assert str(exc.value) == "UNSUPPORTED_FORMAT"
