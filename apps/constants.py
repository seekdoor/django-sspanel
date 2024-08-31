METHOD_CHOICES = (
    ("chacha20-ietf-poly1305", "chacha20-ietf-poly1305"),
    ("aes-128-gcm", "aes-128-gcm"),
    ("aes-256-gcm", "aes-256-gcm"),
)


COUNTRIES_CHOICES = (
    ("US", "美国"),
    ("CN", "中国"),
    ("GB", "英国"),
    ("SG", "新加坡"),
    ("TW", "台湾"),
    ("HK", "香港"),
    ("JP", "日本"),
    ("FR", "法国"),
    ("DE", "德国"),
    ("KR", "韩国"),
    ("JE", "泽西岛"),
    ("NZ", "新西兰"),
    ("MX", "墨西哥"),
    ("CA", "加拿大"),
    ("BR", "巴西"),
    ("CU", "古巴"),
    ("CZ", "捷克"),
    ("EG", "埃及"),
    ("FI", "芬兰"),
    ("GR", "希腊"),
    ("GU", "关岛"),
    ("IS", "冰岛"),
    ("MO", "澳门"),
    ("NL", "荷兰"),
    ("NO", "挪威"),
    ("PL", "波兰"),
    ("IT", "意大利"),
    ("IE", "爱尔兰"),
    ("AR", "阿根廷"),
    ("PT", "葡萄牙"),
    ("AU", "澳大利亚"),
    ("RU", "俄罗斯联邦"),
    ("CF", "中非共和国"),
)

THEME_CHOICES = (
    ("default", "default"),
    ("darkly", "darkly"),
    ("flatly", "flatly"),
    ("journal", "journal"),
    ("materia", "materia"),
    ("minty", "minty"),
    ("spacelab", "spacelab"),
    ("superhero", "superhero"),
)

BULMA_COLOR_EMPTY = ""
BULMA_COLOR_PRIMARY = "is-primary"
BULMA_COLOR_LINK = "is-link"
BULMA_COLOR_INFO = "is-info"
BULMA_COLOR_DANGER = "is-danger"
BULMA_COLOR_WARNING = "is-warning"
BULMA_COLOR_SUCCESS = "is-success"
BULMA_COLOR_CHOICES = (
    (BULMA_COLOR_EMPTY, "empty"),
    (BULMA_COLOR_INFO, "is-info"),
    (BULMA_COLOR_LINK, "is-link"),
    (BULMA_COLOR_PRIMARY, "is-primary"),
    (BULMA_COLOR_DANGER, "is-danger"),
    (BULMA_COLOR_WARNING, "is-warning"),
    (BULMA_COLOR_SUCCESS, "is-success"),
)


# 判断节点在线时间间隔
NODE_TIME_OUT = 75


# ehco隧道相关
LISTEN_RAW = "raw"
LISTEN_WS = "ws"
LISTEN_WSS = "wss"
LISTEN_TYPES = (
    (LISTEN_RAW, "raw"),
    (LISTEN_WS, "ws"),
    (LISTEN_WSS, "wss"),
)

TRANSPORT_RAW = "raw"
TRANSPORT_WS = "ws"
TRANSPORT_WSS = "wss"
TRANSPORT_TYPES = (
    (TRANSPORT_RAW, "raw"),
    (TRANSPORT_WS, "ws"),
    (TRANSPORT_WSS, "wss"),
)


CACHE_TTL_HOUR = 60 * 60
CACHE_TTL_DAY = CACHE_TTL_HOUR * 24
CACHE_TTL_WEEK = CACHE_TTL_DAY * 7
CACHE_TTL_MONTH = CACHE_TTL_DAY * 31
