import pytest

import backend.manager as manager


@pytest.fixture(scope="module", autouse=True)
def sensitive_words(robot_code):
    words_group = {
        "group1": ["特么", "妈的"],
        "group2": ["草泥马"],
    }
    for label, words in words_group.items():
        result = manager.sensitive_words_train(robot_code, words, label)
        assert result["status_code"] == 0
    yield words_group
    manager.delete(robot_code)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,labels,strict,masked_text,words",
    [
        (
            "你特么，我草泥马啊",
            ["group1", "group2"],
            True,
            "你**，我***啊",
            [{"word": "特么", "end": 3, "start": 1}, {"word": "草泥马", "end": 8, "start": 5}],
        ),
        (
            "你特么，我草泥马啊",
            ["group1"],
            True,
            "你**，我草泥马啊",
            [{"word": "特么", "end": 3, "start": 1}],
        ),
        (
            "你特么，我草你妈啊",
            ["group2"],
            True,
            "你特么，我草你妈啊",
            [],
        ),
        (
            "你特么，我操你妈啊",
            ["group1", "group2"],
            False,
            "你**，我***啊",
            [{"word": "特么", "end": 3, "start": 1}, {"word": "操你妈", "end": 8, "start": 5}],
        ),
    ],
)
async def test_sensitive_words(robot_code, text, labels, strict, masked_text, words):
    result = await manager.sensitive_words(robot_code, text, labels=labels, strict=strict)
    assert result["masked_text"] == masked_text
    assert len(result["sensitive_words"]) == len(words)
    assert result["sentiment"] < 0.5
    for word, hyp_word in zip(words, result["sensitive_words"]):
        assert word["word"] == hyp_word["word"]
        assert word["start"] == hyp_word["start"]
        assert word["end"] == hyp_word["end"]
