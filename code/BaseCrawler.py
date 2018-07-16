class BaseCrawler:

    def __init__(self, config_file_path: str):
        self.driver = None
        self.prefix = None
        self.fieldnames = []
        self.config_file_path = config_file_path

    def run(self, *args, **kwargs):
        raise NotImplementedError
