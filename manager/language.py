from discord.ext.commands import Converter, Context


class LanguageName(Converter, int):
    @staticmethod
    def to_language_name(code: str):
        return TO_LANGUAGE_NAME[code]

    def __str__(self):
        return self.to_code()

    def __repr__(self):
        return self.to_code()

    def to_code(self) -> str:
        return TO_CODE[self]

    async def convert(self, ctx: Context, argument: str):
        argument = argument.lower()
        if argument in ('ko', 'korean', '한국어', '한국'):
            return LANGUAGE_KO
        elif argument in ('ja', 'japanese', '일본어', '일본'):
            return LANGUAGE_JA
        elif argument in ('zh-cn', 'zh_cn', '중국어', '중국', '간체'):
            return LANGUAGE_ZH_CN
        elif argument in ('zh-tw', 'zh_tw', '번체'):
            return LANGUAGE_ZH_TW
        elif argument in ('hi', 'hindi', '힌디어', '힌디'):
            return LANGUAGE_HI
        elif argument in ('en', 'english', '영어'):
            return LANGUAGE_EN
        elif argument in ('es', 'spanish', '스페인어', '스페인'):
            return LANGUAGE_ES
        elif argument in ('fr', 'french', '프랑스어', '프랑스'):
            return LANGUAGE_FR
        elif argument in ('de', 'deutsch', 'german', '독일', '독일어'):
            return LANGUAGE_DE
        elif argument in ('pt', 'portuguese', '포루트갈어', '포르투칼', '포루트갈', '포르투칼어'):
            return LANGUAGE_PT
        elif argument in ('vi', 'vietnamese', '베트남어', '베트남'):
            return LANGUAGE_VI
        elif argument in ('id', 'indonesian', '인도네시아', '인도네시아어'):
            return LANGUAGE_ID
        elif argument in ('fa', 'persian', '페르시아어', '페르시아'):
            return LANGUAGE_FA
        elif argument in ('ar', 'arabic', '아랍어', '아랍'):
            return LANGUAGE_AR
        elif argument in ('mm', 'myanmar', '미얀마어', '미얀마'):
            return LANGUAGE_MM
        elif argument in ('th', 'thailand', 'thai', '태국어', '태국'):
            return LANGUAGE_TH
        elif argument in ('ru', 'russian', '러시아어', '러시아'):
            return LANGUAGE_RU
        elif argument in ('it', 'italian', 'italy', '이탈리아어', '이탈리아'):
            return LANGUAGE_IT
        else:
            return LANGUAGE_UNKNOWN


LANGUAGE_PY = LanguageName(-2)
LANGUAGE_UNKNOWN = LanguageName(-1)
LANGUAGE_KO = LanguageName(0)
LANGUAGE_JA = LanguageName(1)
LANGUAGE_ZH_CN = LanguageName(2)
LANGUAGE_ZH_TW = LanguageName(3)
LANGUAGE_HI = LanguageName(4)
LANGUAGE_EN = LanguageName(5)
LANGUAGE_ES = LanguageName(6)
LANGUAGE_FR = LanguageName(7)
LANGUAGE_DE = LanguageName(8)
LANGUAGE_PT = LanguageName(9)
LANGUAGE_VI = LanguageName(10)
LANGUAGE_ID = LanguageName(11)
LANGUAGE_FA = LanguageName(12)
LANGUAGE_AR = LanguageName(13)
LANGUAGE_MM = LanguageName(14)
LANGUAGE_TH = LanguageName(15)
LANGUAGE_RU = LanguageName(16)
LANGUAGE_IT = LanguageName(17)

TO_CODE = {
    LANGUAGE_PY: 'py',
    LANGUAGE_UNKNOWN: 'unk',
    LANGUAGE_KO: 'ko',
    LANGUAGE_JA: 'ja',
    LANGUAGE_ZH_CN: 'zh-CN',
    LANGUAGE_ZH_TW: 'zh-TW',
    LANGUAGE_HI: 'hi',
    LANGUAGE_EN: 'en',
    LANGUAGE_ES: 'es',
    LANGUAGE_FR: 'fr',
    LANGUAGE_DE: 'de',
    LANGUAGE_PT: 'pt',
    LANGUAGE_VI: 'vi',
    LANGUAGE_ID: 'id',
    LANGUAGE_FA: 'fa',
    LANGUAGE_AR: 'ar',
    LANGUAGE_MM: 'mm',
    LANGUAGE_TH: 'th',
    LANGUAGE_RU: 'ru',
    LANGUAGE_IT: 'it'
}

TO_LANGUAGE_NAME = {v: k for k, v in TO_CODE.items()}
