# place holder.
VEDIS_FILE = ":mem:"
CHANGED_FOLDER = "e:/changed-folder"
ARCHIVE_INTERVAL = 60
PENDING_MOVE_INTERVAL = 80
WATCH_PATHES = [
    {
        "regexes": [
            ".*"
        ],
        "ignore_regexes": [
            r"c:Users\\admin\AppData\\Roaming\\.*",
            r"c:Users\\admin\AppData\\Local\\.*",
            r"c:\Windows\\.*",
            r"c:Windows\\.*",
            r".*vedisdb.*"
        ],
        "ignore_directories": True,
        "case_sensitive": False,
        "path": "c:",
        "recursive": True
    },
    {
        "regexes": [
            ".*"
        ],
        "ignore_regexes": [
            r"c:\\Users\\admin\AppData\\Roaming\\.*",
            r"c:\\Users\\admin\AppData\\Local\\.*",
            ".*vedisdb.*"
        ],
        "ignore_directories": True,
        "case_sensitive": False,
        "path": "e:",
        "recursive": True
    }
]
