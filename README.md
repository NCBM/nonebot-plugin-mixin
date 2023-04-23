<div align="center">

# nonebot-plugin-mixin

_✨ 通过代码或非代码方式外部介入 NoneBot2 插件行为 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/NCBM/nonebot-plugin-mixin.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-mixin">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-mixin.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

## 📖 介绍

本插件允许通过代码/非代码方式介入插件内部 Matcher 的行为。

## 💿 安装

通过 `nb-cli`:

```console
nb plugin install nonebot-plugin-mixin
```

## ⚙️ 配置

本插件增加了下列可选配置项，有需要的用户请自行在 `.env` 中配置：

```python
# 下列配置项请按需解除注释并配置

# Mixin 数据文件路径（可选），支持 json 格式。
# mixin_source=["hello_mixin.json", "justsix_mixin.json"]
```

## 使用

### 加载静态数据

> 本插件目前支持加载 json 数据。

要加载静态的 Mixin 数据，需要将数据文件路径加入配置文件中的 `mixin_source` 中，然后启动项目即可。数据格式参阅下面的[数据结构](#数据结构)。

```json
[
    {
        "source": {
            "module_name": "nonebot_plugin_helloworld"
        },
        "dest": {
            "rule": {
                "fullmatch": {
                    "msg": ["fxxk", "fxxkyou", "caonima"]
                }
            },
            "priority": 42
        }
    }
]
```

### 从代码加载

```python
from nonebot import require

mixin = require("nonebot_plugin_mixin")

my_mixins = []
my_mixins.append(
    mixin.Mixin(
        source=mixin.MixinQuery(
            module_name="nonebot_plugin_helloworld"
        ),
        dest=mixin.MixinData(
            rule=mixin.MixinRule(
                fullmatch=mixin.CaseMatch(msg=("fxxk", "fxxkyou", "caonima"))
            ),
            priority=42
        )
    )
)

mixin.multi_mixin(my_mixins)
```

### 数据结构

下面是一个 Mixin 对象的整体结构：

> 注：**可选参数**的类型前面会加星号 `*`。

```text
mixin: Mixin
    source: MixinQuery  # 此段参数只用于查询要修改的 Matcher
        plugin_name: *str
        module_name: *str
        type: *str
        rule: *MixinRule
            startswith: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            endswith: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            fullmatch: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            keywords: *Tuple[str, ...]
                "keyword1"
                ...
            command: *Tuple[Tuple[str, ...]]
                ("command1",)
                ("command2", "sub")
                ...
            regex: *ReMatch
                regex: str
                flags: int = 0
            to_me: bool = False
        priority: *int
        block: *bool
    dest: MixinData  # 此段参数只用于选择性修改 Matcher 的属性
        type: *str
        rule: *MixinRule
            startswith: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            endswith: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            fullmatch: *CaseMatch
                msg: Tuple[str, ...]
                ignorecase: bool = False
            keywords: *Tuple[str, ...]
                "keyword1"
                ...
            command: *Tuple[Tuple[str, ...]]
                ("command1",)
                ("command2", "sub")
                ...
            regex: *ReMatch
                regex: str
                flags: int = 0
            to_me: bool = False
        priority: *int
        block: *bool
```

而读取静态文件时，本插件默认会从某个文件中读取单个或多个并列的 Mixin 规则，因此数据文件的最上级必须是一个序列。例如：

```json
[
    {
        "source": ...,
        "dest": ...
    },
    ...
]
```

### 覆盖规则

可选参数只有给定具体有效值的属性会被完全覆盖，未给定具体有效值的属性默认保留。
