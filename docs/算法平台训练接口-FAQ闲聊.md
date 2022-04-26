# 对话工厂训练数据定义-基于FAQ的闲聊

## 通用参数

请求方法

post:  <http://{ip}:{port}/xiaoyu/faq/chitchat>参数说明

| 参数名称 | 参数类型 | 参数描述                                        |
| -------- | -------- | ----------------------------------------------- |
| method   | str      | 请求方法，目前有“add”,"update","delete"         |
| version   | str      | 训练版本号         |
| data     | any      | 调用对应method所需要的参                        |

请求示例

```http
POST http://{ip}:{port}/xiaoyu/faq/chitchat HTTP/1.1
Content-Type: application/json

{
    "method": "add",
    "data": ...
}
```

参数说明

| 参数名称 | 参数类型 | 参数描述                                |
| -------- | -------- | --------------------------------------- |
| method   | str      | 请求方法，目前有“add”,"update","delete", "ask" |
| data     | any      | 调用对应method所需要的参数              |

返回示例

```json
{
    "status": "200",
    "msg": "请求成功",
    "data": ...
}
```

参数说明

| 参数名称 | 参数类型 | 参数描述                                |
| -------- | -------- | --------------------------------------- |
| status   | str      | 服务状态码，200为请求成功，500为系统内部错误 |
| msg     | str     | 如果状态码是200则返回“请求成功”，如果状态码是500则返回错误堆栈信息，方便调试              |
| data     | any      | 调用对应method的返回参数，只有在状态码为200时存在             |

## 增加数据，更新数据

add，update方法现在相同，调用哪一个都可以，对于新的数据进行添加，对于已经存在的数据直接覆盖更新

data参数示例

```json
POST http://{ip}:{port}/xiaoyu/faq/chitchat HTTP/1.1
Content-Type: application/json

{
    "method": "add",
    "data": [
        {
            "chatfestId": "id1",
            "theme": "你好啊",
            "similar_questions": [
                "Hello",
                "Hi"
            ],
            "answers": [
                "你也好啊！"
                "我叫小语，你也好啊。"
            ],
        },
        {...},
        {...}
    ]
}

```

数据参数说明

| 参数名称          | 参数类型 | 参数描述                                                     |
| ----------------- | -------- | ------------------------------------------------------------ |
| chatfestId             | str      | 当前闲聊主题id，也是唯一标识                                |
| theme             | str      | 闲聊主题名称，不作为唯一标识                               |
| similar_questions | list     | 闲聊问法集合 |
| answers            | list      | 问题的答案，可以是富文本，包含图片、视频等多媒体。应当包含多个答案，每次从中随机选取           |

返回参数示例

```json
{
    "status": "200",
    "msg": "请求成功",
    "data": {
        "status_code": 0
    }
}
```

data参数说明

| 参数名称 | 参数类型 | 参数描述                                |
| -------- | -------- | --------------------------------------- |
| status_code   | int      | 0为数据删除成功，1为数据删除失败 |

## 删除数据（method为delete）

data参数示例

```js
POST http://{ip}:{port}/xiaoyu/faq HTTP/1.1
Content-Type: application/json

{
    "robot_id": "robot_one"
    "method": "delete",
    "data": {
        "chatfestIds": ["id1"]
    }
}


```

参数说明

| 参数名称   | 参数类型 | 参数描述                         |
| ---------- | -------- | -------------------------------- |
| chatfestIds    | list     | 需要删除的faq训练数据对应的chatfestId |

返回参数示例

```json
{
    "status": "200",
    "msg": "请求成功",
    "data": {
        "status_code": 0
    }
}
```

data参数说明

| 参数名称 | 参数类型 | 参数描述                                |
| -------- | -------- | --------------------------------------- |
| status_code   | int      | 0为数据添加更新成功，1为数据添加更新失败 |

## 问答测试接口

本接口仅用于faq闲聊问答测试，与小语机器人正式的问答接口不同。

请求示例

```js
POST http://{ip}:{port}/xiaoyu/faq/chitchat HTTP/1.1
Content-Type: application/json

{
    "method": "ask",
    "data": {
        "question": "hello"
    }
}
```

参数说明

| 参数名称   | 参数类型 | 参数描述                         |
| ---------- | -------- | -------------------------------- |
| question    | str     | 用户提问的问题           |
|            |          |                                  |

返回示例

```js
{
    "status": "200",
    "msg": "请求成功",
    "data": {
        "answers": "你也好啊！"
    }
}
```

参数说明

| 参数名称   | 参数类型 | 参数描述                         |
| ---------- | -------- | -------------------------------- |
| data    | dict     |  返回的是用户问题再faq库中匹配到的训练数据          |
