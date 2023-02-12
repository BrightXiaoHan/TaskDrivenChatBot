# 硬编码优化内容

这个文件夹包含了跟项目强相关的一些hardcoding优化

## 硬编码优化说明

### 社区矫正项目

须在配置文件或者环境变量中配置`project_name`为`shejiao`

#### intent_location_no_guangdong

优化场景为询问是否离开了管辖地，如果抽取到了地址但是没有包含东莞，则认为离开了管辖地。

### 广东监狱项目

须在配置文件或者环境变量中配置`project_name`为`guangdong_prison`

具体增加的内置实体和意图见 [guangdong_prison.py](./guangdong_prison.py)
