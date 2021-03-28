from os import listdir

from rest import Launcher

restful_launcher = Launcher()

for file_name in listdir('./rest'):
    if file_name.endswith('.py') \
            and '__init__' not in file_name \
            and 'launcher' not in file_name:
        restful_launcher.load_resource(f'rest.{file_name[:-3]}')
        print(f'`{file_name}` Resource가 준비되었습니다.')

restful_launcher.run(host='0.0.0.0', port=3375)
