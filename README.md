# Poker Bot

[![Actions Status](https://github.com/yfzm/poker-bot/workflows/build/badge.svg)](https://github.com/yfzm/poker-bot/actions)
[![Release](https://img.shields.io/github/v/release/yfzm/poker-bot?include_prereleases)](https://github.com/yfzm/poker-bot/releases)
[![License](https://img.shields.io/github/license/yfzm/poker-bot)](https://github.com/yfzm/poker-bot/license)

一款基于Slack的德州扑克机器人。

## 安装

您可以使用`pipenv`来安装依赖：

```bash
pipenv install
```

运行程序前需要注入机器人的token：

```bash
export SLACK_BOT_TOKEN="xxxx"
```

最后运行`run.py`：

```bash
python run.py
```

> 注意: python版本至少为3.7。

## 部署

使用[Git-Auto-Deploy](https://github.com/olipo186/Git-Auto-Deploy)来自动化部署，配置请参考[这里](https://github.com/olipo186/Git-Auto-Deploy/blob/master/docs/Configuration.md)。

当新的PR成功合并到dev上时，会自动触发执行部署脚本`deploy.sh`。
