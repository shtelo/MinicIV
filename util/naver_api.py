import json
import urllib.parse
import urllib.request
from os import environ

from manager import LanguageName
from manager.language import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_JA, LANGUAGE_ZH_CN, LANGUAGE_ZH_TW, LANGUAGE_ES, \
    LANGUAGE_FR, LANGUAGE_RU, LANGUAGE_VI, LANGUAGE_TH, LANGUAGE_ID, LANGUAGE_DE, LANGUAGE_IT

TRANSLATABLES = {
    LANGUAGE_KO: {LANGUAGE_EN, LANGUAGE_JA, LANGUAGE_ZH_CN, LANGUAGE_ZH_TW, LANGUAGE_ES, LANGUAGE_FR, LANGUAGE_RU,
                  LANGUAGE_VI, LANGUAGE_TH, LANGUAGE_ID, LANGUAGE_DE, LANGUAGE_IT},
    LANGUAGE_ZH_CN: {LANGUAGE_ZH_TW, LANGUAGE_JA},
    LANGUAGE_ZH_TW: {LANGUAGE_JA},
    LANGUAGE_EN: {LANGUAGE_JA, LANGUAGE_ZH_CN, LANGUAGE_ZH_TW, LANGUAGE_FR}
}

CLIENT_ID = environ['MINIC_NAVER_CLIENT_ID']
CLIENT_SECRET = environ['MINIC_NAVER_CLIENT_SECRET']


def language_detect(sentence: str) -> LanguageName:
    request = urllib.request.Request("https://openapi.naver.com/v1/papago/detectLangs")
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    response = urllib.request.urlopen(request,
                                      data=("query=" + urllib.parse.quote(sentence)).encode("utf-8"))
    response_code = response.getcode()
    if response_code == 200:
        response_body = response.read()
        return LanguageName.to_language_name(json.loads(response_body.decode('utf-8'))['langCode'])
    else:
        raise Exception(f'Language detect failed. Response code from Naver: {response_code}')


def translate(source_language: LanguageName, target_language: LanguageName, sentence: str) -> dict:
    request = urllib.request.Request("https://openapi.naver.com/v1/papago/n2mt")
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    data = f"source={source_language.to_code()}&target={target_language.to_code()}&text={urllib.parse.quote(sentence)}"
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    response_code = response.getcode()
    if response_code == 200:
        response_body = response.read()
        return json.loads(response_body.decode('utf-8'))
    else:
        raise Exception(f'Papago translation failed. Response code from Naver: {response_code}')


if __name__ == '__main__':
    print(translate(LANGUAGE_KO, LANGUAGE_ZH_CN, '안녕하세요. 지금 뭐 하고 계세요?'))
    print(language_detect('안녕하세요.'))
