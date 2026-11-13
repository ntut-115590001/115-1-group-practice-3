"""F3: personal timetable and free-slot search."""

from src.cli import CommandError, command
from src.data_management import DAY_NAMES, DAYS, PERIODS, courses, students

# A timetable maps a time code (day + period, e.g. '13') to the list of
# course codes that occupy that slot. A free slot has an empty list.
Timetable = dict[str, list[str]]


def build_schedule(student_id: str) -> Timetable:
    """Build the 7 x 12 timetable of a student. Prints nothing."""
    if student_id not in students:
        raise CommandError(f'學生 {student_id} 不存在！')
    table: Timetable = {day + period: [] for day in DAYS for period in PERIODS}
    for code in students[student_id].course_ids:
        course = courses.get(code)
        if course is None:  # the id points to a deleted course: ignore it
            continue
        for times, _room in course.sections:
            for time in times:
                if time in table and code not in table[time]:
                    table[time].append(code)
    return table


def find_conflicts(table: Timetable) -> list[tuple[str, list[str]]]:
    """Return every slot that holds two or more courses, ordered by day and period."""
    return [(time, codes) for time, codes in table.items() if len(codes) > 1]


def find_free_blocks(table: Timetable, days: str, start: str, end: str,
                     min_length: int = 1) -> list[tuple[str, str, str]]:
    """Find runs of consecutive free periods.

    Returns (day, first_period, last_period) for each run of at least
    min_length periods, looking only at periods start..end of the given days.
    """
    first, last = PERIODS.index(start), PERIODS.index(end)
    blocks: list[tuple[str, str, str]] = []
    for day in days:
        run_start: int | None = None
        for i in range(first, last + 2):  # one extra step closes the last run
            free = i <= last and not table[day + PERIODS[i]]
            if free and run_start is None:
                run_start = i
            elif not free and run_start is not None:
                if i - run_start >= min_length:
                    blocks.append((day, PERIODS[run_start], PERIODS[i - 1]))
                run_start = None
    return blocks


def count_stats(table: Timetable) -> tuple[dict[str, int], int]:
    """Return (class periods per day, total weekly credits)."""
    per_day = {day: sum(bool(table[day + p]) for p in PERIODS) for day in DAYS}
    codes = {code for codes in table.values() for code in codes}
    credits = sum(courses[code].credit for code in codes)
    return per_day, credits


def format_slot(time: str) -> str:
    """'13' -> 'Mon 3'"""
    return f'{DAY_NAMES[time[0]]} {time[1]}'


def print_table(table: Timetable) -> None:
    """Print the full grid: one row per period, one column per day."""
    cells = {time: '/'.join(codes) for time, codes in table.items()}
    width = max(4, *(len(text) for text in cells.values()))
    print('     ' + ' '.join(DAY_NAMES[day].ljust(width) for day in DAYS))
    for period in PERIODS:
        row = ' '.join(cells[day + period].ljust(width) for day in DAYS)
        print(f'{period:>3}  {row}'.rstrip())


@command('schedule')
def schedule(student_id: str, field: str | None = None, value: str | None = None) -> None:
    """顯示學生的每週課表。語法：schedule <學號> [(day|period|course) <值>]

    不加條件時顯示完整課表（星期一到日、第 1 到 c 節）；
    day <1-7>、period <節次>、course <課號> 只列出符合條件的時段。
    同一時段有兩門以上的課時，會在最後提醒衝堂。
    """
    table = build_schedule(student_id)
    if field is None:
        print_table(table)
    else:
        if value is None:
            raise CommandError('請指定查詢的值！')
        if field == 'day':
            if value not in DAYS:
                raise CommandError(f'星期 {value} 無效，應為 1-7！')
            matched = [t for t in table if t[0] == value]
        elif field == 'period':
            if value not in PERIODS:
                raise CommandError(f'節次 {value} 無效，應為 1-9、a、b、c！')
            matched = [t for t in table if t[1] == value]
        elif field == 'course':
            matched = [t for t, codes in table.items() if value in codes]
        else:
            raise CommandError(f'未知查詢條件：{field}')
        for time in matched:
            codes = table[time]
            print(f'{format_slot(time)}: {"/".join(codes) if codes else "-"}')
        if field == 'course' and not matched:
            print('Not found')
    for time, codes in find_conflicts(table):
        print(f'\033[91m注意！{format_slot(time)} 衝堂：{" 與 ".join(codes)}\033[0m')


@command('free')
def free(student_id: str, day: str, start: str, end: str, min_length: str = '1') -> None:
    """查詢連續空閒時段。語法：free <學號> <星期|*> <起始節> <結束節> [<最少連續節數>]

    例如 free S001 1 3 5 查詢星期一第 3 到 5 節；星期填 * 表示查詢七天。
    """
    table = build_schedule(student_id)
    if day != '*' and day not in DAYS:
        raise CommandError(f'星期 {day} 無效，應為 1-7 或 *！')
    for period in (start, end):
        if period not in PERIODS:
            raise CommandError(f'節次 {period} 無效，應為 1-9、a、b、c！')
    if PERIODS.index(start) > PERIODS.index(end):
        raise CommandError('起始節不能晚於結束節！')
    if not min_length.isdecimal() or int(min_length) < 1:
        raise CommandError('最少連續節數必須是正整數！')
    days = DAYS if day == '*' else day
    blocks = find_free_blocks(table, days, start, end, int(min_length))
    if not blocks:
        print('Not found')
        return
    for block_day, first, last in blocks:
        length = PERIODS.index(last) - PERIODS.index(first) + 1
        print(f'{DAY_NAMES[block_day]} {first}-{last} ({length} periods free)')


@command('schedule_stats')
def schedule_stats(student_id: str) -> None:
    """統計學生課表。語法：schedule_stats <學號>

    顯示每日上課節數、空堂數，以及每週總學分。
    """
    table = build_schedule(student_id)
    per_day, credits = count_stats(table)
    for day in DAYS:
        print(f'{DAY_NAMES[day]}: {per_day[day]} class periods, '
              f'{len(PERIODS) - per_day[day]} free')
    print(f'Total class periods: {sum(per_day.values())}')
    print(f'Total free periods: {sum(len(PERIODS) - n for n in per_day.values())}')
    print(f'Weekly credits: {credits}')
