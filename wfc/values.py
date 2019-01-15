

class FileHash:
    def __init__(self, Algorithm: str, Hash: str, Path: str, Length: int):
        self.Algorithm: str = Algorithm
        self.Hash: str = Hash
        self.Path: str = Path
        self.Length: int = Length

class DiskFree:
    def __init__(self, Name: str, Used: int, Free: int, Percent: str, FreeMegabyte: str, UsedMegabyte: str):
        self.Name: str = Name
        self.Used: int = Used
        self.Free: int = Free
        self.Percent: str = Percent    
        self.FreeMegabyte: str = FreeMegabyte    
        self.UsedMegabyte: str = UsedMegabyte    

class MemoryFree(DiskFree):
    def __init__(self, Used: int, Free: int, Percent: str, FreeMegabyte: str, UsedMegabyte: str, total: int):
        super().__init__('', Used, Free, Percent, FreeMegabyte, UsedMegabyte)
        self.total: int = total
