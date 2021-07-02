# 对话工厂训练数据定义-FAQ

### 通用参数

请求方法 

post:  http://{ip}:{port}/xiaoyu/faq参数说明

| 参数名称 | 参数类型 | 参数描述                                        |
| -------- | -------- | ----------------------------------------------- |
| robot_id | str      | 标识当前faq数据属于哪个机器人，机器人的唯一标识 |
| method   | str      | 请求方法，目前有“add”,"update","delete"         |
| version   | str      | 训练版本号         |
| data     | any      | 调用对应method所需要的参                        |
|          |          |                                                 |

请求示例

```http
POST http://{ip}:{port}/xiaoyu/faq HTTP/1.1
Content-Type: application/json

{
	"robot_id": "robot_one"
    "method": "add",
    "version": "20210305001"
    "data": ...
}
```

参数说明

| 参数名称 | 参数类型 | 参数描述                                |
| -------- | -------- | --------------------------------------- |
| method   | str      | 请求方法，目前有“add”,"update","delete", "ask" |
| msg   | str      | 返回消息内容 |
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

### 增加数据，更新数据
add，update方法现在相同，调用哪一个都可以，对于新的数据进行添加，对于已经存在的数据直接覆盖更新

data参数示例

```json
POST http://{ip}:{port}/xiaoyu/faq HTTP/1.1
Content-Type: application/json

{
    "method": "add",
    "robot_id": "robot_one"
    "version": "20210305001"
    "data": [
        {
        	"faq_id": "id1"
            "title": "苹果手机多少钱",
            "similar_questions": [
                "Apple手机多少钱",
                "iphone多少钱"
            ],
            "related_quesions": [
                "ipad多少钱",
                "iwatch多少钱"
            ],
            "key_words": [
                "苹果",
                "Apple",
                "iphone"
            ],
            "effective_time": "2020-12-31",
            "tags": [
                "手机",
                "电子产品"
            ],
            "answer": "5400元",
            "catagory": "电子产品价格"
        },
        {...},
        {...}
    ]
}

```

数据参数说明

| 参数名称          | 参数类型 | 参数描述                                                     |
| ----------------- | -------- | ------------------------------------------------------------ |
| faq_id             | str      | 当前FAQ知识标题，也是唯一标识                                |
| title             | str      | faq数据的标题，不作为唯一标识                               |
| similar_questions | list     | 添加相似问题可以让算法匹配更加精准，例如：“如何申请退款”相似问题“这个款怎么退？” |
| related_questions | list     | 添加关联知识可以让您控制“触发问题后的知识推荐”， 即用户触发该问题后会依据关联知识和算法继续进行问句推荐。 |
| key_words         | list     | 请填写和这个问题最相关的名词，填写核心词后用户问题定位更加准确，机器人还可以针对核心词做上下文问答. |
| effective_time    | datetime | YY-MM-DD格式日期                                             |
| tags              | list     | 标签仅用于知识分类，不被机器人用于识别定位问题。             |
| answer            | str      | 问题的答案，可以是富文本，包含图片、视频等多媒体。           |
| catagory          | str      | 分类类目，用于问题归档分类。                                 |
| perspective       | str      | 视角，多个视角用逗号隔开                                |

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


### 删除数据（method为delete）

data参数示例

```js
POST http://{ip}:{port}/xiaoyu/faq HTTP/1.1
Content-Type: application/json

{
    "robot_id": "robot_one"
    "method": "delete",
    "data": {
		"faq_ids": ["苹果手机多少钱"]
    }
}


```

参数说明

| 参数名称   | 参数类型 | 参数描述                         |
| ---------- | -------- | -------------------------------- |
| faq_ids    | list     | 需要删除的faq训练数据对应的faq_id |
|            |          |                                  |

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

### FAQ问答测试接口
本接口仅用于faq问答测试，与小语机器人正式的问答接口不同。

请求示例

```js
POST http://{ip}:{port}/xiaoyu/faq HTTP/1.1
Content-Type: application/json

{
    "robot_id": "robot_one"
    "method": "ask",
    "data": {
		"question": "苹果手机多少钱"
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
        "faq_id": "id1"
        "title": "苹果手机多少钱",
        "similar_questions": [
            "Apple手机多少钱",
            "iphone多少钱"
        ],
        "related_quesions": [
            "ipad多少钱",
            "iwatch多少钱"
        ],
        "key_words": [
            "苹果",
            "Apple",
            "iphone"
        ],
        "effective_time": "2020-12-31",
        "tags": [
            "手机",
            "电子产品"
        ],
        "answer": "5400元",
        "catagory": "电子产品价格"
    }
}
```

参数说明

| 参数名称   | 参数类型 | 参数描述                         |
| ---------- | -------- | -------------------------------- |
| data    | dict     |  返回的是用户问题再faq库中匹配到的训练数据          |
|            |          |                                  |
