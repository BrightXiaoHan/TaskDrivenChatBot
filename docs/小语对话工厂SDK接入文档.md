 

# 注意：

接入小语对话工厂SDK，需要严格按照以下步骤进行操作接入流程。

1、在小语对话工厂注册企业信息，并审核通过；

2、登陆小语对话工厂，设置机器人接入渠道（登陆 -> 机器人 -> 渠道配置 -> 创建API接入）；

3、获取创建渠道信息的robotId，channelId，apiKey、Api调用地址；

4、开始接入：

# 1）获取机器人所属企业信息

请求地址：API调用地址/v1/api/session/enterprise

请求方式：get

请求参数：

| 参数    | 类型 | 必须 | 说明     |
| ------- | ---- | ---- | -------- |
| robotId | Long | 是   | 机器人ID |

返回值说明：

| 参数        | 类型   | 说明         |
| ----------- | ------ | ------------ |
| robotName   | String | 机器人名称   |
| companyName | String | 企业名称     |
| tel         | String | 企业联系电话 |
| address     | String | 企业地址     |
| webSite     | String | 企业网站     |
| photoUrl    | String | 企业头像     |

 

# 2）获取渠道配置信息（web接入时才需要）

请求地址：API调用地址/v1/api/session/channel

请求方式：get

请求参数：

| 参数      | 类型 | 必须 | 说明   |
| --------- | ---- | ---- | ------ |
| channelId | Long | 是   | 渠道ID |

返回值说明：

| 参数           | 类型   | 说明                               |
| -------------- | ------ | ---------------------------------- |
| themeColor     | String | 主题颜色                           |
| buttonStyle    | String | 按扭样式                           |
| buttonImg      | String | 按扭图片                           |
| windowType     | String | 窗口类型                           |
| supportLike    | Int    | 是否支持点赞、点踩，0不支持，1支持 |
| supportComment | int    | 是否支持评价，0不支持，1支持       |
| commentOption  | String | 评价选项，为json格式               |

 

# 3）创建会话接口

请求地址：API调用地址/v1/api/session/create

请求方式：post

请求参数：

| 参数      | 类型   | 必须 | 说明                                                |
| --------- | ------ | ---- | --------------------------------------------------- |
| robotId   | Long   | 是   | 机器人ID                                            |
| channelId | Long   | 是   | 渠道ID                                              |
| ts        | Long   | 是   | 当前时间戳，从1970年1月1日0点0分0秒开始到现在的秒数 |
| sign      | String | 是   | 加密数字签名(基于HMACSHA1算法)                      |
| userId    | String | 是   | 用户ID,要求全局唯一                                 |
| nick      | String | 是   | 用户呢称                                            |

## signa生成

a、获取baseString，baseString由是ts、robotId、channelId、userId、nick五个参数以”&”按顺序拼接而成。

baseString示例:

ts=111111&robotId=222&channelId=333&userId=666&nick=zhangsan

b、对baseString进行MD5加密生成32位的长度。

c、以apiKey为key对MD5之后的baseString字符串进行HmacSHA1加密，再对加密后的字符串进行base64编码。

## 注意：

apiKey：接口密钥，在创建渠道信息时自动生成，调用方请注意保管；

sign的生成公式：Base64(HmacSHA1(MD5(ts&robotId&channelId&userId&nick),apiKey))

返回值JSON：

```
{

  "code":"200",

  "msg":"请求成功",

  "data":{

​    "msgId":1111111,

​    "userId":"xiaoyu",

​    "answers":["您好，欢迎您使用小语机器人","您想咨询什么问题"],

​    "recommendQuestions":[],//推荐问题

​    "relatedQuestions":[],//关联问题

​    "hotQuestions":[],//常见问题

​    "status":1

  }

}
```



返回值说明：

| 参数               | 类型     | 说明                                                         |
| ------------------ | -------- | ------------------------------------------------------------ |
| code               | String   | 返回消息编码，具体值见消息编码                               |
| msg                | String   | 返回消息描述                                                 |
| msgId              | Long     | 消息ID                                                       |
| userId             | String   | 用户ID                                                       |
| answers            | String[] | 答案                                                         |
| recommendQuestions | String[] | 推荐问题                                                     |
| relatedQuestions   | String[] | 关联问题                                                     |
| hotQuestions       | String[] | 常见问题                                                     |
| status             | int      | 状态，可选值：1表示识别成功，2表示无法精准识别，3表示无法识别问题； |

answers字段说明：系统欢迎语、识别到用户问题的回复内容；

recommendQuestions字段说明：针对用户的提问进行语义分析识别到的相拟问题；

relatedQuestions字段说明：针对识别到用户的问题，所配置的关联问题；

hotQuestions字段说明：系统配置的固定常见问题；

status字段说明：status=1表示识别成功，answers是所识别的答案，recommendQuestions、hotQuestions为空，relatedQuestions如果配置了关联问题就是非空，未配置关联问题为空；

status=2表示无法精准识别，answers、relatedQuestions为空，recommendQuestions、hotQuestions可能是非空。

Status=3表示无法识别问题，answers、relatedQuestions为空，recommendQuestions、hotQuestions可能是非空。

# 4）用户信息回复接口

请求地址：API调用地址/v1/api/session/replay

请求方式：post

请求参数：

| 参数      | 类型   | 必须 | 说明                                                |
| --------- | ------ | ---- | --------------------------------------------------- |
| robotId   | Long   | 是   | 机器人ID                                            |
| channelId | Long   | 是   | 渠道ID                                              |
| ts        | Long   | 是   | 当前时间戳，从1970年1月1日0点0分0秒开始到现在的秒数 |
| sign      | String | 是   | 加密数字签名(基于HMACSHA1算法)                      |
| userId    | String | 是   | 用户ID,要求全局唯一                                 |
| nick      | String | 是   | 用户呢称                                            |
| question  | String | 是   | 用户的问题                                          |

##　signa生成

d、获取baseString，baseString由是ts、robotId、channelId、userId、nick、question六个参数以”&”按顺序拼接而成。

baseString示例:

ts=111111&robotId=222&channelId=333&userId=666&nick=zhangsan&question=你好

e、对baseString进行MD5加密生成32位的长度。

f、以apiKey为key对MD5之后的baseString字符串进行HmacSHA1加密，再对加密后的字符串进行base64编码。

## 注意：

apiKey：接口密钥，在创建渠道信息时自动生成，调用方请注意保管；

sign的生成公式：Base64(HmacSHA1(MD5(ts&robotId&channelId&userId&nick&question),apiKey))

返回值JSON同创建会话接口返回值一样

# 5）赞/踩回复接口

 

# 6）服务满意度调查接口

 

# 5、消息编码

| 编码  | 说明                          |
| ----- | ----------------------------- |
| 200   | 返回成功                      |
| 61101 | 机器人不存在                  |
| 61102 | 机器人己停用                  |
| 61103 | 机器人未配置算法平台          |
| 61104 | 未创建会话信息                |
| 69001 | 系统繁忙                      |
| 69002 | signa签名错误                 |
| 69003 | 参数错误                      |
| 69004 | question的长度不能超过500字符 |

 