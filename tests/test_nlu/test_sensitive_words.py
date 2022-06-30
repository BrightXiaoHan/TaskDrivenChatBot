from backend.nlu import WordsSearch


def test_sensitive_words():
    words = "中国人|乾清宫"
    search = WordsSearch()
    search.SetKeywords(words.split("|"))
    text = "我是中国人"
    words, masked_text = search.FindAll(text)
    assert len(words) == 1
    assert words[0]["start"] == 2
    assert words[0]["end"] == 5
    assert words[0]["word"] == "中国人"
    assert masked_text == "我是***"
