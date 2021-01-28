import os
import time
import json
import shutil
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from geecracker import validate, panel_visible, GeeConfig


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class URLS:
    INDEX = "https://ehire.51job.com/"
    LOGIN_PAGE = "https://ehire.51job.com/MainLogin.aspx"
    SEARCH_PAGE = "https://ehire.51job.com/Candidate/SearchResumeLatestVersion.aspx"


class WAIT:
    PAGE_INTERVAL = 3
    WAIT_LOGIN_BUTTON = 5
    WAIT_SEARCH_BUTTON = 5
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
    CSS_SEARCH_BUTTON = ".search-people-btn .fl"    # 搜索按钮
    ID_DURATION_SELECT = "search_rsmupdate_input"   # 事件范围多选框


ACCOUNT_FILE = os.path.join(DATA_DIR, 'account.json')
TEST_ACCOUNT_FILE = os.path.join(DATA_DIR, 'account.test.json')

if not os.path.exists(ACCOUNT_FILE):
    shutil.copy(ACCOUNT_FILE, TEST_ACCOUNT_FILE)

with open(TEST_ACCOUNT_FILE, encoding='utf-8') as f:
    account = json.load(f)

MEMBER_NAME = account.get("membername")
USERNAME = account.get("username")
PASSWORD = account.get("password")

assert MEMBER_NAME and USERNAME and PASSWORD, "请传入会员名，用户名，密码以确保成功登陆"

gee_config = GeeConfig()
gee_config.retry_times = 3
gee_config.bg_path = os.path.join(DATA_DIR, 'bg.png')
gee_config.bg_with_slider_path = os.path.join(
    DATA_DIR, 'bg_with_slider.png')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--start-maximized')    # 指定浏览器分辨率
chrome_options.add_argument('--disable-gpu')        # 谷歌文档提到需要加上这个属性来规避bug
driver = webdriver.Chrome(options=chrome_options)
# 登录页面
driver.get(URLS.LOGIN_PAGE)

login_button = WebDriverWait(driver, timeout=WAIT.WAIT_LOGIN_BUTTON).until(
    lambda d: d.find_element_by_id(SELECTORS.ID_LOGIN_BUTTON))
member_name_input = driver.find_element_by_id(SELECTORS.ID_MEMBER_NAME_INPUT)
username_input = driver.find_element_by_id(SELECTORS.ID_USERNAME_INPUT)
password_input = driver.find_element_by_id(SELECTORS.ID_PASSWORD_INPUT)

member_name_input.send_keys(MEMBER_NAME)
time.sleep(WAIT.ACTION_INTERVAL)
username_input.send_keys(USERNAME)
time.sleep(WAIT.ACTION_INTERVAL)
password_input.send_keys(PASSWORD)
time.sleep(WAIT.ACTION_INTERVAL)

login_button.click()

# 等待验证码出现
time.sleep(WAIT.PAGE_INTERVAL)

# 判断极验验证面板是否可见
if panel_visible(driver):
    # 开始验证
    validate(driver, gee_config)
