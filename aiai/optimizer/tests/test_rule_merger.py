from unittest.mock import patch

from aiai.optimizer.rule_merger import Rules, merge_rules


# Patch the .create method which is called internally
@patch("instructor.Instructor.create")
def test_merge_rules(mock_create):
    # Arrange: Define what the mocked LLM call should return
    mock_create.return_value = Rules(always=["always combined"], never=["never combined"], tips=["combined tip"])

    before = Rules(always=["always do this"], never=["never do that"], tips=["consider this"])
    after = Rules(always=["also always"], never=["also never"], tips=["another tip"])

    # Act
    merged = merge_rules(before, after, model="openai/o4-nano")

    # Assert: Check if the mock was called and the result is as expected (based on mock return)
    mock_create.assert_called_once()
    assert merged.always == ["always combined"]
    assert merged.never == ["never combined"]
    assert merged.tips == ["combined tip"]
