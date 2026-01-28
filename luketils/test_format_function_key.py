"""Unit tests for function key formatting."""

from luketils.marimo_profile import (
    FunctionKey,
    _format_function_key,
    _format_function_name,
    _find_class_context,
)


def test_format_function_name_basic():
    """Test basic function name formatting."""
    assert _format_function_name("my_func", None) == "my_func()"
    assert _format_function_name("", None) == "<unknown>"
    assert _format_function_name("~", None) == "<built-in>"
    assert _format_function_name("<module>", None) == "<module-level>"


def test_format_function_name_with_class():
    """Test function name formatting with class context."""
    assert _format_function_name("my_method", "MyClass") == "MyClass:my_method()"
    assert _format_function_name("__init__", "MyClass") == "MyClass:__init__()"


def test_find_class_context():
    """Test class context detection in the actual source file."""
    # Test with a module-level function (should return None)
    result = _find_class_context(
        "luketils/marimo_profile.py", 23, "_find_git_root_for_path"
    )
    assert result is None, f"Expected None for module-level function, got {result}"


def test_format_function_key_builtin():
    """Test formatting built-in functions."""
    key = FunctionKey(filename="<built-in>", line=None, function_name="sum")
    result = _format_function_key(key)
    assert result.display_name == "sum()"
    assert result.file_path == "<built-in>"
    assert result.line_number == 0


def test_format_function_key_regular():
    """Test formatting regular functions."""
    key = FunctionKey(filename="/tmp/test.py", line=10, function_name="my_func")
    result = _format_function_key(key)
    assert result.display_name == "my_func()"
    assert result.line_number == 10


def test_format_function_key_module_level():
    """Test formatting module-level functions."""
    # Test with a module-level function (line 23 is _find_git_root_for_path)
    key = FunctionKey(
        filename="luketils/marimo_profile.py",
        line=23,
        function_name="_find_git_root_for_path",
    )
    result = _format_function_key(key)
    # Should NOT detect a class (module-level function)
    assert result.display_name == "_find_git_root_for_path()", \
        f"Expected '_find_git_root_for_path()', got '{result.display_name}'"
    assert ":" not in result.display_name, "Module-level function should not have class prefix"


if __name__ == "__main__":
    print("Running tests...")
    test_format_function_name_basic()
    print("✓ test_format_function_name_basic")

    test_format_function_name_with_class()
    print("✓ test_format_function_name_with_class")

    test_find_class_context()
    print("✓ test_find_class_context")

    test_format_function_key_builtin()
    print("✓ test_format_function_key_builtin")

    test_format_function_key_regular()
    print("✓ test_format_function_key_regular")

    test_format_function_key_module_level()
    print("✓ test_format_function_key_module_level")

    print("\nAll tests passed! ✨")
