from aiai.optimizer.rule_merger import Rules, merge_rules


def test_merge_rules():
    before = Rules(always=["always do this"], never=["never do that"], tips=["consider this"])
    after = Rules(always=["always do this"], never=["never do that"], tips=["consider this"])
    merged = merge_rules(before, after)
    assert "always do this" in merged.always
    assert "never do that" in merged.never
    assert "consider this" in merged.tips
