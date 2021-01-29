# geecracker

[文章一]: https://gitee.com/bingesun/geeCheck
[文章二]: https://www.cnblogs.com/cocc/p/10820359.html
[文章三]: https://github.com/CrazyBunQnQ/GeetestCrack

极验验证 (geetest) Selenium 破解方式，参考了以下几篇文章:

[文章一], [文章二], [文章三]

## Install

```shell
pip install geecracker
```

## Usage

```python
from geecracker import validate, panel_visible, GeeConfig

# 省略 selenium 登录到面板出现的代码，具体流程可以参考 tests/main.py

# GeeConfig 可以使用默认参数，如果需要修改配置以使更适合自己的项目的话，再考虑进行修改
gee_config = GeeConfig()

# 判断极验验证面板是否可见
if panel_visible(driver):
    # 开始验证
    validate(driver, gee_config)
```

## Advanced

```python
from geecracker import GeeCracker, panel_visible, GeeConfig


class CustomGeeCracker(GeeCracker):
    def __init__(self, *args, **kwargs):
        super(CustomGeeCracker, self).__init__(*args, **kwargs)

    def _validate(self) -> bool:
        # rewrite validation process
        return super(CustomGeeCracker, self)._validate()

    def custom_validation(self) -> bool:
        # this will be automatically added to _validation_passed
        # it's not recommended to modify _validation_passed to ensure GeeCracker works correctly
        return True

    ... # other methods could be rewrite too


... # your codes

CustomGeeCracker(self.driver, self.gee_config).validate()
```

## Contribute

if you want to contribute to this project, follow the steps below

```shell
# in you virtual env, run
pip install -r requirements.txt
# test your code
# currently I don't have enought time to add another test case,
# if you're intereseted in this project, it'll be grateful that you create your own test case with enthusiasm
# use your own ehire account, modify tests/data/account.test.json and tests/data/search_data.test.json
python -m tests.ehire.main
```

feel free to submit a pull request 😆
