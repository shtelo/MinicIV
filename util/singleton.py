def singleton(_cls):
    class Singleton(_cls):
        _instance = None

        def __new__(cls, *args, **kwargs):
            if Singleton._instance is None:
                Singleton._instance = _cls(*args, **kwargs)
            return Singleton._instance

    return Singleton
