"""
内置意图识别能力 @sys.intent.confirm, @sys.intent.deny
"""
import re


class WhetherNode(object):

    RE_DENY_FORCE = re.compile("(不是|不对|不不|不正确|不四|不摄|不要|错了)")
    RE_CONFIRM_FORCE = re.compile("(嗯|恩|确认|没问题|没错|不错|四|摄)")
    RE_DENEY = re.compile('(错误|不)')
    RE_CONFIRM = re.compile('(恩|对|要|是|确认|正确|四|摄)')
    RE_PUNCTUATION = re.compile(
        "[.!//_,$&%^*()<>+\"'?@#:~{}——！\\\\，。=？、：“”‘’《》【】￥……（）]")

    def get_intent(self, msg):

        text = msg.text
        intent = msg.intent
        # 过滤标点符号
        text = re.sub(self.RE_PUNCTUATION, '', text)

        # force deny
        force_deny = self.RE_DENY_FORCE.findall(text)
        if len(force_deny) != 0:
            intent = '@sys.intent.deny'
            return intent

        # force confirm
        force_confirm = self.RE_CONFIRM_FORCE.findall(text)
        if len(force_confirm) != 0:
            intent = '@sys.intent.confirm'
            return intent

        # deny
        deny = self.RE_DENEY.findall(text)
        if len(deny) != 0:
            intent = '@sys.intent.deny'

        # confirm
        confirm = self.RE_CONFIRM.findall(text)
        if len(confirm) != 0:
            intent = '@sys.intent.confirm'

        return intent
