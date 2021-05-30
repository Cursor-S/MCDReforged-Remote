# MCDReforged-Remote
一个MCDR插件+Java库，允许用户通过该库实现QQ，MC双向聊天，服务器控制等功能

### 插件依赖
#### Python包
* requests
* hashlib
* socket
* threading
#### MCDR前置插件
* [OnlinePlayerAPI](https://github.com/zhang-anzhi/MCDReforgedPlugins/tree/master/OnlinePlayerAPI)
* [ConfigAPI](https://github.com/hanbings/ConfigAPI)
* [JsonDataAPI](https://github.com/zhang-anzhi/MCDReforgedPlugins/tree/master/JsonDataAPI)

### 配置
配置文件位于 `config\MCDReforged-Remote\MCDReforged-Remote.yml`
* tcp_server
    * `host` - 默认值 `127.0.0.1` - 服务器所在ip
    * `port` - 默认值 `64000` - 本插件连接端口
    * `authKey` - **您必须更改此设置** - 远程连接该插件所使用的验证码
* QQBot
    * `group_id` - 服内向QQ发送消息时需要送达的群群号
    * `host` - 默认值 `127.0.0.1` - QQ机器人所在服务器IP
    * `port` - 默认值 `65000` - QQ机器人HTTP服务端口

### 基础使用
本插件与 [CuBitStudio/CubikBot](https://www.github.com/CuBitStudio/Cubikbot) 直接兼容，可以直接运行并使用Java库内所有功能。

MC向QQ发送信息的功能与 [kukume/kukubot](https://www.github.com/kukume/kukubot) ，使用 [IceCreamQAQ Yu Web-Core](https://maven.icecreamqaq.com/#browse/browse:maven-releases:com%2FIceCreamQAQ%2FYu%2FWebCore) WebController 以及
（理论上）所有支持 HTTP 控制器的QQ机器人兼容。

### 高级开发
如果您希望直接使用Java库进行开发，请遵循以下步骤：
1. 将本插件像其他MCDR插件一样安装（将py文件放入plugins文件夹内）
2. 在项目内添加maven仓库 `https://maven.cubik65536.top/repository/maven-public/`
3. 在项目内添加依赖 `top.cubik65536.top:MCDReforged-Remote:1.0-RC`
4. 您现在可以使用Java库内的功能了！每个函数都已经有了基本的Doc注释来帮助理解。

开发文档：正在撰写