"""
# 前程无忧企业端
https://ehire.51job.com/
# 前程无忧登录地址
https://ehire.51job.com/MainLogin.aspx
# 登录后跳转到导航页面
https://ehire.51job.com/Navigate.aspx
# 简历搜索界面
https://ehire.51job.com/Candidate/SearchResumeLatestVersion.aspx
# Ajax 异步加载简历缩略信息
https://ehire.51job.com/ajax/Common/GlobalAjaxResumeInfo.aspx?doType=FetchResumeContentNew&SeqID=0&UserID=820285899&strKey=d4205781c1c87cea&strLang=0&strLastUpdate=1611633591000
data = {
    'doType': 'FetchResumeContentNew',
    'SeqID': '0',
    'UserID': '820285899',
    'strKey': 'd4205781c1c87cea',
    'strLang': '0',
    'strLastUpdate': '1611633591000'
}
# 简历详情
https://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID=826068817&hidEvents=23&pageCode=83&hidKey=071b4b282baa6409f6bffb1cfba86943
{
    'hidUserID': '826068817',
    'hidEvents': '23',
    'pageCode': '83',
    'hidKey': '071b4b282baa6409f6bffb1cfba86943'
}
看了一下简历详情的 Form 表单，太长了...，还是直接用 selenium 获取算了，先尝试一下登录吧
# chrome filter
-js / -png / -gif / -jpg / -css
"""

import os
import time
import json
import shutil
from contextlib import closing
from pydantic import BaseModel, validator
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from geecracker import GeeCracker, panel_visible, GeeConfig

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULT_PER_PAGE = 50  # 每页的结果数量
ACCOUNT_FILE = os.path.join(DATA_DIR, 'account.json')
TEST_ACCOUNT_FILE = os.path.join(DATA_DIR, 'account.test.json')
SEARCH_DATA_FILE = os.path.join(DATA_DIR, 'search_data.json')
TEST_SEARCH_DATA_FILE = os.path.join(DATA_DIR, 'search_data.test.json')

if not os.path.exists(TEST_ACCOUNT_FILE):
    shutil.copy(ACCOUNT_FILE, TEST_ACCOUNT_FILE)

if not os.path.exists(TEST_SEARCH_DATA_FILE):
    shutil.copy(SEARCH_DATA_FILE, TEST_SEARCH_DATA_FILE)


class Account(BaseModel):
    member_name: str
    username: str
    password: str

    @classmethod
    @validator(['member_name', 'username', 'password'], pre=True, always=True)
    def disallow_empty_string(cls, v):
        assert v != "", "cannot be empty string"
        return v


class SearchData(BaseModel):
    key: str
    # duration: str = "1年及以上" # 这个点击过程需要刷新，要进行特殊处理


class EHireConfig(BaseModel):
    account: Account
    search_data: SearchData
    gee_config: GeeConfig = GeeConfig()


class URLS:
    # driver.current_url 会带 /，但 document.URL 不带 /
    INDEX = "https://ehire.51job.com/"
    LOGIN_PAGE = "https://ehire.51job.com/MainLogin.aspx"
    NAVIGATE_PAGE = "https://ehire.51job.com/Navigate.aspx"
    SEARCH_PAGE = "https://ehire.51job.com/Candidate/SearchResumeLatestVersion.aspx"


class WAIT:
    PAGE_INTERVAL = 3
    WAIT_LOGIN_BUTTON = 5
    WAIT_SEARCH_BUTTON = 5
    WAIT_REFRESH = 3
    WAIT_RESULT = 3
    ACTION_INTERVAL = 0.5


class SELECTORS:
    """不同开头代表不同的选择器
    ID          id 选择器
    css         css 选择器
    """
    ID_LOGOUT = "MainMenuNew1_hl_LogOut"
    # 登录页面
    ID_MEMBER_NAME_INPUT = "txtMemberNameCN"        # 会员名 input
    ID_USERNAME_INPUT = "txtUserNameCN"             # 用户名 input
    ID_PASSWORD_INPUT = "txtPasswordCN"             # 密码 input
    ID_LOGIN_BUTTON = "Login_btnLoginCN"            # 登录按钮
    # 搜索页面
    ID_SEARCH_INPUT = "search_keyword_txt"          # 搜索内容 input
    CSS_SEARCH_BUTTON = ".search-people-btn.fl"     # 搜索按钮
    ID_DURATION_SELECT = "search_rsmupdate_input"   # 事件范围多选框
    ID_ONE_YEAR_AND_MORE = "search_rsmupdate_a_6"   # 一年及以上
    CSS_FORCE_LOGOUT = "#gvOnLineUser a"            # 强制退出登录


class CustomGeeCracker(GeeCracker):
    def __init__(self, *args, **kwargs):
        super(CustomGeeCracker, self).__init__(*args, **kwargs)

    def _validate(self) -> bool:
        # 如果不在在登录页面的地址，直接返回 True
        if self.driver.current_url not in (URLS.INDEX, URLS.LOGIN_PAGE):
            return True
        return super(CustomGeeCracker, self)._validate()

    def custom_validation(self) -> bool:
        """需要额外判断是否有强制下线这个选项，如果有则点击"""
        # 如果页面地址还在登录页面，才进行后续判断
        print("executed")
        if self.driver.current_url in (URLS.INDEX, URLS.LOGIN_PAGE):
            try:
                self.driver.find_element_by_css_selector(SELECTORS.CSS_FORCE_LOGOUT).click()
                print("退出按钮已点击")
            except NoSuchElementException:
                print("没有找到强制退出登录的按钮")
            finally:
                # 等待页面跳转
                time.sleep(WAIT.WAIT_REFRESH)
                # 根据页面地址是否为 NAVIGATE_PAGE 来判断是否登录成功
                return self.driver.current_url == URLS.NAVIGATE_PAGE
        return True


class EHire:
    def __init__(self, driver: WebDriver, config: EHireConfig):
        self.driver = driver
        # 配置数据
        self.account = config.account
        self.search_data = config.search_data
        self.gee_config = config.gee_config

    def main(self):
        try:
            self.run()
        except Exception as e:
            print(e)
            import pdb
            pdb.set_trace()

    def run(self):
        # 登录页面
        self.login()
        # 滑动验证
        if self.validate():
            # 搜索
            self.search()
            # 当还有下一页的时候，获取单页数据
            while self.has_next_page():
                self.parse_one_page()
                self.to_next_page()

    def login(self):
        self.driver.get(URLS.INDEX)
        login_button = WebDriverWait(self.driver, timeout=WAIT.WAIT_LOGIN_BUTTON).until(
            lambda d: d.find_element_by_id(SELECTORS.ID_LOGIN_BUTTON))
        member_name_input = self.driver.find_element_by_id(SELECTORS.ID_MEMBER_NAME_INPUT)
        username_input = self.driver.find_element_by_id(SELECTORS.ID_USERNAME_INPUT)
        password_input = self.driver.find_element_by_id(SELECTORS.ID_PASSWORD_INPUT)

        member_name_input.send_keys(self.account.member_name)
        time.sleep(WAIT.ACTION_INTERVAL)
        username_input.send_keys(self.account.username)
        time.sleep(WAIT.ACTION_INTERVAL)
        password_input.send_keys(self.account.password)
        time.sleep(WAIT.ACTION_INTERVAL)

        login_button.click()

    def validate(self):
        # 等待验证码出现
        time.sleep(WAIT.PAGE_INTERVAL)

        # 判断极验验证面板是否可见
        if panel_visible(self.driver):
            return CustomGeeCracker(self.driver, self.gee_config).validate()

    def search(self):
        # 搜索页面
        time.sleep(WAIT.PAGE_INTERVAL)

        assert self.driver.current_url not in (URLS.INDEX, URLS.LOGIN_PAGE), "未成功登录"
        self.driver.get(URLS.SEARCH_PAGE)

        search_input = self.driver.find_element_by_id(SELECTORS.ID_SEARCH_INPUT)
        duration_select = self.driver.find_element_by_id(SELECTORS.ID_DURATION_SELECT)

        search_input.send_keys(self.search_data.key)
        time.sleep(WAIT.ACTION_INTERVAL)
        duration_select.click()

        one_year_and_more = self.driver.find_element_by_id(SELECTORS.ID_ONE_YEAR_AND_MORE)
        one_year_and_more.click()

        # 需要放在选择行为之后，因为选择行为刷新了页面
        search_button = WebDriverWait(self.driver, timeout=WAIT.WAIT_SEARCH_BUTTON).until(
            lambda d: d.find_element_by_css_selector(SELECTORS.CSS_SEARCH_BUTTON))
        search_button.click()

    def parse_one_page(self):
        # 往下滚动页面直到页面底部
        script = "window.scrollTo(0, 20000)"
        self.driver.execute_script(script)
        # 简单等待一下数据刷新
        time.sleep(WAIT.WAIT_REFRESH)

        script = """
        result = JSON.stringify(
            $("#search_resume_list > ul > li").map((index, ele) => {
                let node = $(ele);
                return {
                    url: "https://ehire.51job.com" + node.attr("onclick").match(/GoToResumeView\\('([^\']+)/)[1],
                    name: node.find(".position-text").text()
                }
            }).toArray()
        );
        console.log(result);
        return result;
        """
        data = self.driver.execute_script(script)
        time.sleep(WAIT.WAIT_RESULT)
        with open('data/links.json', 'w', encoding='utf-8') as f:
            f.write(data)

    def has_next_page(self):
        """href 不为 undefined 就代表还有下一个链接"""
        script_ = """return $("#pagerBottomNew_nextButton").attr("href") !== undefined;"""
        return self.driver.execute_script(script_)

    def to_next_page(self):
        self.driver.find_element_by_id("pagerBottomNew_nextButton").click()
        time.sleep(WAIT.WAIT_REFRESH)

    def close(self):
        # 善后措施
        time.sleep(WAIT.PAGE_INTERVAL)
        try:
            self.driver.find_element_by_id(SELECTORS.ID_LOGOUT).click()
        except NoSuchElementException:
            pass
        self.driver.quit()


def get_configured_driver() -> WebDriver:
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')    # 浏览器最大化
    chrome_options.add_argument('--disable-gpu')        # 谷歌文档提到需要加上这个属性来规避bug
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def main():
    account = Account.parse_file(TEST_ACCOUNT_FILE)
    search_data = SearchData.parse_file(TEST_SEARCH_DATA_FILE)
    config = EHireConfig(account=account, search_data=search_data)
    # print(config)
    driver = get_configured_driver()
    with closing(EHire(driver, config)) as ehire:
        ehire.main()


if __name__ == '__main__':
    main()
