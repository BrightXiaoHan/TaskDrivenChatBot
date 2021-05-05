"""
识别asr识别的车牌号码
"""
import re
import json

from argparse import Namespace
from pypinyin import lazy_pinyin as pinyin

asr_config = Namespace(**(json.load(open("assets/asr.json"))))


class AsrCarnumber(object):

    # Define some regx to proccess msg
    RE_PLATE_NUMBER = re.compile(
        '[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z查叉插]{1}-?[A-Z0-9查叉插]{4}[A-Z0-9挂学警港澳查叉插]{1}[A-Z0-9查叉插]?')

    RE_ALL_LETER = re.compile(
        r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z0-9一二三四五六七八九零]+")

    RE_ALL_PROVINCE_LETTER = re.compile(
        r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]+")

    RE_YUE_LETTER = re.compile(r"[EPUYEA1DGIZ要JPC又为ED而热就嗯喂以Q1你G六U呃]+")

    RE_GREATE_LETTER = re.compile(r"(喂|你好)")

    PLATE_NOT_COMPLETE = -1
    PLATE_TOO_LONG = -2
    PLATE_OUT_OF_PROVINCE = -3
    PLATE_NEED_CONFIRM = -4  # 豫和渝字是否是本省的车牌需要确认
    PLATE_CONFIRM = 2  # 确认了是本省的车牌
    PLATE_NORMAL = 1

    province_letter = ['皖', '鲁', '黑', '辽', '闽', '吉', '陕', '新', '青', '赣', '宁', '甘', '藏',
                       '粤', '浙', '湘', '蒙', '沪', '晋', '苏', '京', '云', '川', '琼', '贵', '渝', '豫', '鄂', "粤"]

    pinin_need_singing = ["bi", "yi", "di"]

    @staticmethod
    def pronunciation_correction(p, origin_word):
        """
        对用户发音进行纠正，传入字符串为字符的拼音
        """
        force_correct = asr_config.force_pinyin_mapping

        if p in force_correct:
            return force_correct[p]

        correction_dict = asr_config.pinyin_mapping
        if p in correction_dict and p != origin_word:
            return correction_dict[p]
        else:
            return origin_word

    @staticmethod
    def chinese2arabic(text):
        """
        将消息中的汉字转换为阿拉伯数字
        """
        number_map = {
            '一': '1',
            "二": '2',
            "三": '3',
            "四": '4',
            "五": '5',
            "六": '6',
            "七": '7',
            "八": '8',
            "九": '9',
            "零": '0',
        }

        for key, value in number_map.items():
            text = text.replace(key, value)

        return text

    def on_process_message(self, text):

        # 小写字母转大写字母
        text = text.upper()
        # 清除干扰车牌识别的一些符号
        text = re.sub("[\\.\\*,。，-]", '', text)

        province_letter_position = []  # 记录省份车牌字符的位置

        # 使用规则进行车牌纠正
        all_letter = []
        mask = []

        i = 0
        while i < len(text):
            word = text[i]
            two_words = "None" if i == len(text) - 1 else text[i:i+2]
            three_words = "None" if i >= len(text) - 2 else text[i:i+3]
            p = pinyin(word)[0]

            # 车牌省份字符双字符规则纠错
            if two_words in asr_config.province_mapping and asr_config.province_mapping[two_words] == "粤":
                correct_word = asr_config.province_mapping[two_words]
                all_letter.append(correct_word)
                mask.append(True)
                province_letter_position.append(i + 1)
                i += 2

            # 车牌省份字符单字符规则纠错
            elif word in asr_config.province_mapping and asr_config.province_mapping[word] == "粤":
                correct_word = asr_config.province_mapping[word]
                all_letter.append(correct_word)
                mask.append(True)
                province_letter_position.append(i)
                i += 1

            # 车牌省份字符拼音规则纠错
            elif p in asr_config.pinyin2text and asr_config.pinyin2text[p] == "粤":
                correct_word = asr_config.pinyin2text[p]
                all_letter.append(correct_word)
                if p not in self.pinin_need_singing:
                    mask.append(True)
                else:
                    mask.append(False)
                province_letter_position.append(i)
                i += 1

            # 车牌城市双字符规则纠错
            elif three_words in asr_config.city_mapping and i - 1 in province_letter_position:
                correct_word = asr_config.city_mapping[three_words]
                all_letter.append(correct_word)
                mask.append(True)
                i += 3

            # 车牌城市双字符规则纠错
            elif two_words in asr_config.city_mapping and i - 1 in province_letter_position:
                correct_word = asr_config.city_mapping[two_words]
                all_letter.append(correct_word)
                mask.append(True)
                i += 2

            # 车牌城市单字符规则纠错
            elif word in asr_config.city_mapping and i - 1 in province_letter_position:
                correct_word = asr_config.city_mapping[word]
                all_letter.append(correct_word)
                mask.append(True)
                i += 1

            # 车牌主体三字符纠错
            elif three_words in asr_config.word_mapping:
                correct_word = asr_config.word_mapping[three_words]
                all_letter.append(correct_word)
                mask.append(True)
                i += 3

            # 车牌主体双字符纠错
            elif two_words in asr_config.word_mapping:
                correct_word = asr_config.word_mapping[two_words]
                all_letter.append(correct_word)
                mask.append(True)
                i += 2

            # 车牌主体单字符规则纠错
            elif word in asr_config.word_mapping:
                correct_word = asr_config.word_mapping[word]
                all_letter.append(correct_word)
                mask.append(True)
                i += 1

            # 强制拼音转换
            elif p in asr_config.force_pinyin_mapping:
                correct_word = asr_config.force_pinyin_mapping[p]
                all_letter.append(correct_word)
                if correct_word not in ["E"]:
                    mask.append(True)
                else:
                    mask.append(False)
                i += 1

            elif len(self.RE_ALL_LETER.findall(word)) > 0:
                all_letter.append(word)
                mask.append(False)
                i += 1

            # 软拼音转换，拼音纠正成的字符不能等于原字符
            elif p in asr_config.pinyin_mapping:
                correct_word = asr_config.pinyin_mapping[p]
                all_letter.append(correct_word)
                if correct_word not in ["E"]:
                    mask.append(True)
                else:
                    mask.append(False)
                i += 1

            # 车牌省份字符双字符规则纠错
            elif two_words in asr_config.province_mapping and asr_config.province_mapping[two_words] != "粤":
                correct_word = asr_config.province_mapping[two_words]
                all_letter.append(correct_word)
                mask.append(True)
                province_letter_position.append(i + 1)
                i += 2

            # 车牌省份字符单字符规则纠错
            elif word in asr_config.province_mapping and asr_config.province_mapping[word] != "粤":
                correct_word = asr_config.province_mapping[word]
                all_letter.append(correct_word)
                mask.append(True)
                province_letter_position.append(i)
                i += 1

            # 车牌省份字符拼音规则纠错
            elif p in asr_config.pinyin2text and asr_config.pinyin2text[p] != "粤":
                correct_word = asr_config.pinyin2text[p]
                all_letter.append(correct_word)
                if p not in self.pinin_need_singing:
                    mask.append(True)
                else:
                    mask.append(False)
                province_letter_position.append(i)
                i += 1

            # 需要吞掉的字符
            elif word in asr_config.useless:
                i += 1
            else:
                all_letter.append("+")
                mask.append(False)
                i += 1

        all_letter = "".join(all_letter)
        # 将中文数字转化为英文数字
        all_letter = self.chinese2arabic(all_letter)

        # 如果用户回答中没有省份字符，强行将第一个出现的 E、P、U、Y、E、A 转换为粤字
        if len(self.RE_ALL_PROVINCE_LETTER.findall(all_letter)) == 0:
            yue_letter = self.RE_YUE_LETTER.findall(all_letter)
            if len(yue_letter) > 0:
                yue_index = all_letter.index(yue_letter[0])
                all_letter = all_letter[:yue_index] + \
                    "粤" + all_letter[yue_index+1:]

        plate_nums = self.RE_PLATE_NUMBER.findall(all_letter)

        if len(plate_nums) > 0:
            # 应广信方要求8位车牌，最后一位字母为R进行替换
            if len(plate_nums[0]) > 7 and plate_nums[0][-1] == "R":
                plate_nums[0] = plate_nums[0][:-1]
            mask_index = all_letter.index(plate_nums[0])
            return plate_nums[0], mask[mask_index:]
        else:
            return None, None

    def _has_other_province(self, all_letter):
        """
        查找是否存在外省车牌字符
        """
        regx = re.compile(r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]+")

        words = regx.findall(all_letter)
        return len(words) > 0

    def _compute_max_continue_words(self, all_letter):
        # 此处计算车牌号码连续字符，省字车牌之后开始计数，遇到连续两个中断字符重新计数
        # 如啊哦这你咋了ABEF max_continue_words 的计数为0，这了ABEF 的 max_continue_words 为 5
        max_continue_words = 0
        continue_words = 0
        continue_plus = 0
        start_flag = False

        province_letter = "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领"
        for w in all_letter:
            if w in province_letter:
                start_flag = True

            if not start_flag:
                continue

            if w == "+":
                continue_plus += 1
                if continue_plus > 1:
                    start_flag = False
                    continue_words = 0
            else:
                continue_words += 1
                continue_plus = 0
            max_continue_words = max_continue_words if max_continue_words > continue_words else continue_words
        return max_continue_words

    def __call__(self, context, slot_name):
        msg = context._latest_msg()
        car_number, mask = self.on_process_message(msg.text)
        if car_number and mask:
            context.fill_slot(slot_name, car_number)
        return
        yield None


AsrCarnumberNode = AsrCarnumber()
