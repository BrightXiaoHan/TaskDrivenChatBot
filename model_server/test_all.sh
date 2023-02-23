PORT=$1

if [ -z "$PORT" ]; then
    echo "Usage: $0 PORT"
    exit 1
fi

curl --location "http://127.0.0.1:${PORT}/xiaoyu/models/semantic-index" \
--header 'Content-Type: application/json' \
--data '{
    "sentences": [
        "这个苹果电脑100块钱"
    ]
}' > /dev/null


curl --location "http://127.0.0.1:${PORT}/xiaoyu/models/information-extraction" \
--header 'Content-Type: application/json' \
--data '{
    "categories": ["日期", "姓名"],
    "text": "我的生日是2022年1月一日， 名字叫韩冰"
}' > /dev/null


curl --location "http://127.0.0.1:${PORT}/xiaoyu/models/compare" \
--header 'Content-Type: application/json' \
--data '{
    "text_a": "前几天的时候，张三打了我一耳光，我想报复他",
    "text_b": "我会杀了他，那天他揍了我一顿"
}' > /dev/null


curl --location "http://127.0.0.1:${PORT}/xiaoyu/models/sentiment-analysis" \
--header 'Content-Type: application/json' \
--data '{
    "text": "前几天的时候，张三打了我一耳光，我想报复他"
}' > /dev/null


curl --location "http://127.0.0.1:${PORT}/xiaoyu/models/classification" \
--header 'Content-Type: application/json' \
--data '{
    "categories": ["喜事", "灾祸", "暴力倾向"],
    "text": "前几天的时候，张三打了我一耳光，我想报复他"
}' > /dev/null
