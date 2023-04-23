<div align="center">

# nonebot-plugin-mixin

_✨ ... ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/NCBM/nonebot-plugin-mixin.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-mixin">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-mixin.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

## 📖 介绍

...

## 💿 安装

通过 `nb-cli`:

```console
nb plugin install nonebot-plugin-mixin
```

## ⚙️ 配置

本插件增加了下列可选配置项，有需要的用户请自行在 `.env` 中配置：

```python
# 下列配置项请按需解除注释并配置
# 本配置文件中的所有概率均在 0~1 之间

# 收到任意消息时发送括号的概率
# mixin_base_chance=0.12

# 收到末尾带括号消息时发送括号的概率
# mixin_purpose_chance=0.42

# 用于检测与发送的括号备选列表（字符串）
# mixin_brackets=（

# 在消息文本末尾为半角括号时是否以同等概率发送“半角异端！”
# mixin_nohalfsize=true
```
