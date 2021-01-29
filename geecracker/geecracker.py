import time
import base64
import random
from io import BytesIO
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None


class CustomPointerInput(PointerInput):
    def __init__(self, kind, name):
        super(CustomPointerInput, self).__init__(kind, name)
        self.duration = PointerInput.DEFAULT_MOVE_DURATION

    def create_pointer_move(self, duration=PointerInput.DEFAULT_MOVE_DURATION, x=None, y=None, origin=None):
        """重写父类方法，以实现不同的移动速度，duration 是为了保证接口的一致性"""
        super(CustomPointerInput, self).create_pointer_move(
            self.duration, x, y, origin)


class CustomActionChains(ActionChains):
    def __init__(self, driver):
        super(CustomActionChains, self).__init__(driver)
        # ActionChains 中有 self._driver.w3c 的判断，暂时不去处理它好了
        if self.w3c_actions:
            self._mouse = CustomPointerInput(
                interaction.POINTER_MOUSE, "mouse")
            self.w3c_actions = ActionBuilder(driver, self._mouse)

    def set_move_duration(self, duration):
        self._mouse.duration = duration
        return self


class GeeConfig(BaseModel or object):
    """便于兼容 BaseModel"""
    bg_path: str = ''               # 背景图存储位置
    bg_with_slider_path: str = ''   # 带滑块背景图存储位置
    retry_times: int = 3            # 重试次数
    threshold = 60                  # 颜色阈值
    initial_offset = 39             # 初始左侧偏移量
    deviation = -3                  # 移动距离偏移
    move_duration: int = 2          # 移动的时间间隔，用于覆盖 PointInput.DEFAULT_MOVE_DURATION 的值
    # wait
    wait = 10                       # 元素加载时间
    wait_move = 0.5                 # 移动结束后停顿时间
    wait_script_execution = 0.3     # js 代码运行等待时间
    wait_shake = 3                  # 这个是参考文章三的实现，暂时没碰到这种情况
    wait_retry = 2                  # 每次重试等待的时间
    wait_before_validation = 3      # 移动之后调用 validation_passed 之前等待的时间


class GeeCracker:
    # SELECTORS
    SELECTOR_BG = "geetest_canvas_bg"           # 带滑块背景
    SELECTOR_FULLBG = "geetest_canvas_fullbg"   # 背景
    SELECTOR_SLIDER = "geetest_slider_button"   # 滑块
    SELECTOR_PANEL_NEXT = "geetest_panel_next"  # 验证失败后出现的面板
    XPATH_CHECK_VALIDATION_PASSED = "//div[@class='geetest_panel geetest_wind']/div[2]"
    XPATH_PANEL_ERROR_CONTENT = "//div[@class='geetest_panel_error_content']"

    def __init__(self, driver: WebDriver, config: GeeConfig = GeeConfig()):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, self.config.wait)
        # 运行后的到的数据
        self.bg: Image.Image = ...
        self.bg_with_slider: Image.Image = ...

    # region validation
    def validate(self) -> bool:
        """进行多次验证，如果仍然出错则退出验证流程"""
        for i in range(self.config.retry_times):
            if self._validate():
                return True
            time.sleep(self.config.wait_retry)
        return False

    def _validate(self) -> bool:
        """验证操作"""
        # 1. 获取带滑块的图像并保存到 BytesIO
        self._get_bg()
        # 2. 获取不带滑块的背景并保存 BytesIO
        self._get_bg_with_slider()
        # 3. 根据两个图像的像素差计算滑块需要滑动的距离，不在这里进行偏移的处理，将真实距离传入，由 _move_to_gap 处理
        distance = self._get_gap()
        # 4. 获取滑块
        slider = self._get_slider()
        # 5. 移动滑块
        self._move_to_gap(slider, distance)
        # 6. 判断验证是否成功，如果失败则重复验证
        time.sleep(self.config.wait_before_validation)
        return self._validation_passed()

    def _validation_passed(self) -> bool:
        flag = False
        try:
            geetest_class = self.driver.find_element_by_xpath(
                self.XPATH_CHECK_VALIDATION_PASSED).get_attribute("class")
            if "geetest_panel_box" == geetest_class:
                self.driver.find_element_by_xpath(
                    self.XPATH_PANEL_ERROR_CONTENT).click()
            elif "geetest_panelshowslide geetest_shake" in geetest_class:
                time.sleep(self.config.wait_shake)
        except NoSuchElementException:
            flag = True
        # 上面是默认的验证流程，除了上面的验证以外，用户可能还需要有自定义验证，就重写 custom_validation 了
        return flag and self.custom_validation()

    def custom_validation(self) -> bool:
        """一个简易的接口便于使用者添加自己想要的验证过程"""
        return True
    # endregion

    # region get bg and bg_with_slider
    def _get_bg(self) -> None:
        """获取背景图"""
        self.bg = self._canvas_to_img(self.SELECTOR_FULLBG)
        self._save_img(self.bg, self.config.bg_path)

    def _get_bg_with_slider(self) -> None:
        """获取带有滑块的图片"""
        self.bg_with_slider = self._canvas_to_img(self.SELECTOR_BG)
        self._save_img(self.bg_with_slider, self.config.bg_with_slider_path)

    @staticmethod
    def _save_img(img: Image.Image, filepath: str) -> None:
        """
        保存缩略图，如果文件名不存在则直接返回
        :param img: 图片
        :param filepath: 文件路径
        :return:
        """
        if filepath:
            img.save(filepath)

    def _canvas_to_img(self, selector: str) -> Image.Image:
        """
        将画布转为图像
        :param selector: 画布的 css 选择器
        :return: 图片的 BytesIO 类
        """
        script = """return document.querySelector(".%s").toDataURL("image/png");""" % selector
        img = self.driver.execute_script(script)
        time.sleep(self.config.wait_script_execution)
        data = img[img.find(',') + 1:]
        return Image.open(BytesIO(base64.b64decode(data)))

    # endregion

    # region move action
    def _get_gap(self) -> int:
        """计算滑块移动距离"""
        offset_left = self.config.initial_offset
        for i in range(offset_left, self.bg_with_slider.size[0]):
            for j in range(self.bg_with_slider.size[1]):
                if not self._is_pixel_equal(i, j):
                    offset_left = i
                    return offset_left
        return offset_left

    def _is_pixel_equal(self, i: int, j: int) -> bool:
        """
        判断两个像素是否相同
        (r, g, b) 中任意一个差值突破阈值就返回 False
        :param i: 一维下标 i
        :param j: 二维下标 j
        :return: 像素是否相同
        """
        pixel1 = self.bg.getpixel((i, j))
        pixel2 = self.bg_with_slider.getpixel((i, j))

        for i in range(0, 3):
            if abs(pixel1[i] - pixel2[i]) >= self.config.threshold:
                return False
        return True

    @staticmethod
    def _get_track(distance: float) -> list:
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """

        track = []                                  # 移动轨迹
        current = 0                                 # 当前位移
        mid = distance * 7 / 8                      # 减速位置
        t = random.randint(2, 3) / 10               # 计算间隔
        v = 0                                       # 初速度

        while current < distance:
            if current < mid:
                a = 2                               # 加速度为 +2
            else:
                a = -3                              # 加速度为 -6
            v0 = v                                  # 初速度   v0
            v = v0 + a * t                          # 当前速度 v = v0 + at
            move = v0 * t + 1 / 2 * a * t * t       # 移动距离 x = v0 * t + 1 / 2 * a * t^2
            current += move                         # 当前位移
            track.append(round(move))               # 加入轨迹
        return track

    def _get_slider(self) -> WebElement:
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, self.SELECTOR_SLIDER)))
        return slider

    def _get_action_chains(self, duration: int = 0) -> CustomActionChains:
        duration = duration or self.config.move_duration
        return CustomActionChains(self.driver).set_move_duration(duration)

    @staticmethod
    def micro_sleep_in_range(lower: int, upper: int):
        time.sleep(random.randint(lower, upper) / 1000)

    def _move_to_gap(self, slider: WebElement, distance: int) -> None:
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param distance: 需要移动的总距离
        :return:
        """
        # 实际移动距离
        actual_movement = 0

        self._get_action_chains().click_and_hold(slider).perform()
        # 点击之后要先停一下，然后可以有小幅度的移动
        self.micro_sleep_in_range(50, 150)
        actual_movement += self._move(10, 2)
        # 模拟人往回滑动
        fast_move = int(distance * 13 / 16)
        fast_duration = 2                                   # 移动间隔
        # 断续移动
        intermittent_move = int(distance * 2 / 16)          # 总距离
        intermittent_duration = 10                          # 移动间隔
        intermittent_move_times = intermittent_move // 10   # 每次移动距离
        intermittent_move_last = intermittent_move % 10     # 最后一次移动距离

        actual_movement += self._move(fast_move, fast_duration)
        self.micro_sleep_in_range(50, 150)
        for i in range(intermittent_move_times):
            actual_movement += self._move(10, intermittent_duration)
            self.micro_sleep_in_range(50, 100)
        actual_movement += self._move(intermittent_move_last,
                                      intermittent_duration)
        self.micro_sleep_in_range(50, 150)

        # 剩余的距离
        remaining_distance = distance - actual_movement
        self._move(remaining_distance, fast_duration)

        # 往回滑动一点距离
        self._move(10, 2, reverse=True)

        # 放开圆球
        time.sleep(random.randint(6, 14) / 10)
        self._get_action_chains().release().perform()

    def _move(self, distance: int, duration: int = 0, reverse=False) -> int:
        """
        移动的接口
        :param distance: 移动的距离
        :param duration: 移动的时间间隔，微妙
        :param reverse: 是否反向移动
        :return: 实际移动的距离，因为 _get_track 有四舍五入，精度有损失
        """
        track = self._get_track(distance)
        for x in track:
            x = -x if reverse else x
            self._get_action_chains(duration).move_by_offset(
                xoffset=x, yoffset=0).perform()
        return sum(track)
    # endregion


def validate(driver: WebDriver, config: GeeConfig = GeeConfig()) -> bool:
    return GeeCracker(driver, config).validate()


def panel_visible(driver: WebDriver) -> bool:
    """提供外部调用以确认是否激活了极验验证"""
    panel_next = driver.find_element_by_class_name(GeeCracker.SELECTOR_PANEL_NEXT)
    return panel_next and panel_next.is_displayed()
