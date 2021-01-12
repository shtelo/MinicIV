from datetime import timedelta
from typing import Optional

from pytube import YouTube

from util import singleton, datetime


class MusicData:
    def __init__(self, video_id: str, title: str, last_call: datetime):
        self.video_id = video_id
        self.title = title
        self.last_call = last_call

    def get_video_id(self, now: Optional[datetime] = None) -> str:
        if now:
            self.last_call = now
        else:
            self.last_call = datetime.now()
        return self.video_id

    def get_title(self, now: Optional[datetime] = None) -> str:
        if now:
            self.last_call = now
        else:
            self.last_call = datetime.now()
        return self.title


@singleton
class MusicCache:
    def __init__(self):
        self.musics = dict()

    def optimize_cache(self):
        now = datetime.now()
        for music_key in self.musics.keys():
            if self.musics[music_key].last_call < now - timedelta(hours=12):
                del self.musics[music_key]

    def get_length(self):
        return len(self.musics)

    def get_music_data(self, video_id: str, refresh: bool = False) -> MusicData:
        now = datetime.now()
        if refresh or video_id not in self.musics or self.musics[video_id].last_call < now - timedelta(hours=12):
            self.musics[video_id] = MusicData(video_id, YouTube(f'https://youtu.be/{video_id}').title, now)
        return self.musics[video_id]

    def get_title(self, video_id: str, refresh: bool = False) -> str:
        return self.get_music_data(video_id, refresh).title
