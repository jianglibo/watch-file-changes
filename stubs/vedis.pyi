from typing import Set, Dict, List

class Vedis():

    def __init__(self, filename: str = ':mem:', open_database: bool = True) -> None: ...
    
    def set(self, key:str, value:str) -> None: ...
    
    def get(self, key:str) -> str: ...
    
    def hset(self, hash_key:str, key:str, value: str) -> None: ...
    
    def hsetnx(self, hash_key: str, key: str, value: str) -> None: ...
    
    def hgetall(self, hash_key: str) -> Dict[bytes, bytes]: ...

    def smembers(self, key: str) -> Set[bytes]: ...
    
    def hlen(self, hash_key: str) -> int: ...
    
    def scard(self, key: str) -> int: ...

    def close(self) -> None: ...

    def llen(self, key:str) -> int: ...
    
    def List(self, key: str): ...

    def lpush(self,lname: str, value: str): ...
    
    def transaction(self): ...
    


    
    