import random
from models.mood_axes import MOOD_AXES


def score_project(user_mood, project):
    """Euclidean distance between user's mood vector and a project's ideal mood_fit.
    Lower score = better match."""
    fit = project["mood_fit"]
    return sum((user_mood[axis] - fit.get(axis, 0)) ** 2 for axis in MOOD_AXES) ** 0.5


def get_candidates(user_mood, difficulty, projects, pool_size=5):
    """Filters by difficulty, sorts by closeness to user's mood, returns top N."""
    filtered = [p for p in projects if p["difficulty"] == difficulty]
    filtered.sort(key=lambda p: score_project(user_mood, p))
    return filtered[:pool_size]


def spin_wheel(candidates, user_mood):
    """Weighted random pick from the candidate pool - closer mood matches are
    more likely to be picked, but it's not purely deterministic. Keeps the
    wheel feeling intentional instead of arbitrary, without hardcoding the
    'best' project every single time."""
    if not candidates:
        return None

    scored = [(p, score_project(user_mood, p)) for p in candidates]
    # invert distance into a weight; add a small constant to avoid divide-by-zero
    weights = [1 / (dist + 0.5) for _, dist in scored]

    chosen = random.choices([p for p, _ in scored], weights=weights, k=1)[0]
    return chosen


def describe_match_reason(user_mood, project):
    """Builds a short human-readable reason for why this project was picked,
    based on which axis the user leaned into hardest."""
    fit = project["mood_fit"]
    diffs = {axis: abs(user_mood[axis] - fit.get(axis, 0)) for axis in MOOD_AXES}
    closest_axis = min(diffs, key=diffs.get)

    axis_phrases = {
        "energy": "your energy level",
        "creativity": "your creative vs structured leaning",
        "challenge": "how much of a challenge you're up for",
    }

    return f"Of the three preference axes, this project is closest to {axis_phrases.get(closest_axis, closest_axis)}. Its overall vector distance is {score_project(user_mood, project):.2f}."