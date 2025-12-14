"""
Simple test to verify pytest configuration
"""
import pytest


class TestPytestSetup:
    """Test class to verify pytest is working correctly."""

    def test_simple_assertion(self):
        """Test basic assertion works."""
        assert 1 + 1 == 2

    def test_string_operations(self):
        """Test string operations."""
        assert "hello".upper() == "HELLO"

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function works."""
        import asyncio
        await asyncio.sleep(0.01)
        assert True

    @pytest.mark.unit
    def test_with_marker(self):
        """Test with custom marker."""
        assert [1, 2, 3][0] == 1
