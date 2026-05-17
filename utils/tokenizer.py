MAX_OBSERVATION_LENGTH = 500


def _truncate_observation(text: str) -> str:
    """截断过长的工具返回内容，节省 Token"""
    if len(text) <= MAX_OBSERVATION_LENGTH:
        return text
    return text[:MAX_OBSERVATION_LENGTH] + "...(已截断)"
