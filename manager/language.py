from json import load

from discord.ext.commands import Converter, Context


class LanguageName(Converter, int):
    with open('./res/language_names.json', 'r', encoding='utf-8') as file:
        LANGUAGE_NAMES = load(file)

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
        if argument in LanguageName.LANGUAGE_NAMES['ko']:
            return LANGUAGE_KO
        elif argument in LanguageName.LANGUAGE_NAMES['ja']:
            return LANGUAGE_JA
        elif argument in LanguageName.LANGUAGE_NAMES['zh-cn']:
            return LANGUAGE_ZH_CN
        elif argument in LanguageName.LANGUAGE_NAMES['zh-tw']:
            return LANGUAGE_ZH_TW
        elif argument in LanguageName.LANGUAGE_NAMES['hi']:
            return LANGUAGE_HI
        elif argument in LanguageName.LANGUAGE_NAMES['en']:
            return LANGUAGE_EN
        elif argument in LanguageName.LANGUAGE_NAMES['es']:
            return LANGUAGE_ES
        elif argument in LanguageName.LANGUAGE_NAMES['fr']:
            return LANGUAGE_FR
        elif argument in LanguageName.LANGUAGE_NAMES['de']:
            return LANGUAGE_DE
        elif argument in LanguageName.LANGUAGE_NAMES['pt']:
            return LANGUAGE_PT
        elif argument in LanguageName.LANGUAGE_NAMES['vi']:
            return LANGUAGE_VI
        elif argument in LanguageName.LANGUAGE_NAMES['id']:
            return LANGUAGE_ID
        elif argument in LanguageName.LANGUAGE_NAMES['fa']:
            return LANGUAGE_FA
        elif argument in LanguageName.LANGUAGE_NAMES['ar']:
            return LANGUAGE_AR
        elif argument in LanguageName.LANGUAGE_NAMES['mm']:
            return LANGUAGE_MM
        elif argument in LanguageName.LANGUAGE_NAMES['th']:
            return LANGUAGE_TH
        elif argument in LanguageName.LANGUAGE_NAMES['ru']:
            return LANGUAGE_RU
        elif argument in LanguageName.LANGUAGE_NAMES['it']:
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
