"""F7: enumerate and rank feasible course selections."""
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from src.cli import CommandError, command
from src.data_management import PERIODS, check_time, courses, enrolled_count
from src.util import split_map


@dataclass(frozen=True)
class Recommendation:
    codes: tuple[str, ...]
    credits: int
    score: Fraction


def score_schedule(occupied, preferred_count, optional_count, window, weights):
    """Evaluate a feasible schedule. A gap is an unused period between two classes."""
    days = defaultdict(list)
    for day, period in occupied:
        days[day].append(PERIODS.index(period))
    gaps = sum(max(ps) - min(ps) + 1 - len(ps) for ps in days.values())
    early = sum(0 in ps for ps in days.values())
    start, end = window
    outside = sum(not start <= p <= end for ps in days.values() for p in ps)
    ratio = Fraction(preferred_count, max(1, optional_count))
    wd, wg, we, wo, wp = weights
    return wp * ratio - wd * len(days) - wg * gaps - we * early - wo * outside


def search(required, electives, minimum, maximum, blocked, preferred, window, weights):
    """Return every feasible selection, highest score first."""
    if not 0 <= minimum <= maximum:
        raise CommandError('學分範圍須符合 0 ≤ 下限 ≤ 上限。')
    if (required | electives) - courses.keys():
        raise CommandError('必修或候選清單含有未知課號。')
    electives = electives - required
    if preferred - electives:
        raise CommandError('偏好課號必須屬於候選選修。')
    if not all(map(check_time, blocked)):
        raise CommandError('禁止時段格式錯誤。')
    if (len(window) != 2 or any(len(p) != 1 or p not in PERIODS for p in window)
            or PERIODS.index(window[0]) > PERIODS.index(window[1])):
        raise CommandError('集中時段應為起訖節次，例如 2-6。')
    if len(weights) != 5 or min(weights) < 0:
        raise CommandError('請輸入五個非負整數權重。')

    # Prepare each course once, including every meeting in all of its sections.
    available = {}
    for code in required | electives:
        course = courses[code]
        slots = {t for times, _ in course.sections for t in times}
        if enrolled_count(code) < course.student_limit and slots.isdisjoint(blocked):
            available[code] = slots

    occupied = set()
    for code in required:
        if code not in available or not occupied.isdisjoint(available[code]):
            return []
        occupied.update(available[code])
    required_credits = sum(courses[c].credit for c in required)
    if required_credits > maximum:
        return []

    candidates = sorted(electives.intersection(available))
    period_range = tuple(map(PERIODS.index, window))
    results = []

    def visit(first, optional, taken, credits, preferred_count):
        if credits >= minimum:
            codes = tuple(sorted(required.union(optional)))
            score = score_schedule(taken, preferred_count, len(optional), period_range, weights)
            results.append(Recommendation(codes, credits, score))
        # Increasing indices give each subset exactly one path.
        for index in range(first, len(candidates)):
            code = candidates[index]
            total = credits + courses[code].credit
            if total <= maximum and taken.isdisjoint(available[code]):
                visit(index + 1, optional + (code,), taken | available[code],
                      total, preferred_count + (code in preferred))

    visit(0, (), occupied, required_credits, 0)
    return sorted(results, key=lambda row: (-row.score, row.codes))


def as_set(text):
    return set() if text == '-' else set(split_map(text, sep=','))


@command('schedule_search')
def schedule_search(required: str, electives: str, minimum: str, maximum: str,
                    blocked: str = '-', preferred: str = '-', window: str = '2-6',
                    weights: str = '10,3,5,2,6'):
    """搜尋所有可行課表，由高分到低分列出。
    語法：schedule_search 必修 候選 最低學分 最高學分 [禁止時段 [偏好選修 [集中節次 [權重]]]]
    清單以逗號分隔，空清單填 -。集中節次預設 2-6（含端點）。
    權重依序為到校天數、空堂、早八、集中區間外節數、偏好比例，預設 10,3,5,2,6。
    """
    try:
        low, high = int(minimum), int(maximum)
        values = tuple(map(int, weights.split(',')))
    except ValueError as err:
        raise CommandError('學分與權重須為整數。') from err
    rows = search(as_set(required), as_set(electives), low, high,
                  as_set(blocked), as_set(preferred), window.split('-'), values)
    if not rows:
        print('無可行課表')
    for row in rows:
        print(f'{",".join(row.codes) or "（空課表）"} | {row.credits} 學分 | {row.score:.2f} 分')
